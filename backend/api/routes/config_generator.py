from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from core.database import get_db
from services.config_generator import probe_site
from services.ai_config_generator import fetch_models, generate_config
from api.deps import get_current_user
from models.user import User
from models.settings import UserSettings

router = APIRouter(prefix="/api/config-generator", tags=["config-generator"])


class ProbeRequest(BaseModel):
    url: str
    username: Optional[str] = ""
    password: Optional[str] = ""


class FetchModelsRequest(BaseModel):
    api_url: str
    api_key: str


class GenerateRequest(BaseModel):
    user_input: str
    use_custom_prompt: bool = False


@router.post("/probe")
async def probe_site_api(req: ProbeRequest, current_user: User = Depends(get_current_user)):
    """探测站点并生成 api_config（暴力探测）"""
    if not req.url:
        raise HTTPException(status_code=400, detail="请提供网站地址")

    result = await probe_site(req.url, req.username or "", req.password or "")
    return result


@router.post("/fetch-models")
async def fetch_models_api(
    req: FetchModelsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """拉取第三方 LLM API 的模型列表"""
    if not req.api_url:
        raise HTTPException(status_code=400, detail="请提供 API 地址")
    if not req.api_key:
        raise HTTPException(status_code=400, detail="请提供 API Key")

    try:
        models = await fetch_models(req.api_url, req.api_key)
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def generate_config_api(
    req: GenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """使用 AI 生成 api_config"""
    if not req.user_input:
        raise HTTPException(status_code=400, detail="请提供网站信息")

    # 从 UserSettings 读取 AI 配置
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not settings:
        raise HTTPException(status_code=400, detail="请先在设置中配置 AI API 信息")

    api_url = settings.ai_api_url or ""
    api_key = settings.ai_api_key or ""
    model = settings.ai_model or ""

    if not api_url:
        raise HTTPException(status_code=400, detail="请先在设置中配置 AI API 地址")
    if not api_key:
        raise HTTPException(status_code=400, detail="请先在设置中配置 AI API Key")
    if not model:
        raise HTTPException(status_code=400, detail="请先在设置中选择 AI 模型")

    # 确定使用哪个提示词
    custom_prompt = ""
    if req.use_custom_prompt:
        custom_prompt = settings.ai_custom_prompt or ""

    result = await generate_config(
        api_url=api_url,
        api_key=api_key,
        model=model,
        user_input=req.user_input,
        custom_prompt=custom_prompt,
    )

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "AI 生成失败"))

    return result
