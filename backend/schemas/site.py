from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SiteBase(BaseModel):
    name: str
    type: str
    url: Optional[str] = None


class SiteCreate(SiteBase):
    pass


class SiteUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    url: Optional[str] = None


class SiteResponse(SiteBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
