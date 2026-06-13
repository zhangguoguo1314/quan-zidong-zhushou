from pydantic import BaseModel, Field, field_serializer
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta


def _to_beijing_iso(value: datetime) -> Optional[str]:
    """将时间统一转换为北京时间 (UTC+8) 后输出 ISO 格式"""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    beijing_tz = timezone(timedelta(hours=8))
    return value.astimezone(beijing_tz).isoformat()


class ApiConfig(BaseModel):
    login_url: str = ""
    login_method: str = "POST"
    login_body_template: str = '{"username": "{{username}}", "password": "{{password}}"}'
    login_content_type: str = "application/json"
    token_path: str = "token"
    signin_url: str = ""
    signin_method: str = "POST"
    signin_body: str = "{}"
    signin_content_type: str = "application/json"
    auth_header_template: str = "Bearer {{token}}"
    auth_header_name: str = "Authorization"
    success_field: str = ""
    message_field: str = ""


class SiteBase(BaseModel):
    name: str
    display_name: Optional[str] = ""
    category: Optional[str] = "其他"
    type: str
    url: Optional[str] = None
    api_config: Optional[Dict[str, Any]] = None


class SiteCreate(SiteBase):
    pass


class SiteUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    category: Optional[str] = None
    type: Optional[str] = None
    url: Optional[str] = None
    api_config: Optional[Dict[str, Any]] = None


class SiteResponse(SiteBase):
    id: int
    created_at: datetime

    @field_serializer('created_at')
    def serialize_datetime(self, value: datetime) -> Optional[str]:
        return _to_beijing_iso(value)

    class Config:
        from_attributes = True


class SiteTestRequest(BaseModel):
    site_type: str
    api_config: Optional[Dict[str, Any]] = None
    username: str
    password: str


class SitePreset(BaseModel):
    name: str
    type: str
    description: str
    api_config: Dict[str, Any]


class SiteBulkImportRequest(BaseModel):
    sites: List[SiteCreate]
