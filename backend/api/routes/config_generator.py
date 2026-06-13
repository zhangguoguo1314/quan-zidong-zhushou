from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from core.database import get_db
from services.config_generator import probe_site
from services.ai_config_generator import fetch_models, generate_config, parse_and_simplify_har
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


@router.post("/parse-har")
async def parse_har_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    上传 HAR 文件，自动解析并精简为登录/签到相关的请求。

    使用方法：
    1. 浏览器 F12 → Network → 勾选 Preserve log
    2. 执行一次完整的 登录 → 签到 操作
    3. 点击 Network 面板左上角的下载按钮，导出 .har 文件
    4. 上传此文件，系统会自动筛选出登录/签到相关的请求
    5. 精简后的内容可直接用于 AI 配置生成
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="请上传 HAR 文件")

    if not file.filename.endswith(".har"):
        raise HTTPException(status_code=400, detail="请上传 .har 格式的文件")

    try:
        # 读取文件内容
        har_content = await file.read()

        # 限制文件大小（最大 50MB）
        if len(har_content) > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="HAR 文件过大，最大支持 50MB")

        # 解码
        try:
            har_text = har_content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                har_text = har_content.decode("gbk")
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="HAR 文件编码无法识别，请确保是 UTF-8 或 GBK 编码")

        # 解析并精简
        result = parse_and_simplify_har(har_text)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "HAR 文件解析失败"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"HAR 文件处理失败: {str(e)}")


@router.post("/generate-from-har")
async def generate_from_har_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传 HAR 文件，自动解析精简后直接调用 AI 生成 api_config。
    一站式完成：上传 HAR → 精简 → AI 分析 → 输出配置。
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="请上传 HAR 文件")

    if not file.filename.endswith(".har"):
        raise HTTPException(status_code=400, detail="请上传 .har 格式的文件")

    # 读取 AI 配置
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

    try:
        # 读取并解析 HAR
        har_content = await file.read()
        if len(har_content) > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="HAR 文件过大，最大支持 50MB")

        try:
            har_text = har_content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                har_text = har_content.decode("gbk")
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="HAR 文件编码无法识别")

        parse_result = parse_and_simplify_har(har_text)

        if not parse_result.get("success"):
            raise HTTPException(status_code=400, detail=parse_result.get("error", "HAR 解析失败"))

        # 将精简后的内容发给 AI
        custom_prompt = settings.ai_custom_prompt or ""
        ai_result = await generate_config(
            api_url=api_url,
            api_key=api_key,
            model=model,
            user_input=parse_result["simplified_text"],
            custom_prompt=custom_prompt,
        )

        # 附加 HAR 解析信息
        ai_result["har_info"] = {
            "total_entries": parse_result["total_entries"],
            "filtered_entries": parse_result["filtered_entries"],
        }

        if not ai_result.get("success"):
            raise HTTPException(status_code=500, detail=ai_result.get("error", "AI 生成失败"))

        return ai_result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")
