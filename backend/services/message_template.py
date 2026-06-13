"""
消息模板服务 - MessageTemplateService

负责：
1. 构建上下文变量（账号、站点、时间、统计等）
2. 渲染模板文本（替换占位符）
3. 提供默认模板字典，供前端 "恢复默认" 使用
4. 提供模板预览接口所需的 helper

支持的占位符变量：
    {account_name}      - 账号用户名（如 testuser）
    {username}          - 同 account_name
    {site_name}         - 站点名称（如 "GitHub"）
    {site_display_name} - 站点显示名（如 "GitHub 仓库"）
    {site_category}     - 站点分类（如 "资源下载"）
    {message}           - 签到成功消息（来自插件返回）
    {error}             - 错误信息（失败场景）
    {result}            - 原始结果 JSON 文本
    {time}              - 执行时间（YYYY-MM-DD HH:MM:SS）
    {date}              - 执行日期（YYYY-MM-DD）
    {user_email}        - 用户邮箱
    {display_name}      - 个性化显示名（可在设置中修改）
    {success_count}     - 今日成功签到次数
    {fail_count}        - 今日失败签到次数
    {total_count}       - 今日总签到次数
    {success_rate}      - 成功率百分比
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Dict, Optional, Any
from sqlalchemy.orm import Session

from core.utils import to_tz_str
from models.settings import UserSettings
from models.log import Log
from models.account import Account
from models.site import Site


# ============================================================
#  默认模板字典 —— 供前端 "恢复默认" 按钮使用
# ============================================================

DEFAULT_TEMPLATES: Dict[str, str] = {
    # ---- 邮件 ----
    "email_success_subject": "[签到成功] {account_name} @ {site_name}",
    "email_success_body": (
        "您好，\n\n签到任务已顺利完成。\n\n"
        "【账号】{account_name}\n【站点】{site_name}\n"
        "【结果】{message}\n【时间】{time}\n\n"
        "-- \n自动签到系统 {display_name}"
    ),
    "email_failure_subject": "[签到失败] {account_name} @ {site_name}",
    "email_failure_body": (
        "您好，\n\n以下是签到失败的详细信息：\n\n"
        "【账号】{account_name}\n【站点】{site_name}\n"
        "【错误信息】{error}\n【时间】{time}\n\n"
        "建议：\n1. 检查账号/密码是否过期\n"
        "2. 查看签到日志了解最近情况\n"
        "3. 如果是 API 站点，检查接口是否可用\n\n"
        "--\n自动签到系统 {display_name}"
    ),
    "email_stable_subject": "[稳定运行报告] 今日成功 {success_count} 次",
    "email_stable_body": (
        "您好，\n\n这是一份自动签到系统稳定运行报告：\n\n"
        "【日期】{date}\n"
        "【今日签到次数】{success_count} 次成功，{fail_count} 次失败\n"
        "【成功率】{success_rate}%\n【状态】✅ 系统运行正常\n"
        "--\n自动签到系统 {display_name}"
    ),
    "email_error_subject": "[系统异常告警]",
    "email_error_body": (
        "⚠️ 系统异常告警\n\n【时间】{time}\n【错误】{error}\n\n"
        "建议：\n1. 检查系统日志了解详细情况\n"
        "2. 如持续异常请检查配置是否正确\n\n"
        "--\n自动签到系统 {display_name}"
    ),
    # ---- 企业微信机器人 ----
    "bot_success": (
        "## ✅ 签到成功\n\n> **时间**: {time}\n\n"
        "**账号信息**\n- 账号: `{account_name}`\n- 站点: `{site_name}`\n"
        "- 状态: **成功**\n\n**结果详情**\n```\n{message}\n```\n\n"
        "---\n> 来自 全自动签到助手 {display_name}"
    ),
    "bot_failure": (
        "## ❌ 签到失败\n\n> **时间**: {time}\n\n"
        "**账号信息**\n- 账号: `{account_name}`\n- 站点: `{site_name}`\n"
        "- 状态: **失败**\n\n**错误详情**\n```\n{error}\n```\n\n"
        "---\n> 来自 全自动签到助手 {display_name}"
    ),
    "bot_stable": (
        "## 📊 稳定运行报告\n\n> **日期**: {date}\n\n"
        "**今日统计**\n- 成功签到: **{success_count}** 次\n"
        "- 失败签到: **{fail_count}** 次\n- 成功率: **{success_rate}%**\n\n"
        "状态: ✅ 系统运行正常\n\n---\n> 来自 全自动签到助手 {display_name}"
    ),
    "bot_error": (
        "## ⚠️ 系统异常告警\n\n> **时间**: {time}\n\n"
        "**错误信息**\n```\n{error}\n```\n\n"
        "**建议处理步骤**\n1. 查看系统日志了解详细情况\n"
        "2. 如持续异常请检查配置是否正确\n\n"
        "---\n> 来自 全自动签到助手 {display_name}"
    ),
}

# 供前端显示给用户的"可使用变量"说明
PLACEHOLDER_HELP: Dict[str, str] = {
    "{account_name}": "账号用户名",
    "{username}": "账号用户名（同 account_name）",
    "{site_name}": "站点名称",
    "{site_display_name}": "站点显示名称",
    "{site_category}": "站点分类",
    "{message}": "签到成功消息内容",
    "{error}": "错误信息（失败场景）",
    "{result}": "原始结果 JSON",
    "{time}": "执行时间 (YYYY-MM-DD HH:MM:SS)",
    "{date}": "执行日期 (YYYY-MM-DD)",
    "{user_email}": "用户邮箱",
    "{display_name}": "个性化显示名",
    "{success_count}": "今日成功次数",
    "{fail_count}": "今日失败次数",
    "{total_count}": "今日总次数",
    "{success_rate}": "成功率 (%)",
}


# ============================================================
#  核心类
# ============================================================

class MessageTemplateService:
    """消息模板渲染服务。"""

    @staticmethod
    def build_context(
        account: Optional[Account] = None,
        site: Optional[Site] = None,
        user: Optional[Any] = None,
        settings: Optional[UserSettings] = None,
        result: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """构建渲染上下文。

        对于场景中不存在的信息（如没有 account，就没有 account_name），
        会以空字符串替代，防止 template 里出现 ``{account_name}`` 原样残留。
        """

        now = datetime.utcnow()
        tz_name = getattr(settings, "timezone", "") or "Asia/Shanghai"
        ctx: Dict[str, str] = {
            "time": to_tz_str(now, tz_name),
            "date": to_tz_str(now, tz_name, "%Y-%m-%d"),
            "display_name": getattr(settings, "display_name", "") or "",
            "user_email": getattr(user, "email", "") if user else "",
            "message": (result or {}).get("message", "") or "",
            "error": (result or {}).get("error", "") or "",
            "result": json.dumps(result or {}, ensure_ascii=False, indent=2),
            "account_name": getattr(account, "username", "") or "",
            "username": getattr(account, "username", "") or "",
            "site_name": getattr(site, "name", "") or "",
            "site_display_name": (
                getattr(site, "display_name", "") or getattr(site, "name", "") or ""
            ),
            "site_category": getattr(site, "category", "") or "其他",
        }

        # 统计信息 - 如提供了 db 则查询今日日志
        success_count, fail_count = 0, 0
        if db is not None and user is not None:
            try:
                from models.task import Task
                today_start = now.strftime("%Y-%m-%d") + " 00:00:00"
                today_logs = (
                    db.query(Log)
                    .join(Task)
                    .join(Account)
                    .filter(Account.user_id == user.id)
                    .filter(Log.created_at >= today_start)
                    .all()
                )
                for log in today_logs:
                    if log.status == "success":
                        success_count += 1
                    elif log.status == "failed" or log.status == "failure":
                        fail_count += 1
                    else:
                        # 兼容其他可能的值
                        pass
            except Exception:
                success_count, fail_count = 0, 0

        total = success_count + fail_count
        rate = round(success_count / total * 100, 1) if total else 0.0

        ctx.update({
            "success_count": str(success_count),
            "fail_count": str(fail_count),
            "total_count": str(total),
            "success_rate": f"{rate:g}",
        })

        if extra:
            # 允许调用方覆盖 / 追加变量
            for k, v in extra.items():
                ctx[k] = str(v) if v is not None else ""

        return ctx

    @staticmethod
    def render(template: str, context: Dict[str, str]) -> str:
        """用 str.format_map 渲染模板，缺失的变量保持空字符串。"""
        if not template:
            return ""
        try:
            return template.format_map(context)
        except (KeyError, IndexError, ValueError):
            # 若模板里包含了未识别的格式占位符（如 {}），fallback 为简单替换
            result = template
            for key, value in context.items():
                result = result.replace("{" + key + "}", str(value))
            return result

    @staticmethod
    def render_signin_email(
        settings: UserSettings,
        is_success: bool,
        account: Optional[Account],
        site: Optional[Site],
        user: Optional[Any],
        result: Optional[Dict[str, Any]],
        db: Optional[Session] = None,
    ) -> Dict[str, str]:
        """返回渲染后的邮件 {subject, body}。"""
        if is_success:
            tpl_subject = settings.tpl_email_success_subject or DEFAULT_TEMPLATES["email_success_subject"]
            tpl_body = settings.tpl_email_success_body or DEFAULT_TEMPLATES["email_success_body"]
        else:
            tpl_subject = settings.tpl_email_failure_subject or DEFAULT_TEMPLATES["email_failure_subject"]
            tpl_body = settings.tpl_email_failure_body or DEFAULT_TEMPLATES["email_failure_body"]

        context = MessageTemplateService.build_context(
            account=account, site=site, user=user, settings=settings,
            result=result, db=db,
        )
        return {
            "subject": MessageTemplateService.render(tpl_subject, context),
            "body": MessageTemplateService.render(tpl_body, context),
        }

    @staticmethod
    def render_stable_email(
        settings: UserSettings,
        user: Optional[Any],
        db: Optional[Session] = None,
    ) -> Dict[str, str]:
        tpl_subject = settings.tpl_email_stable_subject or DEFAULT_TEMPLATES["email_stable_subject"]
        tpl_body = settings.tpl_email_stable_body or DEFAULT_TEMPLATES["email_stable_body"]
        context = MessageTemplateService.build_context(
            user=user, settings=settings, db=db,
        )
        return {
            "subject": MessageTemplateService.render(tpl_subject, context),
            "body": MessageTemplateService.render(tpl_body, context),
        }

    @staticmethod
    def render_system_error_email(
        settings: UserSettings,
        user: Optional[Any],
        error_message: str,
    ) -> Dict[str, str]:
        tpl_subject = settings.tpl_email_error_subject or DEFAULT_TEMPLATES["email_error_subject"]
        tpl_body = settings.tpl_email_error_body or DEFAULT_TEMPLATES["email_error_body"]
        context = MessageTemplateService.build_context(
            user=user, settings=settings,
            result={"error": error_message},
        )
        return {
            "subject": MessageTemplateService.render(tpl_subject, context),
            "body": MessageTemplateService.render(tpl_body, context),
        }

    # ---- 企业微信 ----
    @staticmethod
    def render_signin_bot(
        settings: UserSettings,
        is_success: bool,
        account: Optional[Account],
        site: Optional[Site],
        user: Optional[Any],
        result: Optional[Dict[str, Any]],
        db: Optional[Session] = None,
    ) -> str:
        if is_success:
            tpl = settings.tpl_bot_success or DEFAULT_TEMPLATES["bot_success"]
        else:
            tpl = settings.tpl_bot_failure or DEFAULT_TEMPLATES["bot_failure"]
        context = MessageTemplateService.build_context(
            account=account, site=site, user=user, settings=settings,
            result=result, db=db,
        )
        return MessageTemplateService.render(tpl, context)

    @staticmethod
    def render_stable_bot(settings: UserSettings, user: Optional[Any], db: Optional[Session] = None) -> str:
        tpl = settings.tpl_bot_stable or DEFAULT_TEMPLATES["bot_stable"]
        context = MessageTemplateService.build_context(user=user, settings=settings, db=db)
        return MessageTemplateService.render(tpl, context)

    @staticmethod
    def render_system_error_bot(settings: UserSettings, user: Optional[Any], error_message: str) -> str:
        tpl = settings.tpl_bot_error or DEFAULT_TEMPLATES["bot_error"]
        context = MessageTemplateService.build_context(
            user=user, settings=settings, result={"error": error_message}
        )
        return MessageTemplateService.render(tpl, context)

    @staticmethod
    def get_defaults() -> Dict[str, str]:
        """返回所有默认模板（供前端恢复默认按钮调用）。"""
        return dict(DEFAULT_TEMPLATES)

    @staticmethod
    def get_placeholder_help() -> Dict[str, str]:
        """返回所有可用占位符的说明字典。"""
        return dict(PLACEHOLDER_HELP)
