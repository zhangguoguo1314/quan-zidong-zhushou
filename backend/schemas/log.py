from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LogResponse(BaseModel):
    id: int
    task_id: int
    result: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
