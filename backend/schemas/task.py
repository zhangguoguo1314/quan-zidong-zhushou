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


class TaskBase(BaseModel):
    account_id: int
    cron: str


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    cron: Optional[str] = None
    status: Optional[str] = None


class TaskResponse(TaskBase):
    id: int
    last_run: Optional[datetime] = None
    status: str
    created_at: datetime

    @field_serializer('last_run', 'created_at')
    def serialize_datetime(self, value: datetime) -> Optional[str]:
        return _to_beijing_iso(value)

    class Config:
        from_attributes = True


class TaskBulkCreate(BaseModel):
    tasks: List[TaskCreate]
