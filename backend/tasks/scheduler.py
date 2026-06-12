import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from core.database import SessionLocal
from models.task import Task
from models.log import Log
from models.account import Account
from models.site import Site
from models.user import User

scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


def run_task(task_id: int):
    """调度器触发入口 - 必须同步函数（add_job 不支持 async 直接调用）"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(execute_task(task_id))
    finally:
        loop.close()


async def execute_task(task_id: int):
    """执行签到任务的核心逻辑"""
    db = SessionLocal()
    result = {"success": False, "error": "未知错误"}
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            print(f"[scheduler] 任务 {task_id} 不存在")
            return
        if task.status != "enabled":
            print(f"[scheduler] 任务 {task_id} 已禁用，跳过执行")
            return

        task.last_run = datetime.utcnow()
        db.commit()

        account = db.query(Account).filter(Account.id == task.account_id).first()
        if not account:
            result = {"success": False, "error": "账号不存在"}
            _write_log(db, task_id, result)
            return

        site = db.query(Site).filter(Site.id == account.site_id).first()
        if not site:
            result = {"success": False, "error": "站点不存在"}
            _write_log(db, task_id, result)
            return

        print(f"[scheduler] 开始执行任务 {task_id}: {account.username} @ {getattr(site, 'name', '?')}")
        result = await perform_sign_in(account, site)
        print(f"[scheduler] 任务 {task_id} 执行结果: {result}")
        _write_log(db, task_id, result)

        # 通知（邮件 + 企业微信机器人）
        try:
            await send_notification(account, site, result, db)
        except Exception as e:
            print(f"[scheduler] 通知发送失败: {e}")

    except Exception as e:
        result = {"success": False, "error": f"执行异常: {str(e)}"}
        print(f"[scheduler] 任务 {task_id} 执行异常: {e}")
        try:
            _write_log(db, task_id, result)
        except Exception:
            pass
    finally:
        db.close()


def _write_log(db: Session, task_id: int, result: dict):
    try:
        log = Log(
            task_id=task_id,
            result=str(result),
            status="success" if result.get("success") else "failed"
        )
        db.add(log)
        db.commit()
    except Exception as e:
        print(f"[scheduler] 写入日志失败: {e}")


async def perform_sign_in(account, site):
    """根据站点类型动态选择签到插件"""
    site_type = (site.type or "").lower()
    api_config = getattr(site, "api_config", None)
    result = {"success": False, "error": "未知类型"}

    try:
        # 1. custom-api - 通用 API 模式（推荐）
        if site_type == "custom-api" and api_config:
            from plugins.custom_api.plugin import CustomApiPlugin
            plugin = CustomApiPlugin()
            result = await plugin.sign_in(account, site=site)

        # 2. gemai - 内置 API 模式
        elif site_type == "gemai":
            from plugins.custom_api.plugin import CustomApiPlugin
            plugin = CustomApiPlugin()
            result = await plugin.sign_in(account, site=site)

        # 3. lizhiyu - 内置公益站（走 custom-api 逻辑）
        elif site_type == "lizhiyu" and api_config:
            from plugins.custom_api.plugin import CustomApiPlugin
            plugin = CustomApiPlugin()
            result = await plugin.sign_in(account, site=site)

        # 4. openrouter - OpenRouter 模式
        elif site_type == "openrouter" and api_config:
            from plugins.custom_api.plugin import CustomApiPlugin
            plugin = CustomApiPlugin()
            result = await plugin.sign_in(account, site=site)

        # 5. forum / custom - Playwright 爬虫模式（仅保留兼容）
        elif site_type in ["forum", "custom"]:
            try:
                from services.scraper import ScraperService
                scraper = ScraperService()
                result = await scraper.sign_in(account, site)
            except Exception as e:
                result = {"success": False, "error": f"Playwright 模式失败: {str(e)}"}

        # 6. 其他类型 - 尝试走 custom_api（如果有 api_config）
        elif api_config:
            from plugins.custom_api.plugin import CustomApiPlugin
            plugin = CustomApiPlugin()
            result = await plugin.sign_in(account, site=site)

        else:
            result = {"success": False, "error": f"不支持的站点类型: {site_type}"}

    except Exception as e:
        result = {"success": False, "error": f"签到执行异常: {str(e)}"}

    return result


async def send_notification(account, site, result, db):
    """发送通知（邮件 + 企业微信机器人）"""
    try:
        from models.settings import UserSettings
        from services.notification import NotificationService
        from services.wechat_bot import WechatBotService

        user = db.query(User).filter(User.id == account.user_id).first()
        if not user:
            return

        settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
        if not settings:
            return

        is_success = result.get("success", False)
        site_name = getattr(site, 'name', '未知')
        account_name = getattr(account, 'username', '未知')
        message = result.get('message', '')
        error = result.get('error', '')

        # ========== 邮件通知 ==========
        if settings.email_enabled:
            should_email = (is_success and settings.notify_on_success) or (not is_success and settings.notify_on_failure)
            if should_email and (settings.smtp_host and settings.smtp_user and settings.smtp_password and settings.email_from):
                try:
                    notification = NotificationService()
                    notification.configure(
                        host=settings.smtp_host,
                        port=settings.smtp_port or 587,
                        username=settings.smtp_user,
                        password=settings.smtp_password,
                        from_email=settings.email_from
                    )
                    if is_success:
                        await notification.send_success_notification(user, account, site, result)
                    else:
                        await notification.send_failure_notification(user, account, site, result)
                except Exception as e:
                    print(f"[scheduler] 邮件通知失败: {e}")

        # ========== 企业微信机器人通知 ==========
        if settings.wechat_bot_enabled and settings.wechat_bot_webhook:
            should_wechat = (is_success and settings.wechat_bot_notify_on_success) or (not is_success and settings.wechat_bot_notify_on_failure)
            if should_wechat:
                try:
                    bot = WechatBotService(webhook_url=settings.wechat_bot_webhook)
                    await bot.send_signin_notification(
                        account_name=account_name,
                        site_name=site_name,
                        success=is_success,
                        message=message,
                        error=error
                    )
                except Exception as e:
                    print(f"[scheduler] 企业微信通知失败: {e}")

    except Exception as e:
        print(f"[scheduler] 通知发送异常: {e}")


def add_task(task_id: int, cron_expr: str):
    """添加定时任务到调度器"""
    try:
        trigger = CronTrigger.from_crontab(cron_expr)
        scheduler.add_job(
            run_task,
            trigger=trigger,
            args=[task_id],
            id=str(task_id),
            replace_existing=True,
            misfire_grace_time=3600,
            coalesce=True
        )
        print(f"[scheduler] 已注册任务 {task_id} (cron: {cron_expr})")
    except Exception as e:
        print(f"[scheduler] 注册任务 {task_id} 失败: {e}")


def remove_task(task_id: int):
    """移除任务"""
    try:
        scheduler.remove_job(job_id=str(task_id))
        print(f"[scheduler] 已移除任务 {task_id}")
    except Exception as e:
        print(f"[scheduler] 移除任务 {task_id} 失败: {e}")


def start_scheduler():
    """启动调度器并加载所有启用的任务"""
    db = SessionLocal()
    count = 0
    try:
        enabled_tasks = db.query(Task).filter(Task.status == "enabled").all()
        for task in enabled_tasks:
            add_task(task.id, task.cron)
            count += 1
        if not scheduler.running:
            scheduler.start()
        print(f"[scheduler] 调度器启动，已加载 {count} 个定时任务")
    except Exception as e:
        print(f"[scheduler] 启动失败: {e}")
    finally:
        db.close()


def stop_scheduler():
    """停止调度器"""
    try:
        if scheduler.running:
            scheduler.shutdown()
            print("[scheduler] 调度器已停止")
    except Exception as e:
        print(f"[scheduler] 停止失败: {e}")
