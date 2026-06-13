from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
import asyncio

from core.database import get_db
from models.site import Site
from models.category import Category
from schemas.site import SiteCreate, SiteUpdate, SiteResponse, SiteTestRequest, SiteBulkImportRequest
from schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from api.deps import get_current_user
from models.user import User

router = APIRouter(prefix="/api/sites", tags=["sites"])


# 常用站点预配置模板 - 用户可以一键导入
SITE_PRESETS = {
    "lizhiyu": {
        "name": "荔枝鱼公益站",
        "display_name": "荔枝鱼",
        "category": "公益站点",
        "type": "custom-api",
        "url": "https://lizhiyu.appleinc.cn",
        "description": "每日签到获取免费额度，Bearer Token 认证",
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
    "gemai": {
        "name": "哈基米API站",
        "display_name": "哈基米API",
        "category": "API服务",
        "type": "custom-api",
        "url": "https://api.gemai.cc",
        "description": "AI模型聚合平台，每日签到获取5-20随机额度（基于New API，Session Cookie认证）",
        "api_config": {
            "login_url": "https://api.gemai.cc/api/user/login",
            "login_method": "POST",
            "login_body_template": '{"username": "{{username}}", "password": "{{password}}"}',
            "login_content_type": "application/json",
            "token_path": "",
            "signin_url": "https://api.gemai.cc/api/user/checkin",
            "signin_method": "POST",
            "signin_body": "{}",
            "signin_content_type": "application/json",
            "auth_header_template": "",
            "auth_header_name": "",
            "success_field": "success",
            "message_field": "message",
            "use_login_cookies": true
        }
    },
    "binmt": {
        "name": "binmt论坛",
        "display_name": "binmt论坛",
        "category": "论坛社区",
        "type": "custom-api",
        "url": "https://bbs.binmt.cc",
        "description": "Discuz论坛，每日签到获取积分，Misign插件",
        "api_config": {
            "login_url": "https://bbs.binmt.cc/member.php?mod=logging&action=login&loginsubmit=yes&infloat=yes&lssubmit=yes&inajax=1",
            "login_method": "POST",
            "login_body_template": "username={{username}}&password={{password}}&quickforward=yes&handlekey=login",
            "login_content_type": "application/x-www-form-urlencoded",
            "token_path": "",
            "signin_url": "https://bbs.binmt.cc/plugin.php?id=k_misign:sign&operation=qiandao&format=empty",
            "signin_method": "GET",
            "signin_body": "{}",
            "signin_content_type": "application/json",
            "auth_header_template": "",
            "auth_header_name": "",
            "success_field": "",
            "message_field": "",
            "use_login_cookies": True
        }
    }
}


# 预设分类
SITE_CATEGORIES = ["API服务", "公益站点", "论坛社区", "资源下载", "工具网站", "购物电商", "其他"]


@router.get("/presets")
def get_site_presets(current_user: User = Depends(get_current_user)):
    return {"presets": SITE_PRESETS, "categories": SITE_CATEGORIES}


# ==================== 分类路由（固定路径，必须在 /{site_id} 之前） ====================

@router.get("/categories", response_model=List[CategoryResponse])
def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    categories = (
        db.query(Category)
        .filter(Category.user_id == current_user.id)
        .order_by(Category.sort_order.asc(), Category.name.asc())
        .all()
    )
    return categories


@router.get("/categories/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    if category.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return category


@router.post("/categories", response_model=CategoryResponse)
def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    data = category_data.model_dump()
    data["user_id"] = current_user.id
    category = Category(**data)
    db.add(category)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category name already exists")
    db.refresh(category)
    return category


@router.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    if category.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    update_data = category_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(category, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category name already exists")
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    if category.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    db.delete(category)
    db.commit()
    return {"message": "Category deleted successfully"}


# ==================== 站点列表/创建路由 ====================

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
    grouped: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sites = db.query(Site).all()
    site_dicts = []
    for site in sites:
        site_dicts.append({
            "id": site.id,
            "name": site.name,
            "display_name": site.display_name or site.name,
            "type": site.type,
            "url": site.url,
            "category": site.category or "其他",
            "created_at": site.created_at.isoformat() if site.created_at else None
        })

    # 新格式：按 category 分组的数组
    groups_map: Dict[str, list] = {}
    for sd in site_dicts:
        cat = sd.get("category") or "其他"
        if cat not in groups_map:
            groups_map[cat] = []
        groups_map[cat].append(sd)

    # 保持 groups 顺序（按分类名称）
    grouped_list = [{"category": k, "sites": v} for k, v in groups_map.items()]

    # 兼容旧的 grouped=true 逻辑：同时返回 groups dict 与 sites 平铺数组
    result: Dict[str, Any] = {"groups": grouped_list}
    if grouped is True or grouped is None:
        # 保留旧前端使用的 dict 结构
        result["groups_dict"] = groups_map
    result["sites"] = site_dicts
    return result


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


# ==================== 固定路径操作路由（必须在 /{site_id} 之前） ====================

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


# ==================== 动态路径路由（/{site_id}，放在最后） ====================

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


class ManualSigninRequest(BaseModel):
    account_id: int


@router.post("/{site_id}/signin")
async def manual_sign_in(
    site_id: int,
    request: ManualSigninRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """手动签到 - 立即执行一次签到操作"""
    from models.account import Account
    from tasks.scheduler import perform_sign_in

    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    account = db.query(Account).filter(
        Account.id == request.account_id,
        Account.site_id == site_id,
        Account.user_id == current_user.id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    result = await perform_sign_in(account, site)
    return result
