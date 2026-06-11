from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


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

    class Config:
        from_attributes = True


class TaskBulkCreate(BaseModel):
    tasks: List[TaskCreate]
