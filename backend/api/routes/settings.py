"""
/api/settings 相关路由。

主要功能：
- 读取 / 保存用户设置（SMTP、微信机器人、消息模板等）
- 模板预览、模板恢复默认
- 发送测试邮件 / 测试微信机器人
- 修改密码
"""

import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from core.database import get_db
from core.security import verify_password, get_password_hash
from models.settings import UserSettings
from models.user import User
from services.message_template import MessageTemplateService
from schemas.settings import (
    SettingsUpdate, SettingsResponse, EmailSettingsUpdate,
    WechatBotSettingsUpdate, TestEmailRequest, TestWechatBotRequest,
    PasswordChangeRequest, TemplatePreviewRequest, ResetTemplatesRequest,
)
from api.deps import get_current_user

router = APIRouter(prefix="/api/settings", tags=["settings"])


# ==============================================================
#  工具
# ==============================================================
def _get_or_create_settings(db: Session, user_id: int) -> UserSettings:
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if not settings:
        settings = UserSettings(user_id=user_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


# ==============================================================
#  设置 CRUD
# ==============================================================
@router.get("", response_model=SettingsResponse)
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_or_create_settings(db, current_user.id)


@router.put("", response_model=SettingsResponse)
def update_settings(
    data: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    settings = _get_or_create_settings(db, current_user.id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(settings, key, value)
    db.commit()
    db.refresh(settings)
    return settings


# ==============================================================
#  模板相关
# ==============================================================
@router.post("/templates/preview")
def preview_template(
    data: TemplatePreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """预览模板渲染结果。

    - ``scenario``: success / failure / stable / error
    - 会根据 scenario 自动填充一些合理的示例变量，以便用户看真实效果
    """
    # 构造一个示例上下文
    scenario = (data.scenario or "success").lower()

    if scenario == "success":
        sample = {
            "account_name": "demo_user",
            "username": "demo_user",
            "site_name": "示例论坛",
            "site_display_name": "示例论坛 Demo",
            "site_category": "论坛社区",
            "message": "签到成功，获得 10 积分",
            "error": "",
            "success_count": "5",
            "fail_count": "0",
            "total_count": "5",
            "success_rate": "100",
            "user_email": current_user.email or "you@example.com",
            "display_name": "我的自动签到",
        }
    elif scenario == "failure":
        sample = {
            "account_name": "demo_user",
            "username": "demo_user",
            "site_name": "示例论坛",
            "site_display_name": "示例论坛 Demo",
            "site_category": "论坛社区",
            "message": "",
            "error": "登录失败：用户名或密码错误 (HTTP 401)",
            "success_count": "4",
            "fail_count": "1",
            "total_count": "5",
            "success_rate": "80",
            "user_email": current_user.email or "you@example.com",
            "display_name": "我的自动签到",
        }
    elif scenario == "stable":
        sample = {
            "success_count": "12",
            "fail_count": "0",
            "total_count": "12",
            "success_rate": "100",
            "user_email": current_user.email or "you@example.com",
            "display_name": "我的自动签到",
        }
    else:  # error
        sample = {
            "error": "数据库连接超时，请检查服务是否正常",
            "user_email": current_user.email or "you@example.com",
            "display_name": "我的自动签到",
        }

    # 允许调用方覆盖
    if data.custom_context:
        sample.update(data.custom_context)

    rendered = MessageTemplateService.render(data.template, sample)
    return {
        "scenario": scenario,
        "template": data.template,
        "context": sample,
        "rendered": rendered,
    }


@router.post("/templates/reset-defaults", response_model=SettingsResponse)
def reset_templates_to_defaults(
    data: ResetTemplatesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """恢复模板为默认值。

    如果 ``targets`` 为空列表，将重置全部 8 个模板字段；
    否则只重置 targets 中指定的字段（字段名用下划线，如
    ``tpl_email_success_subject``、``tpl_bot_failure``）。
    """
    settings = _get_or_create_settings(db, current_user.id)
    defaults = MessageTemplateService.get_defaults()
    # 构建字段 -> 默认值 的完整映射
    field_defaults = {
        "tpl_email_success_subject": defaults["email_success_subject"],
        "tpl_email_success_body": defaults["email_success_body"],
        "tpl_email_failure_subject": defaults["email_failure_subject"],
        "tpl_email_failure_body": defaults["email_failure_body"],
        "tpl_email_stable_subject": defaults["email_stable_subject"],
        "tpl_email_stable_body": defaults["email_stable_body"],
        "tpl_email_error_subject": defaults["email_error_subject"],
        "tpl_email_error_body": defaults["email_error_body"],
        "tpl_bot_success": defaults["bot_success"],
        "tpl_bot_failure": defaults["bot_failure"],
        "tpl_bot_stable": defaults["bot_stable"],
        "tpl_bot_error": defaults["bot_error"],
    }

    targets = (data.targets or []) if data else []
    if targets:
        for field in targets:
            if field in field_defaults:
                setattr(settings, field, field_defaults[field])
    else:
        for field, default_value in field_defaults.items():
            setattr(settings, field, default_value)

    db.commit()
    db.refresh(settings)
    return settings


@router.get("/templates/defaults")
def get_template_defaults(
    _: User = Depends(get_current_user),
):
    """返回所有模板的默认文本（前端 "恢复默认" 按钮使用）。"""
    return {"defaults": MessageTemplateService.get_defaults()}


@router.get("/templates/placeholders")
def get_template_placeholders(
    _: User = Depends(get_current_user),
):
    """返回所有可用的占位符及其说明，供前端展示。"""
    return {"placeholders": MessageTemplateService.get_placeholder_help()}


# ==============================================================
#  邮件设置
# ==============================================================
@router.get("/email", response_model=SettingsResponse)
def get_email_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_or_create_settings(db, current_user.id)


@router.put("/email", response_model=SettingsResponse)
def update_email_settings(
    data: EmailSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    settings = _get_or_create_settings(db, current_user.id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(settings, key, value)
    db.commit()
    db.refresh(settings)
    return settings


@router.post("/test-email")
def test_email(
    data: TestEmailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发送测试邮件，使用 settings 中保存的"签到成功"邮件模板渲染。"""
    try:
        from services.message_template import MessageTemplateService
        settings = _get_or_create_settings(db, current_user.id)

        # 用模板渲染一个示例成功邮件
        sample_context = {
            "account_name": "测试账号",
            "site_name": "测试站点",
            "message": "这是一封来自自动签到系统的测试邮件",
            "user_email": current_user.email,
            "display_name": getattr(settings, "display_name", ""),
        }
        subject = MessageTemplateService.render(
            settings.tpl_email_success_subject or "[测试] 自动签到系统",
            sample_context,
        )
        body = MessageTemplateService.render(
            settings.tpl_email_success_body or "测试邮件",
            sample_context,
        )

        message = MIMEMultipart()
        message["From"] = data.email_from or data.smtp_user or "test@example.com"
        message["To"] = current_user.email
        message["Subject"] = f"[测试] {subject}"
        message.attach(MIMEText(body, "plain", "utf-8"))

        import aiosmtplib
        async def _send():
            await aiosmtplib.send(
                message,
                hostname=data.smtp_host,
                port=data.smtp_port,
                username=data.smtp_user,
                password=data.smtp_password,
                start_tls=True,
                timeout=30,
            )
        asyncio.run(_send())
        return {"success": True, "message": "测试邮件已发送，请查收"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"发送失败: {e}")


# ==============================================================
#  企业微信机器人
# ==============================================================
@router.get("/wechat-bot", response_model=SettingsResponse)
def get_wechat_bot_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_or_create_settings(db, current_user.id)


@router.put("/wechat-bot", response_model=SettingsResponse)
def update_wechat_bot_settings(
    data: WechatBotSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    settings = _get_or_create_settings(db, current_user.id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(settings, key, value)
    db.commit()
    db.refresh(settings)
    return settings


@router.post("/test-wechat-bot")
def test_wechat_bot(
    data: TestWechatBotRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发送测试微信机器人消息。使用保存的"签到成功"机器人模板进行渲染。"""
    try:
        from services.wechat_bot import WechatBotService
        from services.message_template import MessageTemplateService

        settings = _get_or_create_settings(db, current_user.id)

        sample_context = {
            "account_name": "测试账号",
            "site_name": "测试站点",
            "message": "这是一条来自自动签到助手的测试消息",
            "user_email": current_user.email,
            "display_name": getattr(settings, "display_name", ""),
        }
        rendered = MessageTemplateService.render(
            settings.tpl_bot_success or MessageTemplateService.get_defaults()["bot_success"],
            sample_context,
        )

        bot = WechatBotService(webhook_url=data.webhook_url)
        result = bot.send_markdown(rendered)
        if result.get("success"):
            return {"success": True, "message": "测试消息已发送，请查看企业微信群"}
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error", "发送失败"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"发送失败: {e}")


# ==============================================================
#  其他
# ==============================================================
@router.post("/change-password")
def change_password(
    data: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(data.old_password, current_user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="原密码不正确")
    if len(data.new_password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="新密码至少 6 位")
    current_user.password = get_password_hash(data.new_password)
    db.commit()
    return {"success": True, "message": "密码修改成功"}
