from typing import Dict, Any
from playwright.async_api import Page
from plugins.base import BasePlugin


class CustomPlugin(BasePlugin):
    """Custom plugin for user-defined sign-in logic"""

    name = "custom"
    site_type = "custom"

    async def sign_in(self, page: Page, account) -> Dict[str, Any]:
        """Custom sign-in implementation"""
        return {
            "success": False,
            "error": "Custom plugin not configured"
        }

    async def validate(self, account) -> bool:
        """Validate custom account"""
        return False
