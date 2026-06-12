from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import asyncio

from core.database import get_db
from models.site import Site
from schemas.site import SiteCreate, SiteUpdate, SiteResponse, SiteTestRequest, SiteBulkImportRequest
from api.deps import get_current_user
from models.user import User

router = APIRouter(prefix="/api/sites", tags=["sites"])


# 常用站点预配置模板 - 用户可以一键导入
SITE_PRESETS = {
    "lizhiyu": {
        "name": "辉哥boy公益中转站",
        "display_name": "辉哥公益",
        "category": "公益站点",
        "type": "custom-api",
        "description": "https://lizhiyu.appleinc.cn - Bearer Token 认证",
        "api_config": {
            "login_url": "https://lizhiyu.appleinc.cn/v1/user/login-pwd",
            "login_method": "POST",
            "login_body_template": '{"email": "{{username}}", "password": "{{password}}"}',
            "login_content_type": "application/json",
            "token_path": "token",
            "signin_url": "https://lizhiyu.appleinc.cn/v1/user/signin",
            "signin_method": "POST",
            "signin_body": "{}",
            "signin_content_type": "application/json",
            "auth_header_template": "Bearer {{token}}",
            "auth_header_name": "Authorization",
            "success_field": "",
            "message_field": "message"
        }
    },
    "gemai-template": {
        "name": "哈基米API站（通用模板）",
        "display_name": "哈基米API",
        "category": "API服务",
        "type": "custom-api",
        "description": "https://api.gemai.cc 风格的站点 - Session Cookie + Header 认证",
        "api_config": {
            "login_url": "https://api.gemai.cc/api/user/login",
            "login_method": "POST",
            "login_body_template": '{"username": "{{username}}", "password": "{{password}}"}',
            "login_content_type": "application/json",
            "token_path": "data.id",
            "signin_url": "https://api.gemai.cc/api/user/checkin",
            "signin_method": "POST",
            "signin_body": "{}",
            "signin_content_type": "application/json",
            "auth_header_template": "{{token}}",
            "auth_header_name": "New-Api-User",
            "success_field": "success",
            "message_field": "message"
        }
    }
}


# 预设分类
SITE_CATEGORIES = ["API服务", "公益站点", "论坛社区", "资源下载", "工具网站", "购物电商", "其他"]


@router.get("/presets")
def get_site_presets(current_user: User = Depends(get_current_user)):
    return {"presets": SITE_PRESETS, "categories": SITE_CATEGORIES}


@router.get("/categories")
def get_site_categories(current_user: User = Depends(get_current_user)):
    return {"categories": SITE_CATEGORIES}


@router.get("", response_model=List[SiteResponse])
def get_sites(
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Site)
    if category and category != "全部":
        query = query.filter(Site.category == category)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (Site.name.like(like)) | (Site.display_name.like(like))
        )
    sites = query.all()
    return sites


@router.get("/grouped")
def get_sites_grouped(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sites = db.query(Site).all()
    groups: dict = {}
    for site in sites:
        cat = site.category or "其他"
        if cat not in groups:
            groups[cat] = []
        groups[cat].append({
            "id": site.id,
            "name": site.name,
            "display_name": site.display_name or site.name,
            "type": site.type,
            "url": site.url,
            "category": site.category,
            "created_at": site.created_at.isoformat() if site.created_at else None
        })
    return {"groups": groups}


@router.post("", response_model=SiteResponse)
def create_site(
    site_data: SiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    site = Site(**site_data.model_dump())
    db.add(site)
    db.commit()
    db.refresh(site)
    return site


@router.get("/{site_id}", response_model=SiteResponse)
def get_site(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    return site


@router.put("/{site_id}", response_model=SiteResponse)
def update_site(
    site_id: int,
    site_data: SiteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

    update_data = site_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(site, key, value)
    db.commit()
    db.refresh(site)
    return site


@router.delete("/{site_id}")
def delete_site(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    db.delete(site)
    db.commit()
    return {"message": "Site deleted successfully"}


@router.post("/bulk")
def bulk_create_sites(
    data: SiteBulkImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    created = []
    for site_data in data.sites:
        site = Site(**site_data.model_dump())
        db.add(site)
        created.append(site)
    db.commit()
    for site in created:
        db.refresh(site)
    return {"sites": created, "count": len(created)}


@router.get("/export/all")
def export_all_sites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sites = db.query(Site).all()
    export_data = []
    for site in sites:
        export_data.append({
            "name": site.name,
            "display_name": site.display_name or "",
            "category": site.category or "其他",
            "type": site.type,
            "url": site.url or "",
            "api_config": site.api_config
        })
    return {"exported_at": datetime.now().isoformat(), "sites": export_data}


@router.post("/test")
def test_sign_in(
    test_request: SiteTestRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        from plugins.custom_api.plugin import CustomApiPlugin
        from plugins.gemai.plugin import GemaiPlugin

        class TestAccount:
            def __init__(self, username, password):
                self.username = username
                self.password = password
                self.cookie = ""

        class TestSite:
            def __init__(self, site_type, api_config):
                self.type = site_type
                self.api_config = api_config
                self.url = ""

        account = TestAccount(test_request.username, test_request.password)
        site = TestSite(test_request.site_type, test_request.api_config)

        if test_request.site_type == "gemai":
            plugin = GemaiPlugin()
        else:
            plugin = CustomApiPlugin()

        result = asyncio.run(plugin.sign_in(account, site))
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}
