from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class AccountBase(BaseModel):
    site_id: int
    username: str


class AccountCreate(AccountBase):
    password: Optional[str] = None
    token: Optional[str] = None
    cookie: Optional[str] = None


class AccountUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None
    cookie: Optional[str] = None
    status: Optional[str] = None


class AccountResponse(AccountBase):
    id: int
    user_id: int
    password: Optional[str] = None
    token: Optional[str] = None
    cookie: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AccountImportRequest(BaseModel):
    site_id: int
    accounts: List[AccountCreate]
