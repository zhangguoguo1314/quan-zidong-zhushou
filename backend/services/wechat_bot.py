import json
import urllib.request
import urllib.error
from typing import Dict, Any


class WechatBotService:
    """企业微信机器人通知服务

    用户填入企业微信机器人的 webhook 地址，即可自动发送签到通知。
    支持的消息类型：文本消息（text）、markdown 消息（markdown）。
    """

    def __init__(self, webhook_url: str = ""):
        self.webhook_url = webhook_url

    def configure(self, webhook_url: str):
        self.webhook_url = webhook_url

    def _send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.webhook_url:
            return {"success": False, "error": "未配置企业微信 webhook 地址"}

        try:
            data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                raw = response.read().decode('utf-8', errors='ignore')
                try:
                    resp_json = json.loads(raw)
                    if resp_json.get("errcode") == 0:
                        return {"success": True, "message": "发送成功"}
                    return {"success": False, "error": f"企业微信返回错误: {resp_json.get('errmsg', '未知错误')}"}
                except (json.JSONDecodeError, TypeError):
                    return {"success": False, "error": f"解析响应失败: {raw[:200]}"}
        except urllib.error.HTTPError as e:
            return {"success": False, "error": f"HTTP {e.code}: {e.reason}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_text(self, content: str, mentioned_list: list = None, mentioned_mobile_list: list = None) -> Dict[str, Any]:
        """发送纯文本消息"""
        payload = {
            "msgtype": "text",
            "text": {
                "content": content,
                "mentioned_list": mentioned_list or [],
                "mentioned_mobile_list": mentioned_mobile_list or []
            }
        }
        return self._send(payload)

    def send_markdown(self, content: str) -> Dict[str, Any]:
        """发送 markdown 消息（支持格式更丰富）"""
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }
        return self._send(payload)

    async def send_signin_notification(self, account_name: str, site_name: str, success: bool, message: str = "", error: str = "", extra_info: str = "") -> Dict[str, Any]:
        """发送签到结果通知（markdown 格式，信息丰富）"""
        import datetime
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if success:
            title = "✅ 签到成功"
            color = "info"
            status_text = "成功"
            detail = message or "签到完成"
        else:
            title = "❌ 签到失败"
            color = "warning"
            status_text = "失败"
            detail = error or message or "未知错误"

        md_content = f"""## {title}

> **时间**: {now}

**账号信息**
- 账号: `{account_name}`
- 站点: `{site_name}`
- 状态: **{status_text}**

**结果详情**
```
{detail}
```
"""
        if extra_info:
            md_content += f"\n**附加信息**\n```\n{extra_info}\n```"

        md_content += "\n\n---\n> 来自 全自动签到助手"

        return self.send_markdown(md_content)

    async def send_test_message(self) -> Dict[str, Any]:
        """发送测试消息"""
        return self.send_text("🤖 全自动签到助手测试消息\n\n如果您收到此消息，说明企业微信机器人配置正确！")
