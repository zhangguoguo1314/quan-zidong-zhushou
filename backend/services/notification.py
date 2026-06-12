"""
邮件通知服务 - NotificationService

使用 MessageTemplateService 渲染用户自定义的邮件模板。
"""

from __future__ import annotations

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any


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
                timeout=30,
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
