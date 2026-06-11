import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config import settings


class NotificationService:
    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.username = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.EMAIL_FROM

    async def send_failure_notification(self, account, result):
        """Send email notification when sign-in fails"""
        if not all([self.host, self.username, self.password, self.from_email]):
            return

        subject = f"Sign-in Failed: {account.username}"
        body = f"""
        Sign-in failed for account: {account.username}

        Site: {account.site.name}
        Error: {result.get('error', 'Unknown error')}

        Time: {result.get('timestamp', 'N/A')}
        """

        await self._send_email(account.user.email, subject, body)

    async def send_success_notification(self, account, result):
        """Send email notification when sign-in succeeds"""
        if not all([self.host, self.username, self.password, self.from_email]):
            return

        subject = f"Sign-in Success: {account.username}"
        body = f"""
        Sign-in successful for account: {account.username}

        Site: {account.site.name}
        """

        await self._send_email(account.user.email, subject, body)

    async def _send_email(self, to_email: str, subject: str, body: str):
        """Send an email"""
        message = MIMEMultipart()
        message["From"] = self.from_email
        message["To"] = to_email
        message["Subject"] = subject

        message.attach(MIMEText(body, "plain"))

        try:
            await aiosmtplib.send(
                message,
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                start_tls=True
            )
        except Exception as e:
            print(f"Failed to send email: {e}")
