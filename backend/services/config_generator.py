import httpx
import json
import re
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse, urljoin

# 常见登录路径探测列表
COMMON_LOGIN_PATHS = [
    "/api/user/login",
    "/api/auth/login",
    "/api/v1/login",
    "/api/login",
    "/v1/user/login",
    "/v1/login",
    "/user/login",
    "/auth/login",
    "/login",
    "/api/user/login-pwd",
    "/member.php?mod=logging&action=login&loginsubmit=yes&infloat=yes&lssubmit=yes&inajax=1",
]

# 常见签到路径探测列表
COMMON_SIGNIN_PATHS = [
    "/api/user/checkin",
    "/api/user/signin",
    "/api/v1/signin",
    "/api/v1/checkin",
    "/api/user/sign",
    "/api/sign",
    "/api/checkin",
    "/user/checkin",
    "/user/signin",
    "/signin",
    "/checkin",
    "/sign",
    "/plugin.php?id=k_misign:sign&operation=qiandao&format=empty",
]

async def probe_site(url: str, username: str = "", password: str = "") -> Dict[str, Any]:
    """
    探测站点，尝试找到登录和签到接口
    返回: {
        "success": bool,
        "message": str,
        "detected_login_url": str or None,
        "detected_signin_url": str or None,
        "login_response_sample": dict or None,
        "signin_response_sample": dict or None,
        "api_config": dict or None,  # 生成的配置
        "curl_commands": dict,  # 测试用 curl 命令
        "probed_endpoints": list,  # 探测过的端点列表
    }
    """
    result = {
        "success": False,
        "message": "",
        "detected_login_url": None,
        "detected_signin_url": None,
        "login_response_sample": None,
        "signin_response_sample": None,
        "api_config": None,
        "curl_commands": {},
        "probed_endpoints": [],
    }

    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    detected_login = None
    login_resp_data = None
    login_content_type = "application/json"
    login_body_format = "json"
    login_username_field = "username"

    # Step 1: 探测登录接口
    async with httpx.AsyncClient(timeout=10, verify=False, follow_redirects=True) as client:
        for path in COMMON_LOGIN_PATHS:
            full_url = urljoin(base_url, path)
            result["probed_endpoints"].append(f"LOGIN PROBE: {full_url}")

            try:
                # 尝试 JSON 格式
                json_body = _guess_login_body(path, username, password, "json")
                resp = await client.post(full_url, json=json_body, headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0"
                }, timeout=8)

                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        if isinstance(data, dict) and (data.get("success") or data.get("token") or data.get("data") or "token" in str(data).lower() or "access_token" in str(data).lower()):
                            detected_login = full_url
                            login_resp_data = data
                            login_content_type = "application/json"
                            break
                    except:
                        pass

                # 如果 JSON 失败，尝试 form-urlencoded
                if not detected_login and resp.status_code in [200, 302, 401, 403]:
                    form_body = _guess_login_body(path, username, password, "form")
                    resp2 = await client.post(full_url, content=form_body, headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "User-Agent": "Mozilla/5.0"
                    }, timeout=8)

                    if resp2.status_code == 200:
                        try:
                            data = resp2.json()
                            if isinstance(data, dict) and (data.get("success") or data.get("token") or data.get("data")):
                                detected_login = full_url
                                login_resp_data = data
                                login_content_type = "application/x-www-form-urlencoded"
                                login_body_format = "form"
                                break
                        except:
                            # Discuz 论坛返回 XML/HTML
                            if "CDATA" in resp2.text or "logging" in path:
                                detected_login = full_url
                                login_resp_data = {"raw": resp2.text[:500]}
                                login_content_type = "application/x-www-form-urlencoded"
                                login_body_format = "form"
                                break
            except Exception:
                continue

    if not detected_login:
        result["message"] = f"未能自动探测到登录接口。已尝试 {len(COMMON_LOGIN_PATHS)} 个常见路径。建议：\n1. 在浏览器 F12 Network 中找到登录请求\n2. 提供请求的 URL、方法、请求体格式\n3. 或提供 HAR 文件"
        return result

    result["detected_login_url"] = detected_login
    result["login_response_sample"] = login_resp_data

    # Step 2: 分析登录响应，提取 token 路径
    token_path = _detect_token_path(login_resp_data) if isinstance(login_resp_data, dict) else ""

    # Step 3: 探测签到接口
    detected_signin = None
    signin_resp_data = None

    async with httpx.AsyncClient(timeout=10, verify=False, follow_redirects=True) as client:
        for path in COMMON_SIGNIN_PATHS:
            full_url = urljoin(base_url, path)
            result["probed_endpoints"].append(f"SIGNIN PROBE: {full_url}")

            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                if token_path and login_resp_data:
                    token_val = _extract_nested(login_resp_data, token_path)
                    if token_val:
                        headers["Authorization"] = f"Bearer {token_val}"

                resp = await client.post(full_url, json={}, headers=headers, timeout=8)

                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        detected_signin = full_url
                        signin_resp_data = data
                        break
                    except:
                        if resp.text:
                            detected_signin = full_url
                            signin_resp_data = {"raw": resp.text[:500]}
                            break
            except:
                continue

    result["detected_signin_url"] = detected_signin
    result["signin_response_sample"] = signin_resp_data

    # Step 4: 生成 api_config
    api_config = _generate_api_config(
        detected_login, login_content_type, login_body_format,
        username, password, token_path,
        detected_signin, login_resp_data
    )
    result["api_config"] = api_config

    # Step 5: 生成 curl 命令
    result["curl_commands"] = _generate_curl_commands(api_config, username, password)

    if detected_login:
        result["success"] = True
        result["message"] = f"探测完成！发现登录接口: {detected_login}" + (f"\n发现签到接口: {detected_signin}" if detected_signin else "\n未探测到签到接口，请手动补充")

    return result


def _guess_login_body(path: str, username: str, password: str, fmt: str) -> Any:
    """根据路径猜测登录请求体格式"""
    if "member.php" in path:
        # Discuz 论坛
        return f"username={username}&password={password}&quickforward=yes&handlekey=login"

    if fmt == "form":
        return f"username={username}&password={password}"

    # JSON 格式，猜测字段名
    if "login-pwd" in path:
        return {"email": username, "password": password}
    return {"username": username, "password": password}


def _detect_token_path(data: dict) -> str:
    """从登录响应中检测 token 字段路径"""
    if not isinstance(data, dict):
        return ""

    # 常见 token 字段
    token_keys = ["token", "access_token", "session_token", "api_key"]
    for key in token_keys:
        if key in data and isinstance(data[key], str):
            return key

    # 检查 data 子对象
    if "data" in data and isinstance(data["data"], dict):
        for key in ["token", "access_token", "id", "session"]:
            if key in data["data"]:
                return f"data.{key}"

    # 检查 result 子对象
    if "result" in data and isinstance(data["result"], dict):
        for key in ["token", "access_token"]:
            if key in data["result"]:
                return f"result.{key}"

    return ""


def _extract_nested(data: dict, path: str) -> str:
    parts = path.split(".")
    current = data
    for p in parts:
        if isinstance(current, dict) and p in current:
            current = current[p]
        else:
            return ""
    return str(current) if current else ""


def _generate_api_config(login_url, content_type, body_format, username, password, token_path, signin_url, login_resp) -> dict:
    """生成 api_config JSON"""
    config = {}

    if login_url:
        config["login_url"] = login_url
        config["login_method"] = "POST"

        if body_format == "form":
            if "member.php" in login_url:
                config["login_body_template"] = "username={{username}}&password={{password}}&quickforward=yes&handlekey=login"
            else:
                config["login_body_template"] = "username={{username}}&password={{password}}"
            config["login_content_type"] = "application/x-www-form-urlencoded"
        else:
            if "login-pwd" in login_url:
                config["login_body_template"] = '{"email": "{{username}}", "password": "{{password}}"}'
            else:
                config["login_body_template"] = '{"username": "{{username}}", "password": "{{password}}"}'
            config["login_content_type"] = "application/json"

        config["token_path"] = token_path

    if signin_url:
        config["signin_url"] = signin_url
        config["signin_method"] = "POST"
        config["signin_body"] = "{}"
        config["signin_content_type"] = "application/json"

        if token_path:
            config["auth_header_name"] = "Authorization"
            config["auth_header_template"] = "Bearer {{token}}"
        else:
            config["auth_header_name"] = ""
            config["auth_header_template"] = ""
            config["use_login_cookies"] = True

    config["success_field"] = "success"
    config["message_field"] = "message"

    return config


def _generate_curl_commands(config: dict, username: str, password: str) -> dict:
    """生成测试用 curl 命令"""
    commands = {}

    login_url = config.get("login_url", "")
    if login_url:
        ct = config.get("login_content_type", "application/json")
        body_tpl = config.get("login_body_template", "")
        body = body_tpl.replace("{{username}}", username).replace("{{password}}", password)

        if ct == "application/x-www-form-urlencoded":
            commands["login"] = f'curl -s -X POST "{login_url}" -H "Content-Type: application/x-www-form-urlencoded" -d \'{body}\''
        else:
            commands["login"] = f'curl -s -X POST "{login_url}" -H "Content-Type: application/json" -d \'{body}\''

    signin_url = config.get("signin_url", "")
    if signin_url:
        auth_header = config.get("auth_header_name", "")
        auth_tpl = config.get("auth_header_template", "")
        if auth_header and auth_tpl:
            # 需要用户替换 token
            token_placeholder = auth_tpl.replace("{{token}}", "YOUR_TOKEN_HERE")
            commands["signin"] = f'curl -s -X POST "{signin_url}" -H "{auth_header}: {token_placeholder}" -H "Content-Type: application/json"'
        else:
            commands["signin"] = f'curl -s -X POST "{signin_url}" -H "Content-Type: application/json" -b "your_cookie_here"'

    return commands
