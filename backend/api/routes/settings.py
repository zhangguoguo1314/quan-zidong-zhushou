import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import verify_password, get_password_hash
from models.settings import UserSettings
from models.user import User
from schemas.settings import (
    SettingsUpdate, SettingsResponse, EmailSettingsUpdate,
    WechatBotSettingsUpdate, TestEmailRequest, TestWechatBotRequest, PasswordChangeRequest
)
from api.deps import get_current_user

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _get_or_create_settings(db: Session, user_id: int) -> UserSettings:
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if not settings:
        settings = UserSettings(user_id=user_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.get("", response_model=SettingsResponse)
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return _get_or_create_settings(db, current_user.id)


@router.put("", response_model=SettingsResponse)
def update_settings(
    data: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    settings = _get_or_create_settings(db, current_user.id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(settings, key, value)
    db.commit()
    db.refresh(settings)
    return settings


@router.get("/email", response_model=SettingsResponse)
def get_email_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return _get_or_create_settings(db, current_user.id)


@router.put("/email", response_model=SettingsResponse)
def update_email_settings(
    data: EmailSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
    current_user: User = Depends(get_current_user)
):
    try:
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        message = MIMEMultipart()
        message["From"] = data.email_from or data.smtp_user or "test@example.com"
        message["To"] = current_user.email
        message["Subject"] = "🔔 自动签到系统 - 测试邮件"
        message.attach(MIMEText(f"您好，\n\n这是一封来自自动签到系统的测试邮件。\n如果您收到此邮件，说明 SMTP 配置正确。\n\n时间: {asyncio.get_event_loop().time()}", "plain", "utf-8"))

        import aiosmtplib
        async def _send():
            await aiosmtplib.send(
                message,
                hostname=data.smtp_host,
                port=data.smtp_port,
                username=data.smtp_user,
                password=data.smtp_password,
                start_tls=True,
                timeout=30
            )
        asyncio.run(_send())
        return {"success": True, "message": "测试邮件已发送，请查收"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"发送失败: {str(e)}")


# ============ 企业微信机器人 ============

@router.get("/wechat-bot", response_model=SettingsResponse)
def get_wechat_bot_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return _get_or_create_settings(db, current_user.id)


@router.put("/wechat-bot", response_model=SettingsResponse)
def update_wechat_bot_settings(
    data: WechatBotSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
    current_user: User = Depends(get_current_user)
):
    try:
        from services.wechat_bot import WechatBotService
        bot = WechatBotService(webhook_url=data.webhook_url)
        result = bot.send_text("🤖 全自动签到助手测试消息\n\n如果您收到此消息，说明企业微信机器人配置正确！")
        if result.get("success"):
            return {"success": True, "message": "测试消息已发送，请查看企业微信群"}
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error", "发送失败"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"发送失败: {str(e)}")


@router.post("/change-password")
def change_password(
    data: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not verify_password(data.old_password, current_user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="原密码不正确")
    if len(data.new_password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="新密码至少 6 位")
    current_user.password = get_password_hash(data.new_password)
    db.commit()
    return {"success": True, "message": "密码修改成功"}
