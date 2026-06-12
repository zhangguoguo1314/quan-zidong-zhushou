from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text
from sqlalchemy.sql import func
from core.database import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)

    email_enabled = Column(Boolean, default=False)
    notify_on_success = Column(Boolean, default=False)
    notify_on_failure = Column(Boolean, default=True)
    notify_on_stable = Column(Boolean, default=False)
    notify_on_system_error = Column(Boolean, default=True)

    smtp_host = Column(String(200))
    smtp_port = Column(Integer, default=587)
    smtp_user = Column(String(200))
    smtp_password = Column(String(200))
    email_from = Column(String(200))

    wechat_bot_enabled = Column(Boolean, default=False)
    wechat_bot_webhook = Column(String(500))
    wechat_bot_notify_on_success = Column(Boolean, default=False)
    wechat_bot_notify_on_failure = Column(Boolean, default=True)
    wechat_bot_notify_on_stable = Column(Boolean, default=False)
    wechat_bot_notify_on_system_error = Column(Boolean, default=True)

    display_name = Column(String(100), default="")
    timezone = Column(String(50), default="Asia/Shanghai")
    language = Column(String(20), default="zh-CN")

    # --- AI 配置（第三方 LLM API） ---
    ai_api_url = Column(String(500), default="")
    ai_api_key = Column(String(500), default="")
    ai_model = Column(String(200), default="")
    ai_custom_prompt = Column(Text, default="")

    extra = Column(JSON, nullable=True)

    # --- 定时状态报告 ---
    status_report_enabled = Column(Boolean, default=False)
    status_report_interval = Column(Integer, default=0)  # 0=关闭, 单位分钟
    status_report_last_sent = Column(String(50), default="")

    tpl_email_success_subject = Column(String(200), default="[签到成功] {account_name} @ {site_name}")
    tpl_email_success_body = Column(String(5000), default="您好，\n\n签到任务已顺利完成。\n\n【账号】{account_name}\n【站点】{site_name}\n【结果】{message}\n【时间】{time}\n\n--\n自动签到系统 {display_name}")

    tpl_email_failure_subject = Column(String(200), default="[签到失败] {account_name} @ {site_name}")
    tpl_email_failure_body = Column(String(5000), default="您好，\n\n以下是签到失败的详细信息：\n\n【账号】{account_name}\n【站点】{site_name}\n【错误信息】{error}\n【时间】{time}\n\n建议：\n1. 检查账号/密码是否过期\n2. 查看签到日志了解最近情况\n3. 如果是 API 站点，检查接口是否可用\n\n--\n自动签到系统 {display_name}")

    tpl_email_stable_subject = Column(String(200), default="[稳定运行报告] 今日成功 {success_count} 次")
    tpl_email_stable_body = Column(String(5000), default="您好，\n\n这是一份自动签到系统稳定运行报告：\n\n【日期】{date}\n【今日签到次数】{success_count} 次成功，{fail_count} 次失败\n【成功率】{success_rate}%\n【状态】✅ 系统运行正常\n--\n自动签到系统 {display_name}")

    tpl_email_error_subject = Column(String(200), default="[系统异常告警]")
    tpl_email_error_body = Column(String(5000), default="⚠️ 系统异常告警\n\n【时间】{time}\n【错误】{error}\n\n建议：\n1. 检查系统日志了解详细情况\n2. 如持续异常请检查配置是否正确\n\n--\n自动签到系统 {display_name}")

    tpl_bot_success = Column(String(5000), default="## ✅ 签到成功\n\n> **时间**: {time}\n\n**账号信息**\n- 账号: `{account_name}`\n- 站点: `{site_name}`\n- 状态: **成功**\n\n**结果详情**\n```\n{message}\n```\n\n---\n> 来自 全自动签到助手 {display_name}")
    tpl_bot_failure = Column(String(5000), default="## ❌ 签到失败\n\n> **时间**: {time}\n\n**账号信息**\n- 账号: `{account_name}`\n- 站点: `{site_name}`\n- 状态: **失败**\n\n**错误详情**\n```\n{error}\n```\n\n---\n> 来自 全自动签到助手 {display_name}")
    tpl_bot_stable = Column(String(5000), default="## 📊 稳定运行报告\n\n> **日期**: {date}\n\n**今日统计**\n- 成功签到: **{success_count}** 次\n- 失败签到: **{fail_count}** 次\n- 成功率: **{success_rate}%**\n\n状态: ✅ 系统运行正常\n\n---\n> 来自 全自动签到助手 {display_name}")
    tpl_bot_error = Column(String(5000), default="## ⚠️ 系统异常告警\n\n> **时间**: {time}\n\n**错误信息**\n```\n{error}\n```\n\n**建议处理步骤**\n1. 查看系统日志了解详细情况\n2. 如持续异常请检查配置是否正确\n\n---\n> 来自 全自动签到助手 {display_name}")

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
