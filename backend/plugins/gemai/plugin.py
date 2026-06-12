from typing import Dict, Any
import json
import urllib.request
import urllib.parse
import http.cookiejar
import ssl


class GemaiPlugin:
    """Plugin for 哈基米API站 sign-in via API"""

    name = "gemai"
    site_type = "gemai"

    async def sign_in(self, account, site=None) -> Dict[str, Any]:
        """
        哈基米API站签到流程：
        1. POST /api/user/login - 登录获取 session cookie
        2. POST /api/user/checkin - 签到
        """
        try:
            username = account.username
            password = account.password

            if not username or not password:
                return {"success": False, "error": "用户名或密码未设置"}

            # 创建一个支持 cookie 的 opener
            cookie_jar = http.cookiejar.CookieJar()
            cookie_handler = urllib.request.HTTPCookieProcessor(cookie_jar)

            # 创建不验证SSL的 context（因为有时会有问题）
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            https_handler = urllib.request.HTTPSHandler(context=ssl_context)
            opener = urllib.request.build_opener(cookie_handler, https_handler)

            # Step 1: 登录获取 session cookie
            login_url = "https://api.gemai.cc/api/user/login"
            login_data = json.dumps({
                "username": username,
                "password": password
            }).encode('utf-8')

            login_req = urllib.request.Request(
                login_url,
                data=login_data,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                method='POST'
            )

            try:
                with opener.open(login_req, timeout=30) as response:
                    login_response = json.loads(response.read().decode('utf-8'))
            except Exception as e:
                return {"success": False, "error": f"登录请求失败: {str(e)}"}

            if not login_response.get("success"):
                return {
                    "success": False,
                    "error": login_response.get("message", "登录失败")
                }

            # 获取用户ID
            user_id = login_response.get("data", {}).get("id")
            if not user_id:
                return {"success": False, "error": "获取用户信息失败"}

            # Step 2: 签到
            checkin_url = "https://api.gemai.cc/api/user/checkin"

            checkin_req = urllib.request.Request(
                checkin_url,
                data=b'{}',
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'New-Api-User': str(user_id)
                },
                method='POST'
            )

            try:
                with opener.open(checkin_req, timeout=30) as response:
                    checkin_response = json.loads(response.read().decode('utf-8'))
            except Exception as e:
                return {"success": False, "error": f"签到请求失败: {str(e)}"}

            if checkin_response.get("success"):
                return {"success": True, "message": "签到成功"}
            else:
                message = checkin_response.get("message", "签到失败")
                # "今日已签到" = 今天已经签过了也算成功
                if "已签到" in message or "already" in message.lower():
                    return {"success": True, "message": message}
                return {"success": False, "error": message}

        except Exception as e:
            return {"success": False, "error": f"签到异常: {str(e)}"}

    async def validate(self, account) -> bool:
        """验证账号配置"""
        return bool(account.username and account.password)

    def is_api_mode(self) -> bool:
        """是否为纯API模式，不需要浏览器"""
        return True
