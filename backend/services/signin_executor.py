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
        "login_body_template": {"username": "{{username}}", "password": "{{password}}"},
        "login_content_type": "application/json" 或 "application/x-www-form-urlencoded",
        "token_path": "data.token",
        "signin_url": "https://xxx/api/checkin",
        "signin_method": "POST",
        "signin_body": "{}",
        "signin_content_type": "application/json",
        "auth_header_template": "Bearer {{token}}",
        "auth_header_name": "Authorization",
        "success_field": "success",
        "message_field": "message",
        "use_login_cookies": true  // 签到时复用登录返回的 cookies
    }
    """
    result = {"success": False, "error": ""}

    try:
        config = api_config or {}

        # Step 1: 登录获取 token（如果配置了 login_url）
        token = account_token or ""
        login_url = config.get("login_url", "").strip()
        login_cookies = {}

        if login_url:
            login_method = config.get("login_method", "POST").upper()
            login_body_template = config.get("login_body") or config.get("login_body_template", "{}")
            content_type = config.get("login_content_type", "application/json")
            login_headers = {"Content-Type": content_type, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

            # 替换模板变量
            login_body_str = _apply_template(str(login_body_template), {
                "username": account_username,
                "password": account_password,
            })

            async with httpx.AsyncClient(timeout=30, verify=False, follow_redirects=True) as client:
                if login_method == "POST":
                    if content_type == "application/x-www-form-urlencoded":
                        resp = await client.post(login_url, content=login_body_str, headers=login_headers)
                    else:
                        try:
                            login_body = json.loads(login_body_str)
                        except (json.JSONDecodeError, TypeError):
                            login_body = {}
                        resp = await client.post(login_url, json=login_body, headers=login_headers)
                else:
                    resp = await client.get(login_url, headers=login_headers)

                # 保存登录 cookies
                login_cookies = dict(resp.cookies)

                try:
                    login_data = resp.json()
                except Exception:
                    login_data = {"raw": resp.text}

                # 从响应中提取 token
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
        signin_content_type = config.get("signin_content_type", "application/json")

        # 构造签到请求头
        signin_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        signin_headers_template = config.get("signin_headers", {})

        if isinstance(signin_headers_template, dict):
            for k, v in signin_headers_template.items():
                signin_headers[k] = _apply_template(str(v), {
                    "token": token,
                    "username": account_username,
                    "cookie": account_cookie or "",
                })

        # auth_header_template
        auth_header_template = config.get("auth_header_template", "")
        auth_header_name = config.get("auth_header_name", "Authorization")
        if auth_header_template and auth_header_name not in signin_headers:
            signin_headers[auth_header_name] = _apply_template(auth_header_template, {
                "token": token,
                "username": account_username,
                "cookie": account_cookie or "",
            })

        if signin_content_type and "Content-Type" not in signin_headers:
            signin_headers["Content-Type"] = signin_content_type

        # 构造签到请求体
        signin_body_template = config.get("signin_body", "{}")
        signin_body_str = _apply_template(str(signin_body_template), {
            "token": token,
            "username": account_username,
        })

        async with httpx.AsyncClient(timeout=30, verify=False, follow_redirects=True) as client:
            # 如果需要复用登录 cookies
            use_login_cookies = config.get("use_login_cookies", False)
            if use_login_cookies and login_cookies:
                client.cookies.update(login_cookies)

            # 如果用户提供了 account_cookie，也加上
            if account_cookie:
                for cookie_str in account_cookie.split(";"):
                    cookie_str = cookie_str.strip()
                    if "=" in cookie_str:
                        k, v = cookie_str.split("=", 1)
                        client.cookies.set(k.strip(), v.strip())

            if signin_method == "POST":
                if signin_content_type == "application/x-www-form-urlencoded":
                    resp = await client.post(signin_url, content=signin_body_str, headers=signin_headers)
                else:
                    try:
                        signin_body = json.loads(signin_body_str)
                    except (json.JSONDecodeError, TypeError):
                        signin_body = {}
                    resp = await client.post(signin_url, json=signin_body, headers=signin_headers)
            elif signin_method == "GET":
                resp = await client.get(signin_url, headers=signin_headers)
            else:
                if signin_content_type == "application/x-www-form-urlencoded":
                    resp = await client.put(signin_url, content=signin_body_str, headers=signin_headers)
                else:
                    try:
                        signin_body = json.loads(signin_body_str)
                    except (json.JSONDecodeError, TypeError):
                        signin_body = {}
                    resp = await client.put(signin_url, json=signin_body, headers=signin_headers)

            resp_text = resp.text
            try:
                resp_data = resp.json()
            except Exception:
                resp_data = {"raw": resp_text}

        # Step 3: 检查是否成功
        success_check = config.get("success_check", "") or config.get("success_field", "")
        message_field = config.get("message_field", "")

        # 检查 "今日已签到" 等关键词（对文本和 JSON 都检查）
        raw_text = resp_text if resp_text else str(resp_data)
        if _is_already_signed_in(raw_text):
            result["success"] = True
            msg = _extract_field(resp_data, message_field) if message_field else "今日已签到"
            result["message"] = str(msg) if msg else "今日已签到"
        elif isinstance(resp_data, dict):
            if success_check:
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
                    result["error"] = f"HTTP {resp.status_code}: {resp_text[:200]}"
            else:
                if resp.status_code == 200:
                    result["success"] = True
                    result["message"] = f"签到请求已发送 (HTTP {resp.status_code})"
                else:
                    result["error"] = f"HTTP {resp.status_code}: {resp_text[:200]}"
        else:
            if resp.status_code == 200:
                result["success"] = True
                result["message"] = "签到请求已发送"
            else:
                result["error"] = f"HTTP {resp.status_code}: {resp_text[:200]}"

        result["raw_response"] = resp_text[:500] if resp_text else ""
        result["status_code"] = resp.status_code

    except httpx.TimeoutException:
        result["error"] = "请求超时"
    except Exception as e:
        result["error"] = str(e)[:300]

    return result


# ============ 辅助方法 ============

ALREADY_SIGNED_IN_KEYWORDS = [
    "已签到", "已经签到", "今日已签", "already", "already signed",
    "signed in", "signed-in", "签到过", "重复签到", "signed",
    "今日已签到", "您已签到", "您今日已",
]


def _is_already_signed_in(msg: str) -> bool:
    if not msg:
        return False
    msg_lower = msg.lower()
    return any(kw.lower() in msg_lower for kw in ALREADY_SIGNED_IN_KEYWORDS)


def _apply_template(template: str, variables: Dict[str, str]) -> str:
    result = str(template)
    for key, value in variables.items():
        result = result.replace("{{" + key + "}}", str(value) if value is not None else "")
        result = result.replace("{" + key + "}", str(value) if value is not None else "")
    return result


def _extract_field(data: Any, path: str) -> Any:
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
