import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


class NotificationService:
    """邮件通知服务

    支持两种使用方式：
    1. configure() 方式 - 从数据库读取用户保存的配置
    2. 传统方式 - 从 settings 读取（保留兼容）
    """

    def __init__(self):
        self.host = None
        self.port = 587
        self.username = None
        self.password = None
        self.from_email = None

    def configure(self, host: str, port: int, username: str, password: str, from_email: str):
        """动态配置 SMTP 参数"""
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email

    async def send_failure_notification(self, user, account, site, result):
        """发送失败通知邮件"""
        if not all([self.host, self.username, self.password, self.from_email]):
            return False

        subject = f"[签到失败] {account.username} @ {getattr(site, 'name', '未知')}"
        site_name = getattr(site, 'name', '未知')
        body = f"""您好，

以下是签到失败的详细信息：

【账号】{account.username}
【站点】{site_name}
【错误信息】{result.get('error', 'Unknown error')}
【时间】{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

--
自动签到系统"""

        await self._send_email(user.email, subject, body)
        return True

    async def send_success_notification(self, user, account, site, result):
        """发送成功通知邮件"""
        if not all([self.host, self.username, self.password, self.from_email]):
            return False

        subject = f"[签到成功] {account.username} @ {getattr(site, 'name', '未知')}"
        site_name = getattr(site, 'name', '未知')
        message = result.get('message', 'Success')

        body = f"""您好，

以下是签到成功的详细信息：

【账号】{account.username}
【站点】{site_name}
【结果】{message}
【时间】{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

--
自动签到系统"""

        await self._send_email(user.email, subject, body)
        return True

    async def _send_email(self, to_email: str, subject: str, body: str):
        """实际发送邮件"""
        message = MIMEMultipart()
        message["From"] = self.from_email
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain", "utf-8"))

        try:
            await aiosmtplib.send(
                message,
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                start_tls=True,
                timeout=30
            )
            print(f"[notification] 邮件发送成功 -> {to_email}")
        except Exception as e:
            print(f"[notification] 邮件发送失败: {e}")
