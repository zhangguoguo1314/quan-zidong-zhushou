"""
Discuz! 论坛签到插件。

支持 Discuz! X3.2/X3.4 论坛的自动签到，使用 k_misign（百变每日签到）插件。

流程：
1. GET 登录页面 → 提取 loginhash 和 formhash
2. POST 登录 → 获取 Cookie（saltkey + auth）
3. GET 签到页面 → 提取新的 formhash
4. GET 签到接口 → 完成签到

认证方式：Cookie 认证（Discuz! 标准机制）
"""
from typing import Dict, Any, Optional
import re
import httpx


class DiscuzPlugin:
    """Discuz! 论坛签到插件"""

    name = "discuz"
    site_type = "discuz"

    ALREADY_SIGNED_IN_KEYWORDS = [
        "已签到", "已经签到", "今日已签", "您已签到", "您今日已",
        "签到成功", "签到完成", "连续签到",
        "already", "already signed", "signed in",
    ]

    def __init__(self):
        pass

    async def sign_in(
        self,
        account,
        site=None,
        api_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        执行 Discuz 论坛签到。

        api_config 支持的字段：
        - base_url: 论坛地址（如 https://bbs.binmt.cc）
        - cookiepre: Cookie 前缀（如 cQWy_2132_），可选，自动检测
        - login_questionid: 安全提问 ID（默认 0）
        - login_answer: 安全提问答案（默认空）
        """
        try:
            config = api_config or {}
            base_url = (config.get("base_url") or "").rstrip("/")
            if not base_url:
                base_url = getattr(site, "url", "").rstrip("/") if site else ""
            if not base_url:
                return {"success": False, "error": "未配置论坛地址 (base_url)"}

            username = account.username
            password = account.password
            if not username or not password:
                return {"success": False, "error": "用户名或密码未设置"}

            cookiepre = config.get("cookiepre", "")
            questionid = config.get("login_questionid", "0")
            answer = config.get("login_answer", "")

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            }

            async with httpx.AsyncClient(
                timeout=30, verify=False, follow_redirects=True,
                headers=headers,
            ) as client:
                # ============ Step 1: 获取登录页面的 loginhash 和 formhash ============
                login_page_url = (
                    f"{base_url}/member.php?mod=logging&action=login"
                    f"&infloat=yes&handlekey=login&inajax=1"
                )
                login_page_resp = await client.get(login_page_url)
                login_page_html = login_page_resp.text

                # 自动检测 cookiepre
                if not cookiepre:
                    match = re.search(r"var\s+cookiepre\s*=\s*['\"]([^'\"]+)['\"]", login_page_html)
                    if match:
                        cookiepre = match.group(1)

                # 提取 loginhash
                loginhash = ""
                lh_match = re.search(r'loginhash=([a-zA-Z0-9]+)', login_page_html)
                if lh_match:
                    loginhash = lh_match.group(1)

                # 提取 formhash
                formhash = self._extract_formhash(login_page_html)

                # ============ Step 2: 执行登录 ============
                login_url = (
                    f"{base_url}/member.php?mod=logging&action=login"
                    f"&loginsubmit=yes&handlekey=login"
                    f"&loginhash={loginhash}&inajax=1"
                )
                login_data = {
                    "formhash": formhash,
                    "referer": f"{base_url}/forum.php",
                    "loginfield": "username",
                    "username": username,
                    "password": password,
                    "questionid": questionid,
                    "answer": answer,
                    "cookietime": "2592000",
                }
                login_resp = await client.post(
                    login_url,
                    data=login_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                login_text = login_resp.text

                # 检查登录是否成功
                if "欢迎您回来" not in login_text and "登录成功" not in login_text:
                    # 尝试提取错误信息
                    error_match = re.search(r'errorhandle_login\([^)]*"([^"]+)"', login_text)
                    if error_match:
                        error_msg = error_match.group(1)
                        return {"success": False, "error": f"登录失败: {error_msg}"}
                    if "密码错误" in login_text or "password" in login_text.lower():
                        return {"success": False, "error": "登录失败: 密码错误"}
                    if "登录失败" in login_text:
                        return {"success": False, "error": f"登录失败: {login_text[:200]}"}
                    # 有些论坛登录成功但不返回 "欢迎您回来"，检查是否有 auth cookie
                    auth_cookie_name = f"{cookiepre}auth" if cookiepre else "auth"
                    has_auth = any(auth_cookie_name in k for k in client.cookies.keys())
                    if not has_auth:
                        return {"success": False, "error": f"登录失败: {login_text[:200]}"}

                # ============ Step 3: 获取签到页面的 formhash ============
                sign_page_url = f"{base_url}/k_misign-sign.html"
                sign_page_resp = await client.get(sign_page_url)
                sign_page_html = sign_page_resp.text

                sign_formhash = self._extract_formhash(sign_page_html)
                if not sign_formhash:
                    # 尝试从其他页面获取 formhash
                    home_resp = await client.get(f"{base_url}/forum.php")
                    sign_formhash = self._extract_formhash(home_resp.text)
                if not sign_formhash:
                    return {"success": False, "error": "无法获取签到 formhash，请检查是否已登录"}

                # ============ Step 4: 执行签到 ============
                sign_url = (
                    f"{base_url}/plugin.php?id=k_misign:sign"
                    f"&operation=qiandao&formhash={sign_formhash}"
                    f"&format=text&inajax=1"
                )
                sign_resp = await client.get(sign_url)
                sign_text = sign_resp.text

                # ============ Step 5: 解析签到结果 ============
                if self._is_already_signed_in(sign_text):
                    return {"success": True, "message": self._extract_sign_message(sign_text)}

                if "签到成功" in sign_text or "积分" in sign_text:
                    return {"success": True, "message": self._extract_sign_message(sign_text)}

                if sign_resp.status_code == 200:
                    return {"success": True, "message": self._extract_sign_message(sign_text) or "签到请求已发送"}

                return {"success": False, "error": f"签到失败: {sign_text[:200]}"}

        except httpx.TimeoutException:
            return {"success": False, "error": "请求超时，请检查网络连接"}
        except httpx.ConnectError:
            return {"success": False, "error": "连接失败，请检查论坛地址是否正确"}
        except Exception as e:
            return {"success": False, "error": f"签到异常: {str(e)[:300]}"}

    async def validate(self, account) -> bool:
        return bool(account.username and account.password)

    def is_api_mode(self) -> bool:
        return True

    def _extract_formhash(self, html: str) -> str:
        """从 HTML 中提取 formhash"""
        # 匹配 <input type="hidden" name="formhash" value="xxx" />
        match = re.search(r'name="formhash"\s+value="([a-zA-Z0-9]+)"', html)
        if match:
            return match.group(1)
        # 匹配 <input value="xxx" name="formhash" />
        match = re.search(r'value="([a-zA-Z0-9]+)"\s+name="formhash"', html)
        if match:
            return match.group(1)
        # 宽松匹配
        match = re.search(r'formhash["\s=]+([a-zA-Z0-9]{6,})', html)
        if match:
            return match.group(1)
        return ""

    def _is_already_signed_in(self, msg: str) -> bool:
        if not msg:
            return False
        msg_lower = msg.lower()
        return any(kw.lower() in msg_lower for kw in self.ALREADY_SIGNED_IN_KEYWORDS)

    def _extract_sign_message(self, text: str) -> str:
        """从签到响应中提取消息文本"""
        # Discuz AJAX 响应格式: <root><![CDATA[...]]></root>
        cdata_match = re.search(r'<!\[CDATA\[(.*?)\]\]>', text, re.DOTALL)
        if cdata_match:
            return cdata_match.group(1).strip()
        # 去除 HTML 标签
        clean = re.sub(r'<[^>]+>', '', text).strip()
        return clean[:200] if clean else text[:200]
