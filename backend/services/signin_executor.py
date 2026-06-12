import httpx
import json
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime


async def execute_signin(
    site_type: str,
    site_url: str,
    account_username: str,
    account_password: str,
    account_token: Optional[str],
    account_cookie: Optional[str],
    api_config: Optional[Dict[str, Any]],
    account_id: Optional[int] = None,
    db=None,
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
        "use_login_cookies": true,  // 签到时复用登录返回的 cookies
        "proxy": "http://proxy.example.com:8080"  // 可选代理
    }

    多账号隔离：每个账号的登录 cookies 存储在各自的 account 记录中，
    签到执行时为每个账号创建独立的 httpx.AsyncClient，不复用连接。
    """
    result = {"success": False, "error": ""}

    try:
        config = api_config or {}

        # 获取代理配置（按 account_id 隔离）
        proxy = config.get("proxy", "") or None

        # Step 1: 登录获取 token（如果配置了 login_url）
        token = account_token or ""
        login_url = config.get("login_url", "").strip()
        login_cookies = {}
        login_success = False

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

            try:
                # 为每个账号创建独立的 httpx.AsyncClient，不复用连接
                async with httpx.AsyncClient(
                    timeout=30, verify=False, follow_redirects=True,
                    proxy=proxy,
                ) as client:
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

                    # 保存登录 cookies（按 account_id 隔离）
                    login_cookies = dict(resp.cookies)

                    try:
                        login_data = resp.json()
                    except Exception:
                        login_data = {"raw": resp.text}

                    # 检查登录是否成功
                    if resp.status_code == 401:
                        result["error"] = _classify_login_error(resp.status_code, resp.text, "密码错误或认证失败")
                    elif resp.status_code == 404:
                        result["error"] = _classify_login_error(resp.status_code, resp.text, "登录接口不存在 (404)")
                    elif resp.status_code >= 500:
                        result["error"] = _classify_login_error(resp.status_code, resp.text, f"服务器错误 (HTTP {resp.status_code})")
                    elif resp.status_code == 403:
                        result["error"] = _classify_login_error(resp.status_code, resp.text, "账号被禁止访问 (403 Forbidden)")
                    else:
                        login_success = True
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

                        # 如果 use_login_cookies=True 且登录成功，保存 cookies 到数据库（按 account_id 隔离）
                        use_login_cookies = config.get("use_login_cookies", False)
                        if use_login_cookies and login_cookies and account_id is not None and db is not None:
                            save_login_cookies(account_id, login_cookies, db)

            except httpx.TimeoutException:
                result["error"] = "登录请求超时，请检查网络连接或登录接口是否可达"
            except httpx.ConnectError:
                result["error"] = "登录连接失败，请检查网络连接或站点地址是否正确"
            except httpx.HTTPStatusError as e:
                result["error"] = f"登录HTTP错误: {e.response.status_code} - {e.response.text[:200]}"
            except Exception as e:
                result["error"] = f"登录过程异常: {str(e)[:300]}"

            # 如果登录出错，尝试使用数据库中缓存的 cookies（按 account_id 隔离）
            if result.get("error") and account_id is not None and db is not None:
                cached_cookies = get_login_cookies(account_id, db)
                if cached_cookies:
                    print(f"[signin_executor] 账号 {account_id} 登录失败，尝试使用缓存的 cookies (共 {len(cached_cookies)} 个)")
                    login_cookies = cached_cookies
                    login_success = True
                    result["error"] = ""  # 清除错误，尝试用缓存 cookies 继续

            # 如果仍然有错误，直接返回
            if result.get("error"):
                result["raw_response"] = resp.text[:500] if 'resp' in dir() else ""
                result["status_code"] = resp.status_code if 'resp' in dir() else 0
                return result
        else:
            # 没有 login_url，尝试从数据库加载缓存的 cookies
            login_success = True
            if account_id is not None and db is not None:
                cached_cookies = get_login_cookies(account_id, db)
                if cached_cookies:
                    login_cookies = cached_cookies

        # Step 2: 执行签到（为每个账号创建独立的 httpx.AsyncClient）
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

        try:
            # 为每个账号创建独立的 httpx.AsyncClient，不复用连接
            async with httpx.AsyncClient(
                timeout=30, verify=False, follow_redirects=True,
                proxy=proxy,
            ) as client:
                # 如果需要复用登录 cookies（按 account_id 隔离）
                use_login_cookies = config.get("use_login_cookies", False)
                if use_login_cookies and login_cookies:
                    client.cookies.update(login_cookies)
                    print(f"[signin_executor] 账号 {account_id} 使用 {len(login_cookies)} 个 cookies 进行签到")

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

        except httpx.TimeoutException:
            result["error"] = "签到请求超时，请检查网络连接或签到接口是否可达"
            return result
        except httpx.ConnectError:
            result["error"] = "签到连接失败，请检查网络连接或站点地址是否正确"
            return result
        except httpx.HTTPStatusError as e:
            result["error"] = f"签到HTTP错误: {e.response.status_code} - {e.response.text[:200]}"
            return result
        except Exception as e:
            result["error"] = f"签到请求异常: {str(e)[:300]}"
            return result

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
                    result["error"] = _classify_signin_error(resp.status_code, resp_text)
            else:
                if resp.status_code == 200:
                    result["success"] = True
                    result["message"] = "签到请求已发送"
                else:
                    result["error"] = _classify_signin_error(resp.status_code, resp_text)
        else:
            if resp.status_code == 200:
                result["success"] = True
                result["message"] = "签到请求已发送"
            else:
                result["error"] = _classify_signin_error(resp.status_code, resp_text)

        result["raw_response"] = resp_text[:500] if resp_text else ""
        result["status_code"] = resp.status_code

    except httpx.TimeoutException:
        result["error"] = "请求超时，请检查网络连接"
    except httpx.ConnectError:
        result["error"] = "连接失败，请检查网络连接或站点地址是否正确"
    except Exception as e:
        result["error"] = f"执行异常: {str(e)[:300]}"

    return result


# ============ Cookie 存储函数（按 account_id 隔离） ============

def save_login_cookies(account_id: int, cookies_dict: dict, db):
    """将登录 cookies 保存到数据库（按 account_id 隔离）"""
    try:
        from models.account import Account
        account = db.query(Account).filter(Account.id == account_id).first()
        if account:
            account.login_cookies = json.dumps(cookies_dict, ensure_ascii=False)
            account.cookies_updated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            db.commit()
            print(f"[signin_executor] 已保存账号 {account_id} 的登录 cookies (共 {len(cookies_dict)} 个)")
    except Exception as e:
        print(f"[signin_executor] 保存 cookies 失败 (账号 {account_id}): {e}")


def get_login_cookies(account_id: int, db) -> dict:
    """从数据库获取登录 cookies（按 account_id 隔离）"""
    try:
        from models.account import Account
        account = db.query(Account).filter(Account.id == account_id).first()
        if account and account.login_cookies:
            cookies = json.loads(account.login_cookies)
            if isinstance(cookies, dict):
                return cookies
    except Exception as e:
        print(f"[signin_executor] 获取 cookies 失败 (账号 {account_id}): {e}")
    return {}


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


def _classify_login_error(status_code: int, resp_text: str, default_msg: str) -> str:
    """根据登录响应分类错误类型，提供更详细的错误提示"""
    text = resp_text[:200].lower() if resp_text else ""

    if status_code == 401:
        if "password" in text or "密码" in text:
            return f"密码错误 (HTTP 401): {resp_text[:200]}"
        elif "user" in text or "账号" in text or "account" in text:
            return f"账号不存在或认证失败 (HTTP 401): {resp_text[:200]}"
        else:
            return f"认证失败 (HTTP 401): {resp_text[:200]}"

    if status_code == 403:
        return f"账号被禁止访问 (HTTP 403): {resp_text[:200]}"

    if status_code == 404:
        return f"登录接口不存在 (HTTP 404): 请检查站点配置中的登录URL是否正确"

    if status_code >= 500:
        return f"服务器内部错误 (HTTP {status_code}): 服务端可能暂时不可用，请稍后重试"

    return f"{default_msg}: {resp_text[:200]}"


def _classify_signin_error(status_code: int, resp_text: str) -> str:
    """根据签到响应分类错误类型，提供更详细的错误提示"""
    text = resp_text[:200].lower() if resp_text else ""

    if status_code == 401:
        return f"未登录或登录已过期 (HTTP 401): {resp_text[:200]}"

    if status_code == 403:
        if "permission" in text or "权限" in text:
            return f"权限不足 (HTTP 403): {resp_text[:200]}"
        return f"禁止访问 (HTTP 403): {resp_text[:200]}"

    if status_code == 404:
        return f"签到接口不存在 (HTTP 404): 请检查站点配置中的签到URL是否正确"

    if status_code == 429:
        return f"请求过于频繁 (HTTP 429): 请稍后重试"

    if status_code >= 500:
        return f"服务器内部错误 (HTTP {status_code}): 服务端可能暂时不可用，请稍后重试"

    return f"HTTP {status_code}: {resp_text[:200]}"
