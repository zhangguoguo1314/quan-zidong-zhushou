from typing import Dict, Any
from playwright.async_api import Page
from plugins.base import BasePlugin


class ForumPlugin(BasePlugin):
    """Generic forum sign-in plugin"""

    name = "forum"
    site_type = "forum"

    async def sign_in(self, page: Page, account) -> Dict[str, Any]:
        """Sign in to forum"""
        try:
            await page.goto(page.context.browser._parent._url or account.site.url)
            await page.wait_for_load_state("networkidle")

            login_selectors = [
                'a:has-text("Login")',
                'a:has-text("Sign In")',
                'button:has-text("Login")',
                'a:has-text("Log In")'
            ]

            for selector in login_selectors:
                element = await page.query_selector(selector)
                if element:
                    await element.click()
                    break

            await page.wait_for_timeout(1000)

            username_field = await page.query_selector(
                'input[name="username"], input[name="user"], input[id="username"]'
            )
            if username_field:
                await username_field.fill(account.username)

            password_field = await page.query_selector('input[type="password"]')
            if password_field and account.password:
                await password_field.fill(account.password)

            submit_button = await page.query_selector(
                'button[type="submit"], input[type="submit"]'
            )
            if submit_button:
                await submit_button.click()

            await page.wait_for_timeout(2000)

            cookies = await page.context.cookies()
            account.cookie = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

            return {"success": True, "message": "Signed in to forum successfully"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def validate(self, account) -> bool:
        """Validate forum account"""
        return bool(account.username)
