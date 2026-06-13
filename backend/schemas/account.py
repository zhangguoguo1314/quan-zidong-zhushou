from pydantic import BaseModel, field_serializer
from typing import Optional, List
from datetime import datetime, timezone, timedelta


def _to_beijing_iso(value: datetime) -> Optional[str]:
    """将时间统一转换为北京时间 (UTC+8) 后输出 ISO 格式"""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    beijing_tz = timezone(timedelta(hours=8))
    return value.astimezone(beijing_tz).isoformat()


class AccountBase(BaseModel):
    site_id: int
    username: str


class AccountCreate(AccountBase):
    nickname: Optional[str] = ""
    password: Optional[str] = None
    token: Optional[str] = None
    cookie: Optional[str] = None


class AccountUpdate(BaseModel):
    username: Optional[str] = None
    nickname: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None
    cookie: Optional[str] = None
    status: Optional[str] = None


class AccountResponse(AccountBase):
    id: int
    user_id: int
    nickname: Optional[str] = ""
    password: Optional[str] = None
    token: Optional[str] = None
    cookie: Optional[str] = None
    status: str
    total_signins: Optional[int] = 0
    success_count: Optional[int] = 0
    fail_count: Optional[int] = 0
    created_at: datetime

    @field_serializer('created_at')
    def serialize_datetime(self, value: datetime) -> Optional[str]:
        return _to_beijing_iso(value)

    class Config:
        from_attributes = True


class AccountImportRequest(BaseModel):
    site_id: int
    accounts: List[AccountCreate]
