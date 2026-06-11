from typing import Dict, Any
from playwright.async_api import Page
from plugins.base import BasePlugin


class OpenRouterPlugin(BasePlugin):
    """Plugin for OpenRouter sign-in"""

    name = "openrouter"
    site_type = "openrouter"

    async def sign_in(self, page: Page, account) -> Dict[str, Any]:
        """Sign in to OpenRouter"""
        try:
            await page.goto("https://openrouter.ai/auth/login")
            await page.wait_for_load_state("networkidle")

            await page.fill('input[type="email"]', account.username)

            if account.password:
                await page.fill('input[type="password"]', account.password)

            await page.click('button[type="submit"]')
            await page.wait_for_timeout(3000)

            cookies = await page.context.cookies()
            account.cookie = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

            return {"success": True, "message": "Signed in to OpenRouter successfully"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def validate(self, account) -> bool:
        """Validate OpenRouter account"""
        return bool(account.username)
