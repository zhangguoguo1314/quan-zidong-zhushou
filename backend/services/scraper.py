from core.config import settings

try:
    from playwright.async_api import async_playwright
except Exception:
    async_playwright = None


class ScraperService:
    def __init__(self):
        self.headless = settings.PLAYWRIGHT_HEADLESS

    async def sign_in(self, account, site):
        """Sign in to a site using Playwright"""
        if async_playwright is None:
            return {
                "success": False,
                "error": "Playwright 未安装或当前设备不支持。手机 Termux 可先使用 Cookie/Token 插件，复杂浏览器自动化建议部署到 Linux/Docker。"
            }

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context()

            if account.cookie:
                cookies = self._parse_cookies(account.cookie)
                await context.add_cookies(cookies)

            page = await context.new_page()

            try:
                if site.type == "openrouter":
                    result = await self._sign_in_openrouter(page, account, site)
                elif site.type == "forum":
                    result = await self._sign_in_forum(page, account, site)
                else:
                    result = await self._sign_in_custom(page, account, site)

                await context.close()
                await browser.close()
                return result

            except Exception as e:
                await browser.close()
                return {"success": False, "error": str(e)}

    async def _sign_in_openrouter(self, page, account, site):
        """Sign in to OpenRouter"""
        await page.goto(site.url or "https://openrouter.ai")
        await page.wait_for_load_state("networkidle")

        try:
            await page.click('button:has-text("Sign In")')
            await page.wait_for_selector('input[type="email"]')
            await page.fill('input[type="email"]', account.username)

            if account.password:
                await page.fill('input[type="password"]', account.password)

            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)

            cookies = await context.cookies()
            account.cookie = self._serialize_cookies(cookies)

            return {"success": True, "message": "Signed in successfully"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _sign_in_forum(self, page, account, site):
        """Sign in to forum sites"""
        await page.goto(site.url)
        await page.wait_for_load_state("networkidle")

        try:
            await page.click('a:has-text("Login"), a:has-text("Sign In"), button:has-text("Login")')
            await page.wait_for_timeout(1000)

            username_field = await page.query_selector('input[name="username"], input[name="user"]')
            if username_field:
                await username_field.fill(account.username)

            password_field = await page.query_selector('input[type="password"]')
            if password_field and account.password:
                await password_field.fill(account.password)

            submit_button = await page.query_selector('button[type="submit"]')
            if submit_button:
                await submit_button.click()

            await page.wait_for_timeout(2000)

            cookies = await page.context.cookies()
            account.cookie = self._serialize_cookies(cookies)

            return {"success": True, "message": "Signed in successfully"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _sign_in_custom(self, page, account, site):
        """Custom sign in - basic implementation"""
        return {"success": False, "error": "Custom sign-in not implemented"}

    def _parse_cookies(self, cookie_str: str):
        """Parse cookie string into list of dicts"""
        cookies = []
        for part in cookie_str.split(";"):
            part = part.strip()
            if "=" in part:
                name, value = part.split("=", 1)
                cookies.append({
                    "name": name.strip(),
                    "value": value.strip(),
                    "domain": ".example.com"
                })
        return cookies

    def _serialize_cookies(self, cookies):
        """Serialize cookies list into string"""
        return "; ".join([f"{c['name']}={c['value']}" for c in cookies])
