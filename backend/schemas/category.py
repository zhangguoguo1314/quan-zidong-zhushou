from pydantic import BaseModel, field_serializer
from typing import Optional
from datetime import datetime, timezone, timedelta


def _to_beijing_iso(value: datetime) -> Optional[str]:
    """将时间统一转换为北京时间 (UTC+8) 后输出 ISO 格式"""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    beijing_tz = timezone(timedelta(hours=8))
    return value.astimezone(beijing_tz).isoformat()


class CategoryBase(BaseModel):
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    sort_order: Optional[int] = 0
    is_public: Optional[bool] = False


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    sort_order: Optional[int] = None
    is_public: Optional[bool] = None


class CategoryResponse(CategoryBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, value: datetime) -> Optional[str]:
        return _to_beijing_iso(value)

    class Config:
        from_attributes = True
