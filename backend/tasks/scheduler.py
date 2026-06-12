import asyncio
import json
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
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
    import threading
    thread = threading.Thread(target=_run_in_thread, args=(task_id,), daemon=True)
    thread.start()
    thread.join(timeout=300)


def _run_in_thread(task_id: int):
    """在独立线程中创建 event loop 执行任务，避免与主循环冲突。"""
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
        result = await perform_sign_in(account, site, db=db)
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
        raw_response = result.get("raw_response", "")
        # 构建详细的 result JSON 字符串
        detail = {
            "success": result.get("success", False),
            "error": result.get("error", ""),
            "message": result.get("message", ""),
            "status_code": result.get("status_code", 0),
        }
        log = Log(
            task_id=task_id,
            result=json.dumps(detail, ensure_ascii=False),
            status="success" if result.get("success") else "failed",
            raw_response=raw_response[:2000] if raw_response else "",
        )
        db.add(log)
        db.commit()
    except Exception as e:
        print(f"[scheduler] 写入日志失败: {e}")


async def perform_sign_in(account, site, db=None):
    """根据站点类型动态选择签到插件"""
    site_type = (site.type or "").lower()
    api_config = getattr(site, "api_config", None)

    # 解析 api_config：如果是字符串则 json.loads
    if isinstance(api_config, str):
        try:
            api_config = json.loads(api_config)
        except (json.JSONDecodeError, TypeError):
            api_config = None

    # 如果 api_config 为空，尝试从 SITE_PRESETS 中获取预设配置
    if not api_config:
        api_config = _get_preset_api_config(site_type)

    result = {"success": False, "error": "未知类型"}

    try:
        # 0. Cookie 心跳检查：如果配置了 use_login_cookies 且 cookies 过期，先重新登录刷新
        if api_config and api_config.get("use_login_cookies", False) and db is not None:
            await refresh_cookies_if_needed(account, site, api_config, db)

        # 1. 如果有 api_config（无论是直接配置的还是从预设获取的），使用通用执行器
        if api_config:
            from services.signin_executor import execute_signin
            result = await execute_signin(
                site_type=site_type,
                site_url=getattr(site, "url", "") or "",
                account_username=account.username or "",
                account_password=account.password or "",
                account_token=getattr(account, "token", None),
                account_cookie=getattr(account, "cookie", None),
                api_config=api_config,
                account_id=account.id if account else None,
                db=db,
            )

        # 2. forum / custom - Playwright 爬虫模式（仅保留兼容）
        elif site_type in ["forum", "custom"]:
            try:
                from services.scraper import ScraperService
                scraper = ScraperService()
                result = await scraper.sign_in(account, site)
            except Exception as e:
                result = {"success": False, "error": f"Playwright 模式失败: {str(e)}"}

        # 3. 其他无 api_config 的类型
        else:
            result = {"success": False, "error": f"不支持的站点类型: {site_type}，且未配置 api_config"}

    except Exception as e:
        result = {"success": False, "error": f"签到执行异常: {str(e)}"}

    return result


def _get_preset_api_config(site_type: str):
    """根据站点类型从 SITE_PRESETS 中获取预设的 api_config

    查找策略：
    1. 直接用 site_type 作为 key 查找 SITE_PRESETS
    2. 遍历所有预设，匹配预设的 type 字段
    """
    try:
        from api.routes.sites import SITE_PRESETS

        # 策略1：直接 key 匹配
        preset = SITE_PRESETS.get(site_type)
        if preset and isinstance(preset, dict):
            config = preset.get("api_config")
            if config and isinstance(config, dict):
                return config

        # 策略2：遍历预设，匹配 type 字段
        for _key, preset in SITE_PRESETS.items():
            if isinstance(preset, dict) and preset.get("type") == site_type:
                config = preset.get("api_config")
                if config and isinstance(config, dict):
                    return config

    except Exception as e:
        print(f"[scheduler] 获取预设配置失败: {e}")
    return None


async def refresh_cookies_if_needed(account, site, api_config: dict, db):
    """Cookie 心跳刷新：检查 cookies_updated_at，如果超过心跳间隔则重新登录刷新 cookies。

    默认心跳间隔为 24 小时，可通过 api_config 中的 cookie_heartbeat_hours 字段自定义。
    """
    try:
        from services.signin_executor import execute_signin, save_login_cookies

        cookies_updated_at = getattr(account, "cookies_updated_at", "") or ""
        heartbeat_hours = api_config.get("cookie_heartbeat_hours", 24)

        need_refresh = False
        if not cookies_updated_at:
            need_refresh = True
        else:
            try:
                updated = datetime.strptime(cookies_updated_at, "%Y-%m-%d %H:%M:%S")
                elapsed = (datetime.utcnow() - updated).total_seconds()
                if elapsed > heartbeat_hours * 3600:
                    need_refresh = True
            except (ValueError, TypeError):
                need_refresh = True

        if need_refresh:
            print(f"[scheduler] Cookies 已过期或不存在 (上次更新: {cookies_updated_at})，重新登录刷新...")
            login_result = await execute_signin(
                site_type=(site.type or "").lower(),
                site_url=getattr(site, "url", "") or "",
                account_username=account.username or "",
                account_password=account.password or "",
                account_token=getattr(account, "token", None),
                account_cookie=getattr(account, "cookie", None),
                api_config=api_config,
                account_id=account.id if account else None,
                db=db,
            )
            if login_result.get("success"):
                print(f"[scheduler] Cookies 刷新成功")
            else:
                print(f"[scheduler] Cookies 刷新失败: {login_result.get('error', '未知错误')}")
        else:
            print(f"[scheduler] Cookies 仍在有效期内 (上次更新: {cookies_updated_at})，跳过刷新")

    except Exception as e:
        print(f"[scheduler] Cookie 心跳刷新异常: {e}")


async def send_notification(account, site, result, db):
    """发送通知（邮件 + 企业微信机器人）。

    使用 MessageTemplateService 渲染用户自定义模板。
    """
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

        is_success = bool(result.get("success", False))

        # ========== 邮件通知 ==========
        if settings.email_enabled:
            should_email = (is_success and settings.notify_on_success) or (not is_success and settings.notify_on_failure)
            if should_email and (settings.smtp_host and settings.smtp_user and settings.smtp_password and settings.email_from):
                try:
                    notification = NotificationService(
                        host=settings.smtp_host,
                        port=settings.smtp_port or 587,
                        username=settings.smtp_user,
                        password=settings.smtp_password,
                        from_email=settings.email_from,
                    )
                    await notification.send_signin_notification(
                        to_email=user.email,
                        is_success=is_success,
                        settings=settings,
                        account=account,
                        site=site,
                        user=user,
                        result=result,
                        db=db,
                    )
                except Exception as e:
                    print(f"[scheduler] 邮件通知失败: {e}")

        # ========== 稳定运行报告（邮件） ==========
        if settings.email_enabled and settings.notify_on_stable:
            # 只在成功场景下附加一次稳定报告，避免每次都发
            # 实际频率可由用户通过稳定通知开关控制，这里简单保持不重复发送
            pass

        # ========== 企业微信机器人通知 ==========
        if settings.wechat_bot_enabled and settings.wechat_bot_webhook:
            should_wechat = (is_success and settings.wechat_bot_notify_on_success) or (not is_success and settings.wechat_bot_notify_on_failure)
            if should_wechat:
                try:
                    bot = WechatBotService(webhook_url=settings.wechat_bot_webhook)
                    await bot.send_signin_notification(
                        account_name=getattr(account, 'username', '未知'),
                        site_name=getattr(site, 'name', '未知'),
                        success=is_success,
                        message=result.get('message', ''),
                        error=result.get('error', ''),
                        settings=settings,
                        account=account,
                        site=site,
                        user=user,
                        result=result,
                        db=db,
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

        # 加载定时状态报告任务
        load_status_report_jobs()
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


# ==============================================================
#  定时状态报告
# ==============================================================
def _run_status_report_in_thread(user_id: int):
    """在独立线程中执行状态报告发送。"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_do_send_status_report(user_id))
    finally:
        loop.close()


async def _do_send_status_report(user_id: int):
    """执行状态报告发送的 async 逻辑。"""
    from models.settings import UserSettings
    from services.notification import send_status_report

    db = SessionLocal()
    try:
        settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        if not settings:
            print(f"[status_report] 用户 {user_id} 无设置，跳过")
            return
        if not settings.status_report_enabled:
            print(f"[status_report] 用户 {user_id} 状态报告已关闭，跳过")
            return
        await send_status_report(settings, db)
        print(f"[status_report] 用户 {user_id} 状态报告发送完成")
    except Exception as e:
        print(f"[status_report] 用户 {user_id} 状态报告发送失败: {e}")
    finally:
        db.close()


def run_status_report(user_id: int):
    """调度器触发入口 - 同步函数。"""
    import threading
    thread = threading.Thread(target=_run_status_report_in_thread, args=(user_id,), daemon=True)
    thread.start()
    thread.join(timeout=120)


def add_status_report_job(user_id: int, interval_minutes: int):
    """添加定时状态报告任务到调度器。"""
    try:
        job_id = f"status_report_{user_id}"
        trigger = IntervalTrigger(minutes=interval_minutes)
        scheduler.add_job(
            run_status_report,
            trigger=trigger,
            args=[user_id],
            id=job_id,
            replace_existing=True,
            misfire_grace_time=3600,
            coalesce=True,
        )
        print(f"[scheduler] 已注册状态报告任务 (用户 {user_id}, 间隔 {interval_minutes} 分钟)")
    except Exception as e:
        print(f"[scheduler] 注册状态报告任务失败 (用户 {user_id}): {e}")


def remove_status_report_job(user_id: int):
    """移除定时状态报告任务。"""
    try:
        job_id = f"status_report_{user_id}"
        scheduler.remove_job(job_id=job_id)
        print(f"[scheduler] 已移除状态报告任务 (用户 {user_id})")
    except Exception as e:
        print(f"[scheduler] 移除状态报告任务失败 (用户 {user_id}): {e}")


def load_status_report_jobs():
    """扫描所有用户设置，为启用了状态报告的用户添加定时任务。"""
    from models.settings import UserSettings

    db = SessionLocal()
    try:
        all_settings = db.query(UserSettings).filter(
            UserSettings.status_report_enabled == True,
            UserSettings.status_report_interval > 0,
        ).all()
        for settings in all_settings:
            add_status_report_job(settings.user_id, settings.status_report_interval)
        if all_settings:
            print(f"[scheduler] 已加载 {len(all_settings)} 个状态报告定时任务")
    except Exception as e:
        print(f"[scheduler] 加载状态报告任务失败: {e}")
    finally:
        db.close()
