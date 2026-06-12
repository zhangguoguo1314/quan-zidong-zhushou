from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class SettingsBase(BaseModel):
    email_enabled: bool = False
    notify_on_success: bool = False
    notify_on_failure: bool = True
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None

    # 企业微信机器人
    wechat_bot_enabled: bool = False
    wechat_bot_webhook: Optional[str] = None
    wechat_bot_notify_on_success: bool = False
    wechat_bot_notify_on_failure: bool = True

    display_name: str = ""
    timezone: str = "Asia/Shanghai"
    language: str = "zh-CN"
    extra: Optional[Dict[str, Any]] = None


class SettingsUpdate(SettingsBase):
    pass


class SettingsResponse(SettingsBase):
    id: int
    user_id: int
    updated_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class EmailSettingsUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    notify_on_success: Optional[bool] = None
    notify_on_failure: Optional[bool] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None


class WechatBotSettingsUpdate(BaseModel):
    wechat_bot_enabled: Optional[bool] = None
    wechat_bot_webhook: Optional[str] = None
    wechat_bot_notify_on_success: Optional[bool] = None
    wechat_bot_notify_on_failure: Optional[bool] = None


class TestEmailRequest(BaseModel):
    smtp_host: str
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None


class TestWechatBotRequest(BaseModel):
    webhook_url: str


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str
