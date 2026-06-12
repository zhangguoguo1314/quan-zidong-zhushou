from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from core.database import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)

    # 邮件通知开关
    email_enabled = Column(Boolean, default=False)
    notify_on_success = Column(Boolean, default=False)
    notify_on_failure = Column(Boolean, default=True)

    # SMTP 配置
    smtp_host = Column(String(200))
    smtp_port = Column(Integer, default=587)
    smtp_user = Column(String(200))
    smtp_password = Column(String(200))
    email_from = Column(String(200))

    # 企业微信机器人配置
    wechat_bot_enabled = Column(Boolean, default=False)
    wechat_bot_webhook = Column(String(500))
    wechat_bot_notify_on_success = Column(Boolean, default=False)
    wechat_bot_notify_on_failure = Column(Boolean, default=True)

    # 个性化设置
    display_name = Column(String(100), default="")
    timezone = Column(String(50), default="Asia/Shanghai")
    language = Column(String(20), default="zh-CN")

    # 自定义扩展字段
    extra = Column(JSON, nullable=True)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
