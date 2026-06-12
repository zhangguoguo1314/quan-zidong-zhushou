"""
邮件通知服务 - NotificationService

使用 MessageTemplateService 渲染用户自定义的邮件模板。
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any

import aiosmtplib


class NotificationService:
    def __init__(self, host: Optional[str] = None, port: int = 587,
                 username: Optional[str] = None, password: Optional[str] = None,
                 from_email: Optional[str] = None):
        self.host = host
        self.port = port or 587
        self.username = username
        self.password = password
        self.from_email = from_email

    def configure(self, host: str, port: int, username: str, password: str, from_email: str):
        self.host = host
        self.port = port or 587
        self.username = username
        self.password = password
        self.from_email = from_email

    # --------- 内部 ---------
    async def _send_email(self, to_email: str, subject: str, body: str) -> bool:
        """真正的邮件发送逻辑。返回 True 表示成功。"""
        if not self.host or not self.username or not self.password:
            return False
        try:
            message = MIMEMultipart()
            message["From"] = self.from_email or self.username
            message["To"] = to_email
            message["Subject"] = subject
            message.attach(MIMEText(body, "plain", "utf-8"))

            await aiosmtplib.send(
                message,
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                start_tls=True,
                timeout=10,
            )
            print(f"[notification] 邮件发送成功 -> {to_email}")
            return True
        except Exception as e:
            print(f"[notification] 邮件发送失败: {e}")
            return False

    # --------- 对外 API ---------
    async def send_signin_notification(
        self,
        to_email: str,
        is_success: bool,
        settings: Any,
        account: Any = None,
        site: Any = None,
        user: Any = None,
        result: Optional[Dict[str, Any]] = None,
        db: Any = None,
    ) -> bool:
        """根据自定义模板发送签到结果邮件。"""
        from services.message_template import MessageTemplateService
        rendered = MessageTemplateService.render_signin_email(
            settings=settings, is_success=is_success,
            account=account, site=site, user=user, result=result, db=db,
        )
        return await self._send_email(to_email, rendered["subject"], rendered["body"])

    async def send_stable_report(
        self,
        to_email: str,
        settings: Any,
        user: Any = None,
        db: Any = None,
    ) -> bool:
        """发送稳定运行报告。"""
        from services.message_template import MessageTemplateService
        rendered = MessageTemplateService.render_stable_email(
            settings=settings, user=user, db=db,
        )
        return await self._send_email(to_email, rendered["subject"], rendered["body"])

    async def send_system_error(
        self,
        to_email: str,
        settings: Any,
        error_message: str,
        user: Any = None,
    ) -> bool:
        """发送系统异常告警。"""
        from services.message_template import MessageTemplateService
        rendered = MessageTemplateService.render_system_error_email(
            settings=settings, user=user, error_message=error_message,
        )
        return await self._send_email(to_email, rendered["subject"], rendered["body"])

    # 保留老方法，兼容现有代码
    async def send_success_notification(self, user, account, site, result):
        to_email = getattr(user, "email", None)
        if not to_email:
            return False
        # 老方法没有 settings 可用，构造一个临时的
        from services.message_template import MessageTemplateService
        from models.settings import UserSettings
        fake_settings = UserSettings(user_id=getattr(user, "id", 0))
        rendered = MessageTemplateService.render_signin_email(
            settings=fake_settings, is_success=True,
            account=account, site=site, user=user, result=result,
        )
        return await self._send_email(to_email, rendered["subject"], rendered["body"])

    async def send_failure_notification(self, user, account, site, result):
        to_email = getattr(user, "email", None)
        if not to_email:
            return False
        from services.message_template import MessageTemplateService
        from models.settings import UserSettings
        fake_settings = UserSettings(user_id=getattr(user, "id", 0))
        rendered = MessageTemplateService.render_signin_email(
            settings=fake_settings, is_success=False,
            account=account, site=site, user=user, result=result,
        )
        return await self._send_email(to_email, rendered["subject"], rendered["body"])


# ==============================================================
#  定时状态报告（模块级函数）
# ==============================================================
async def send_status_report(user_settings, db) -> dict:
    """发送系统运行状态报告（邮件 + 企业微信）。

    参数:
        user_settings: UserSettings 实例
        db: SQLAlchemy Session

    返回:
        {"email": bool, "wechat": bool}
    """
    from models.site import Site
    from models.account import Account
    from models.task import Task
    from models.log import Log
    from models.user import User
    from services.wechat_bot import WechatBotService
    from services.message_template import MessageTemplateService

    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    report_time = now.strftime("%Y-%m-%d %H:%M:%S")

    user_id = user_settings.user_id
    user = db.query(User).filter(User.id == user_id).first()

    # ---------- 统计数据 ----------
    total_sites = db.query(Site).filter(Site.accounts.any(Account.user_id == user_id)).count()
    total_accounts = db.query(Account).filter(Account.user_id == user_id).count()
    total_tasks = db.query(Task).join(Account).filter(Account.user_id == user_id).count()
    active_tasks = db.query(Task).join(Account).filter(
        Account.user_id == user_id, Task.status == "enabled"
    ).count()

    # 今日签到统计：通过 Log 表，关联 task -> account -> user
    today_success = db.query(Log).join(Task).join(Account).filter(
        Account.user_id == user_id,
        Log.status == "success",
        Log.created_at >= today_start,
    ).count()
    today_fail = db.query(Log).join(Task).join(Account).filter(
        Account.user_id == user_id,
        Log.status == "failed",
        Log.created_at >= today_start,
    ).count()
    total_today = today_success + today_fail
    success_rate = round(today_success / total_today * 100, 2) if total_today > 0 else 100.0

    # 计算系统运行时长（从最早的 task 创建时间算起）
    earliest_task = db.query(Task).join(Account).filter(
        Account.user_id == user_id
    ).order_by(Task.created_at.asc()).first()
    if earliest_task and earliest_task.created_at:
        uptime_hours = round((now - earliest_task.created_at).total_seconds() / 3600, 1)
    else:
        uptime_hours = 0

    display_name = getattr(user_settings, "display_name", "") or "自动签到系统"

    # ---------- 构建报告内容 ----------
    # 企业微信 Markdown 报告
    bot_report = (
        f"## 📊 系统运行状态报告\n"
        f"> 报告时间: {report_time}\n\n"
        f"**运行概况**\n"
        f"- 🌐 管理站点: {total_sites} 个\n"
        f"- 👤 管理账号: {total_accounts} 个\n"
        f"- ⏰ 定时任务: {total_tasks} 个（活跃: {active_tasks}）\n\n"
        f"**今日签到统计**\n"
        f"- ✅ 成功: {today_success} 次\n"
        f"- ❌ 失败: {today_fail} 次\n"
        f"- 📈 成功率: {success_rate}%\n\n"
        f"**系统状态**\n"
        f"- 🟢 系统运行正常\n"
        f"- ⏱ 已稳定运行 {uptime_hours} 小时\n\n"
        f"---\n> 来自 全自动签到助手 {display_name}"
    )

    # 邮件纯文本报告
    email_report = (
        f"系统运行状态报告\n"
        f"报告时间: {report_time}\n\n"
        f"【运行概况】\n"
        f"  管理站点: {total_sites} 个\n"
        f"  管理账号: {total_accounts} 个\n"
        f"  定时任务: {total_tasks} 个（活跃: {active_tasks}）\n\n"
        f"【今日签到统计】\n"
        f"  成功: {today_success} 次\n"
        f"  失败: {today_fail} 次\n"
        f"  成功率: {success_rate}%\n\n"
        f"【系统状态】\n"
        f"  系统运行正常\n"
        f"  已稳定运行 {uptime_hours} 小时\n\n"
        f"--\n自动签到系统 {display_name}"
    )

    result = {"email": False, "wechat": False}

    # ---------- 发送邮件 ----------
    if user_settings.email_enabled and user and user.email:
        try:
            notification = NotificationService(
                host=user_settings.smtp_host,
                port=user_settings.smtp_port or 587,
                username=user_settings.smtp_user,
                password=user_settings.smtp_password,
                from_email=user_settings.email_from,
            )
            email_subject = f"[状态报告] {display_name} - {report_time}"
            ok = await notification._send_email(user.email, email_subject, email_report)
            result["email"] = ok
            if ok:
                print(f"[status_report] 邮件发送成功 -> {user.email}")
        except Exception as e:
            print(f"[status_report] 邮件发送失败: {e}")

    # ---------- 发送企业微信 ----------
    if user_settings.wechat_bot_enabled and user_settings.wechat_bot_webhook:
        try:
            bot = WechatBotService(webhook_url=user_settings.wechat_bot_webhook)
            bot_result = bot.send_markdown(bot_report)
            result["wechat"] = bot_result.get("success", False)
            if result["wechat"]:
                print("[status_report] 企业微信消息发送成功")
            else:
                print(f"[status_report] 企业微信消息发送失败: {bot_result.get('error', '')}")
        except Exception as e:
            print(f"[status_report] 企业微信消息发送失败: {e}")

    # ---------- 更新最后发送时间 ----------
    user_settings.status_report_last_sent = report_time
    db.commit()

    return result
