from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.config_generator import probe_site
from api.deps import get_current_user
from models.user import User

router = APIRouter(prefix="/api/config-generator", tags=["config-generator"])

class ProbeRequest(BaseModel):
    url: str
    username: Optional[str] = ""
    password: Optional[str] = ""

@router.post("/probe")
async def probe_site_api(req: ProbeRequest, current_user: User = Depends(get_current_user)):
    """探测站点并生成 api_config"""
    if not req.url:
        raise HTTPException(status_code=400, detail="请提供网站地址")

    result = await probe_site(req.url, req.username or "", req.password or "")
    return result
