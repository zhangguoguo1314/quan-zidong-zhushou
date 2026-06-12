import httpx
import json
import asyncio
from typing import Dict, Any, Optional


async def execute_signin(
    site_type: str,
    site_url: str,
    account_username: str,
    account_password: str,
    account_token: Optional[str],
    account_cookie: Optional[str],
    api_config: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    通用签到执行器
    支持的 api_config 格式：
    {
        "login_url": "https://xxx/api/login",
        "login_method": "POST",
        "login_body": {"username": "{username}", "password": "{password}"},
        "login_headers": {"Content-Type": "application/json"},
        "token_field": "data.token",  # 从登录响应中提取 token 的 JSONPath
        "signin_url": "https://xxx/api/checkin",
        "signin_method": "POST",
        "signin_headers": {"Authorization": "Bearer {token}"},
        "signin_body": {},
        "success_check": "success",  # 检查响应中是否包含此字段/值
    }
    同时兼容 SITE_PRESETS 中的模板格式（使用 {{username}} 占位符）。
    """
    result = {"success": False, "error": ""}

    try:
        config = api_config or {}

        # Step 1: 登录获取 token（如果配置了 login_url）
        token = account_token or ""
        login_url = config.get("login_url", "").strip()

        if login_url:
            login_method = config.get("login_method", "POST").upper()

            # 兼容两种模板格式：{username} 和 {{username}}
            login_body_template = config.get("login_body") or config.get("login_body_template", "{}")
            login_headers = config.get("login_headers", {"Content-Type": "application/json"})

            # 如果 login_headers 是简单字符串，转为 dict
            if isinstance(login_headers, str):
                ct = config.get("login_content_type", "application/json")
                login_headers = {"Content-Type": ct}

            # 替换模板变量（兼容 {{}} 和 {} 两种格式）
            login_body_str = _apply_template(str(login_body_template), {
                "username": account_username,
                "password": account_password,
            })

            try:
                login_body = json.loads(login_body_str)
            except (json.JSONDecodeError, TypeError):
                login_body = {}

            async with httpx.AsyncClient(timeout=30, verify=False) as client:
                if login_method == "POST":
                    resp = await client.post(login_url, json=login_body, headers=login_headers)
                else:
                    resp = await client.get(login_url, headers=login_headers)

                try:
                    login_data = resp.json()
                except Exception:
                    login_data = {"raw": resp.text}

                # 从响应中提取 token（兼容 token_field 和 token_path 两种命名）
                token_field = config.get("token_field", "") or config.get("token_path", "")
                if token_field:
                    parts = token_field.split(".")
                    extracted = login_data
                    for p in parts:
                        if isinstance(extracted, dict):
                            extracted = extracted.get(p, "")
                        else:
                            extracted = ""
                            break
                    if extracted:
                        token = str(extracted)

        # Step 2: 执行签到
        signin_url = config.get("signin_url", "").strip() or site_url
        if not signin_url:
            return {"success": False, "error": "未配置签到 URL"}

        signin_method = config.get("signin_method", "POST").upper()

        # 构造签到请求头
        signin_headers = {}
        signin_headers_template = config.get("signin_headers", {})

        # 兼容 SITE_PRESETS 的 auth_header_template / auth_header_name 格式
        auth_header_template = config.get("auth_header_template", "")
        auth_header_name = config.get("auth_header_name", "Authorization")

        if isinstance(signin_headers_template, dict):
            for k, v in signin_headers_template.items():
                signin_headers[k] = _apply_template(str(v), {
                    "token": token,
                    "username": account_username,
                    "cookie": account_cookie or "",
                })

        # 如果没有通过 signin_headers 设置认证头，但配置了 auth_header_template
        if auth_header_template and auth_header_name not in signin_headers:
            signin_headers[auth_header_name] = _apply_template(auth_header_template, {
                "token": token,
                "username": account_username,
                "cookie": account_cookie or "",
            })

        # 确保有 Content-Type
        if "Content-Type" not in signin_headers:
            signin_headers["Content-Type"] = config.get("signin_content_type", "application/json")

        # 构造签到请求体
        signin_body_template = config.get("signin_body", "{}")
        signin_body_str = _apply_template(str(signin_body_template), {
            "token": token,
            "username": account_username,
        })
        try:
            signin_body = json.loads(signin_body_str)
        except (json.JSONDecodeError, TypeError):
            signin_body = {}

        async with httpx.AsyncClient(timeout=30, verify=False) as client:
            if signin_method == "POST":
                resp = await client.post(signin_url, json=signin_body, headers=signin_headers)
            elif signin_method == "GET":
                resp = await client.get(signin_url, headers=signin_headers)
            else:
                resp = await client.put(signin_url, json=signin_body, headers=signin_headers)

            try:
                resp_data = resp.json()
            except Exception:
                resp_data = {"raw": resp.text}

        # Step 3: 检查是否成功
        # 兼容 success_check 和 success_field 两种命名
        success_check = config.get("success_check", "") or config.get("success_field", "")
        message_field = config.get("message_field", "")

        if isinstance(resp_data, dict):
            # 检查 "今日已签到" 等关键词
            raw_text = str(resp_data)
            if _is_already_signed_in(raw_text):
                result["success"] = True
                msg = _extract_field(resp_data, message_field) if message_field else "今日已签到"
                result["message"] = str(msg) if msg else "今日已签到"
            elif success_check:
                val = _extract_field(resp_data, success_check)
                if val is not None and val is not False and val != "":
                    result["success"] = True
                    msg = _extract_field(resp_data, message_field) if message_field else "签到成功"
                    result["message"] = str(msg) if msg else "签到成功"
                else:
                    msg = _extract_field(resp_data, message_field) if message_field else ""
                    result["success"] = False
                    result["error"] = str(msg) if msg else "签到失败"
            elif message_field:
                msg = _extract_field(resp_data, message_field)
                if msg:
                    result["success"] = True
                    result["message"] = str(msg)
                elif resp.status_code == 200:
                    result["success"] = True
                    result["message"] = f"签到请求已发送 (HTTP {resp.status_code})"
                else:
                    result["error"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
            else:
                # 没有配置检查字段，根据 HTTP 状态码判断
                if resp.status_code == 200:
                    result["success"] = True
                    result["message"] = f"签到请求已发送 (HTTP {resp.status_code})"
                else:
                    result["error"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
        else:
            result["error"] = f"响应格式异常: {str(resp_data)[:200]}"

        result["raw_response"] = str(resp_data)[:500]
        result["status_code"] = resp.status_code

    except httpx.TimeoutException:
        result["error"] = "请求超时"
    except Exception as e:
        result["error"] = str(e)[:300]

    return result


# ============ 辅助方法 ============

ALREADY_SIGNED_IN_KEYWORDS = [
    "已签到", "已经签到", "今日已签", "already", "already signed",
    "signed in", "signed-in", "签到过", "重复签到", "signed", "sign in",
    "signin", "今日已签到", "您已签到", "sign in successful",
]


def _is_already_signed_in(msg: str) -> bool:
    """检查消息是否表示今日已签到"""
    if not msg:
        return False
    msg_lower = msg.lower()
    return any(kw.lower() in msg_lower for kw in ALREADY_SIGNED_IN_KEYWORDS)


def _apply_template(template: str, variables: Dict[str, str]) -> str:
    """替换模板变量，兼容 {{key}} 和 {key} 两种格式"""
    result = str(template)
    for key, value in variables.items():
        # 先替换 {{key}} 格式
        result = result.replace("{{" + key + "}}", str(value) if value is not None else "")
        # 再替换 {key} 格式
        result = result.replace("{" + key + "}", str(value) if value is not None else "")
    return result


def _extract_field(data: Any, path: str) -> Any:
    """支持嵌套路径提取值，如 data.token、result.message"""
    if not path or not isinstance(data, dict):
        return None
    keys = path.split(".")
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current
