"""
企业微信机器人通知服务 - WechatBotService

使用 MessageTemplateService 渲染用户自定义的模板。
支持 markdown 格式消息。
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from core.utils import to_tz_str


class WechatBotService:
    def __init__(self, webhook_url: str = ""):
        self.webhook_url = webhook_url

    def configure(self, webhook_url: str):
        self.webhook_url = webhook_url

    # -------- 内部 --------
    def _send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.webhook_url:
            return {"success": False, "error": "未配置企业微信 webhook 地址"}
        try:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                raw = response.read().decode("utf-8", errors="ignore")
                try:
                    resp_json = json.loads(raw)
                    if resp_json.get("errcode") == 0:
                        return {"success": True, "message": "发送成功"}
                    return {
                        "success": False,
                        "error": f"企业微信返回错误: {resp_json.get('errmsg', '未知错误')}",
                    }
                except (json.JSONDecodeError, TypeError):
                    return {"success": False, "error": f"解析响应失败: {raw[:200]}"}
        except urllib.error.HTTPError as e:
            return {"success": False, "error": f"HTTP {e.code}: {e.reason}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_text(self, content: str, mentioned_list: list = None,
                  mentioned_mobile_list: list = None) -> Dict[str, Any]:
        payload = {
            "msgtype": "text",
            "text": {
                "content": content,
                "mentioned_list": mentioned_list or [],
                "mentioned_mobile_list": mentioned_mobile_list or [],
            },
        }
        return self._send(payload)

    def send_markdown(self, content: str) -> Dict[str, Any]:
        payload = {"msgtype": "markdown", "markdown": {"content": content}}
        return self._send(payload)

    # -------- 对外: 签到相关 --------
    def send_signin_notification_sync(
        self,
        is_success: bool,
        settings: Any,
        account: Any = None,
        site: Any = None,
        user: Any = None,
        result: Optional[Dict[str, Any]] = None,
        db: Any = None,
    ) -> Dict[str, Any]:
        """同步版本 — 在无法 await 的地方使用。"""
        from services.message_template import MessageTemplateService
        content = MessageTemplateService.render_signin_bot(
            settings=settings, is_success=is_success,
            account=account, site=site, user=user, result=result, db=db,
        )
        return self.send_markdown(content)

    async def send_signin_notification(
        self,
        account_name: str = "",
        site_name: str = "",
        success: bool = True,
        message: str = "",
        error: str = "",
        extra_info: str = "",
        # 可选：若提供 settings/user/account/site/db 则改用自定义模板
        settings: Any = None,
        account: Any = None,
        site: Any = None,
        user: Any = None,
        result: Optional[Dict[str, Any]] = None,
        db: Any = None,
    ) -> Dict[str, Any]:
        """发送签到结果通知。

        如果传入了 ``settings`` 等参数，则使用用户自定义模板；
        否则降级使用基于参数的简单模板，保持向后兼容。
        """
        if settings is not None:
            from services.message_template import MessageTemplateService
            if result is None:
                result = {"message": message, "error": error}
            content = MessageTemplateService.render_signin_bot(
                settings=settings, is_success=success,
                account=account, site=site, user=user, result=result, db=db,
            )
            return self.send_markdown(content)

        # ---- 降级 / 兼容版本 ----
        tz_name = getattr(settings, "timezone", "") or "Asia/Shanghai" if settings else "Asia/Shanghai"
        now = to_tz_str(datetime.now(timezone.utc), tz_name)
        if success:
            title = "✅ 签到成功"
            status_text = "成功"
            detail = message or "签到完成"
        else:
            title = "❌ 签到失败"
            status_text = "失败"
            detail = error or message or "未知错误"

        md_content = (
            f"## {title}\n\n> **时间**: {now}\n\n"
            f"**账号信息**\n- 账号: `{account_name}`\n"
            f"- 站点: `{site_name}`\n- 状态: **{status_text}**\n\n"
            f"**结果详情**\n```\n{detail}\n```\n"
        )
        if extra_info:
            md_content += f"\n**附加信息**\n```\n{extra_info}\n```"
        md_content += "\n\n---\n> 来自 全自动签到助手"
        return self.send_markdown(md_content)

    async def send_stable_report(
        self, settings: Any, user: Any = None, db: Any = None,
    ) -> Dict[str, Any]:
        from services.message_template import MessageTemplateService
        content = MessageTemplateService.render_stable_bot(
            settings=settings, user=user, db=db,
        )
        return self.send_markdown(content)

    async def send_system_error(
        self, settings: Any, error_message: str, user: Any = None,
    ) -> Dict[str, Any]:
        from services.message_template import MessageTemplateService
        content = MessageTemplateService.render_system_error_bot(
            settings=settings, user=user, error_message=error_message,
        )
        return self.send_markdown(content)

    async def send_test_message(self) -> Dict[str, Any]:
        return self.send_text(
            "🤖 全自动签到助手测试消息\n\n如果您收到此消息，说明企业微信机器人配置正确！"
        )
