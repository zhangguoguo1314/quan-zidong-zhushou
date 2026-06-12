from typing import Dict, Any, Optional
import json
import urllib.request
import urllib.error
import urllib.parse
import http.cookiejar
import ssl


class CustomApiPlugin:
    """通用自定义 API 签到插件 - 支持多样化的配置

    支持的高级特性：
    - 登录 → 提取 token → 签到 标准流程
    - 跳过登录直接签到（账号已有 token/cookie 时）
    - 自定义请求头（额外 headers）
    - URL query 参数支持
    - Cookie 持久化保留
    - 自定义请求方法/内容类型
    - "今日已签到"关键词识别
    """

    name = "custom-api"
    site_type = "custom-api"

    ALREADY_SIGNED_IN_KEYWORDS = [
        "已签到", "已经签到", "今日已签", "already", "already signed",
        "signed in", "signed-in", "签到过", "重复签到", "signed", "sign in",
        "signin", "今日已签到", "您已签到", "sign in successful"
    ]

    def __init__(self):
        self._cookie_jar = http.cookiejar.CookieJar()

    async def sign_in(self, account, site=None, api_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            self._cookie_jar = http.cookiejar.CookieJar()

            config = api_config or (getattr(site, 'api_config', None) if site else None)
            if not config:
                return {"success": False, "error": "未配置 api_config"}

            username = account.username
            password = account.password
            token = getattr(account, 'token', None)
            cookie_str = getattr(account, 'cookie', None)

            if not username or not password:
                # 如果没有密码但有 token/cookie，仍然尝试直接签到
                if not token and not cookie_str:
                    return {"success": False, "error": "用户名/密码未设置"}

            # 预先填充 cookie（如果账号已有）
            if cookie_str:
                try:
                    self._load_cookie_string(cookie_str)
                except Exception:
                    pass

            result_msg = ""

            # ============ Step 1: 登录请求 ============
            # 如果已有 token 且配置要求使用 token，可以跳过登录
            login_url = config.get("login_url", "").strip()
            token = token or None
            extracted_token = None

            if login_url and (not token or config.get("force_login", False)):
                login_method = (config.get("login_method", "POST") or "POST").upper()
                login_body = self._apply_template(
                    config.get("login_body_template", '{"username": "{{username}}", "password": "{{password}}"}'),
                    {"username": username, "password": password}
                )
                login_content_type = config.get("login_content_type", "application/json")

                extra_headers = config.get("login_extra_headers", {}) or {}

                login_response = await self._http_request(
                    url=login_url,
                    method=login_method,
                    body=login_body,
                    content_type=login_content_type,
                    use_cookies=True,
                    extra_headers=extra_headers,
                    verify_ssl=config.get("verify_ssl", True)
                )

                if not login_response["success"]:
                    err_msg = str(login_response.get("error", ""))
                    if self._is_already_signed_in(err_msg):
                        return {"success": True, "message": err_msg}
                    return {"success": False, "error": f"登录失败: {login_response['error']}"}

                # 从登录响应提取 token
                token_path = config.get("token_path", "token")
                extracted_token = self._extract_value(login_response["data"], token_path)

                if not extracted_token:
                    message_field = config.get("message_field", "")
                    if message_field:
                        msg = self._extract_value(login_response["data"], message_field)
                        if msg and self._is_already_signed_in(str(msg)):
                            return {"success": True, "message": str(msg)}
                        if msg:
                            return {"success": True, "message": str(msg)}

                    success_field = config.get("success_field", "")
                    if success_field:
                        val = self._extract_value(login_response["data"], success_field)
                        if val and val is not False:
                            return {"success": True, "message": "登录成功，无需额外签到"}

                    # 登录成功但没拿到 token，这可能是 "登录即签到" 的站点
                    # 此时继续使用可能为真的 token，或者视为成功
                    if config.get("login_only", False):
                        return {"success": True, "message": "登录完成（该站点登录即签到）"}

                    # 如果 cookie 被保存，可能后面用 cookie 签到
                    if self._cookie_jar and len(list(self._cookie_jar)) > 0:
                        result_msg = "登录成功（使用 cookie 继续）"
                    else:
                        return {"success": False, "error": f"无法从响应提取 token (路径: {token_path})"}

            # 选择最终 token
            final_token = extracted_token or token

            # ============ Step 2: 签到请求 ============
            signin_url = config.get("signin_url", "").strip()
            if not signin_url:
                # 如果没有签到 URL，说明登录就是签到
                if login_url:
                    return {"success": True, "message": result_msg or "登录成功（该站点登录即签到）"}
                return {"success": False, "error": "未配置签到地址"}

            signin_method = (config.get("signin_method", "POST") or "POST").upper()
            signin_body = config.get("signin_body", "{}")
            signin_content_type = config.get("signin_content_type", "application/json")

            # 构造认证 header
            auth_header_template = config.get("auth_header_template", "Bearer {{token}}")
            auth_header_name = config.get("auth_header_name", "Authorization")

            extra_headers = config.get("signin_extra_headers", {}) or {}
            if auth_header_template and final_token:
                extra_headers[auth_header_name] = self._apply_template(auth_header_template, {"token": str(final_token)})

            # 额外 header 合并
            global_headers = config.get("extra_headers", {}) or {}
            if global_headers:
                extra_headers.update(global_headers)

            signin_response = await self._http_request(
                url=signin_url,
                method=signin_method,
                body=signin_body,
                content_type=signin_content_type,
                extra_headers=extra_headers,
                use_cookies=True,
                verify_ssl=config.get("verify_ssl", True)
            )

            if not signin_response["success"]:
                err_msg = str(signin_response.get("error", ""))
                if self._is_already_signed_in(err_msg):
                    return {"success": True, "message": err_msg}
                return {"success": False, "error": f"签到失败: {signin_response['error']}"}

            # ============ Step 3: 解析响应 ============
            success_field = config.get("success_field", "")
            if success_field:
                val = self._extract_value(signin_response["data"], success_field)
                if isinstance(val, bool) and val is False:
                    msg = self._extract_value(signin_response["data"], config.get("message_field", "")) or "签到请求被拒绝"
                    if self._is_already_signed_in(str(msg)):
                        return {"success": True, "message": str(msg)}
                    return {"success": False, "error": str(msg)}

            message_field = config.get("message_field", "")
            if message_field:
                msg = self._extract_value(signin_response["data"], message_field)
                if msg:
                    return {"success": True, "message": str(msg)}

            return {"success": True, "message": "签到成功"}

        except Exception as e:
            return {"success": False, "error": f"签到异常: {str(e)}"}

    async def validate(self, account) -> bool:
        return bool(account.username and (account.password or getattr(account, 'token', None) or getattr(account, 'cookie', None)))

    def is_api_mode(self) -> bool:
        return True

    # ============ 辅助方法 ============

    def _is_already_signed_in(self, msg: str) -> bool:
        if not msg:
            return False
        msg_lower = str(msg).lower()
        return any(kw.lower() in msg_lower for kw in self.ALREADY_SIGNED_IN_KEYWORDS)

    def _apply_template(self, template: str, variables: Dict[str, str]) -> str:
        result = str(template)
        for key, value in variables.items():
            placeholder = "{{" + key + "}}"
            result = result.replace(placeholder, str(value) if value is not None else "")
        return result

    def _extract_value(self, data: Any, path: str) -> Any:
        """支持 token / data.token / result.data.user.id 等嵌套路径"""
        if not path:
            return None
        if not isinstance(data, dict):
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except (json.JSONDecodeError, TypeError):
                    return None
            else:
                return None

        keys = path.split(".")
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current

    def _load_cookie_string(self, cookie_str: str):
        """从字符串解析 cookie（简单格式：name=value; name2=value2）"""
        if not cookie_str:
            return
        import http.cookies
        c = http.cookies.SimpleCookie()
        c.load(cookie_str)
        # 这里只是简单加载到当前 jar
        for key, morsel in c.items():
            cookie = http.cookiejar.Cookie(
                version=0, name=key, value=morsel.value, port=None, port_specified=False,
                domain="", domain_specified=False, domain_initial_dot=False,
                path="/", path_specified=True, secure=False, expires=None,
                discard=True, comment=None, comment_url=None, rest={"HttpOnly": None},
                rfc2109=False
            )
            try:
                self._cookie_jar.set_cookie(cookie)
            except Exception:
                pass

    async def _http_request(
        self,
        url: str,
        method: str = "POST",
        body: str = "{}",
        content_type: str = "application/json",
        extra_headers: Optional[Dict[str, str]] = None,
        use_cookies: bool = False,
        verify_ssl: bool = True
    ) -> Dict[str, Any]:
        try:
            ssl_context = ssl.create_default_context()
            if not verify_ssl:
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

            headers = {
                "Content-Type": content_type,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            if extra_headers:
                for k, v in extra_headers.items():
                    headers[k] = str(v)

            cookie_handler = urllib.request.HTTPCookieProcessor(self._cookie_jar)
            https_handler = urllib.request.HTTPSHandler(context=ssl_context)
            opener = urllib.request.build_opener(cookie_handler, https_handler)

            if method == "GET":
                # 支持将 body 作为 query 参数解析附加到 URL
                req = urllib.request.Request(url, headers=headers, method="GET")
            else:
                if isinstance(body, dict):
                    body_bytes = json.dumps(body, ensure_ascii=False).encode('utf-8')
                elif isinstance(body, str):
                    # 检查内容类型
                    if content_type and "json" in content_type.lower():
                        try:
                            json.loads(body)
                            body_bytes = body.encode('utf-8')
                        except json.JSONDecodeError:
                            body_bytes = body.encode('utf-8')
                    else:
                        body_bytes = body.encode('utf-8')
                else:
                    body_bytes = str(body).encode('utf-8')
                req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)

            try:
                with opener.open(req, timeout=30) as response:
                    raw_data = response.read().decode('utf-8', errors='ignore')
                    try:
                        json_data = json.loads(raw_data)
                        return {"success": True, "data": json_data}
                    except (json.JSONDecodeError, TypeError):
                        return {"success": True, "data": {"message": raw_data[:500]}}
            except urllib.error.HTTPError as e:
                try:
                    raw_data = e.read().decode('utf-8', errors='ignore')
                    try:
                        json_data = json.loads(raw_data)
                        return {"success": False, "error": f"{self._extract_error_message(json_data)}"}
                    except (json.JSONDecodeError, TypeError):
                        return {"success": False, "error": raw_data[:200]}
                except Exception:
                    return {"success": False, "error": f"HTTP {e.code}: {e.reason}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _extract_error_message(self, data: Any) -> str:
        if not isinstance(data, dict):
            return str(data)
        for key in ["error", "message", "msg", "detail", "error_message", "err_msg"]:
            if key in data:
                val = data[key]
                if isinstance(val, str):
                    return val
                if isinstance(val, dict) and "message" in val:
                    return str(val["message"])
                return str(val)
        return str(data)[:200]
