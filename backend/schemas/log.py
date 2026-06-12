from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LogResponse(BaseModel):
    id: int
    task_id: int
    result: Optional[str] = None
    status: str
    account_username: Optional[str] = ""
    site_name: Optional[str] = ""
    task_name: Optional[str] = ""
    created_at: datetime

    class Config:
        from_attributes = True
