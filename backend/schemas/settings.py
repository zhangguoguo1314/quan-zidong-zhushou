"""
设置相关的 Pydantic Schemas。

新增字段：
- 邮件通知开关：notify_on_stable, notify_on_system_error
- 微信机器人通知开关：wechat_bot_notify_on_stable, wechat_bot_notify_on_system_error
- 8 个消息模板字段（见下方注释）
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class SettingsBase(BaseModel):
    """设置基础字段（含所有模板）。"""

    # --- 邮件通知开关 ---
    email_enabled: bool = False
    notify_on_success: bool = False
    notify_on_failure: bool = True
    notify_on_stable: bool = False
    notify_on_system_error: bool = True

    # --- SMTP 配置 ---
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None

    # --- 企业微信机器人 ---
    wechat_bot_enabled: bool = False
    wechat_bot_webhook: Optional[str] = None
    wechat_bot_notify_on_success: bool = False
    wechat_bot_notify_on_failure: bool = True
    wechat_bot_notify_on_stable: bool = False
    wechat_bot_notify_on_system_error: bool = True

    # --- 个性化 ---
    display_name: str = ""
    timezone: str = "Asia/Shanghai"
    language: str = "zh-CN"
    extra: Optional[Dict[str, Any]] = None

    # --- AI 配置（第三方 LLM API） ---
    ai_api_url: str = ""
    ai_api_key: str = ""
    ai_model: str = ""
    ai_custom_prompt: str = ""

    # --- 定时状态报告 ---
    status_report_enabled: bool = False
    status_report_interval: int = 0  # 0=关闭, 单位分钟
    status_report_last_sent: str = ""

    # --- 邮件模板 ---
    tpl_email_success_subject: str = "[签到成功] {account_name} @ {site_name}"
    tpl_email_success_body: str = (
        "您好，\n\n签到任务已顺利完成。\n\n"
        "【账号】{account_name}\n【站点】{site_name}\n"
        "【结果】{message}\n【时间】{time}\n\n"
        "-- \n自动签到系统 {display_name}"
    )
    tpl_email_failure_subject: str = "[签到失败] {account_name} @ {site_name}"
    tpl_email_failure_body: str = (
        "您好，\n\n以下是签到失败的详细信息：\n\n"
        "【账号】{account_name}\n【站点】{site_name}\n"
        "【错误信息】{error}\n【时间】{time}\n\n"
        "建议：\n1. 检查账号/密码是否过期\n"
        "2. 查看签到日志了解最近情况\n"
        "3. 如果是 API 站点，检查接口是否可用\n\n"
        "--\n自动签到系统 {display_name}"
    )
    tpl_email_stable_subject: str = "[稳定运行报告] 今日成功 {success_count} 次"
    tpl_email_stable_body: str = (
        "您好，\n\n这是一份自动签到系统稳定运行报告：\n\n"
        "【日期】{date}\n"
        "【今日签到次数】{success_count} 次成功，{fail_count} 次失败\n"
        "【成功率】{success_rate}%\n【状态】✅ 系统运行正常\n"
        "--\n自动签到系统 {display_name}"
    )
    tpl_email_error_subject: str = "[系统异常告警]"
    tpl_email_error_body: str = (
        "⚠️ 系统异常告警\n\n【时间】{time}\n【错误】{error}\n\n"
        "建议：\n1. 检查系统日志了解详细情况\n"
        "2. 如持续异常请检查配置是否正确\n\n"
        "--\n自动签到系统 {display_name}"
    )

    # --- 企业微信机器人模板 ---
    tpl_bot_success: str = (
        "## ✅ 签到成功\n\n> **时间**: {time}\n\n"
        "**账号信息**\n- 账号: `{account_name}`\n- 站点: `{site_name}`\n"
        "- 状态: **成功**\n\n**结果详情**\n```\n{message}\n```\n\n"
        "---\n> 来自 全自动签到助手 {display_name}"
    )
    tpl_bot_failure: str = (
        "## ❌ 签到失败\n\n> **时间**: {time}\n\n"
        "**账号信息**\n- 账号: `{account_name}`\n- 站点: `{site_name}`\n"
        "- 状态: **失败**\n\n**错误详情**\n```\n{error}\n```\n\n"
        "---\n> 来自 全自动签到助手 {display_name}"
    )
    tpl_bot_stable: str = (
        "## 📊 稳定运行报告\n\n> **日期**: {date}\n\n"
        "**今日统计**\n- 成功签到: **{success_count}** 次\n"
        "- 失败签到: **{fail_count}** 次\n- 成功率: **{success_rate}%**\n\n"
        "状态: ✅ 系统运行正常\n\n---\n> 来自 全自动签到助手 {display_name}"
    )
    tpl_bot_error: str = (
        "## ⚠️ 系统异常告警\n\n> **时间**: {time}\n\n"
        "**错误信息**\n```\n{error}\n```\n\n"
        "**建议处理步骤**\n1. 查看系统日志了解详细情况\n"
        "2. 如持续异常请检查配置是否正确\n\n"
        "---\n> 来自 全自动签到助手 {display_name}"
    )


class SettingsUpdate(SettingsBase):
    """提交的设置更新。"""
    pass


class SettingsResponse(SettingsBase):
    id: int
    user_id: int
    updated_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# ---- 兼容老代码 ----
class EmailSettingsUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    notify_on_success: Optional[bool] = None
    notify_on_failure: Optional[bool] = None
    notify_on_stable: Optional[bool] = None
    notify_on_system_error: Optional[bool] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None


class WechatBotSettingsUpdate(BaseModel):
    wechat_bot_enabled: Optional[bool] = None
    wechat_bot_webhook: Optional[str] = None
    wechat_bot_notify_on_success: Optional[bool] = None
    wechat_bot_notify_on_failure: Optional[bool] = None
    wechat_bot_notify_on_stable: Optional[bool] = None
    wechat_bot_notify_on_system_error: Optional[bool] = None


class TestEmailRequest(BaseModel):
    smtp_host: str
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None


class TestWechatBotRequest(BaseModel):
    webhook_url: str


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str


# ---- 模板预览相关 ----
class TemplatePreviewRequest(BaseModel):
    """模板预览请求。

    - template: 要预览的模板文本
    - scenario: 场景（success / failure / stable / error），决定预置哪些变量
    - custom_context: 可选，覆盖默认变量
    """

    template: str
    scenario: str = "success"
    custom_context: Optional[Dict[str, str]] = None


class ResetTemplatesRequest(BaseModel):
    """仅重置模板部分字段。"""
    targets: Optional[list] = None  # 如 ["email_success_subject", "bot_failure"]
