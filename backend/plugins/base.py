from abc import ABC, abstractmethod
from typing import Dict, Any


class BasePlugin(ABC):
    """Base class for all sign-in plugins"""

    name: str = "base"
    site_type: str = "base"

    @abstractmethod
    async def sign_in(self, page, account) -> Dict[str, Any]:
        """Perform sign-in action"""
        pass

    @abstractmethod
    async def validate(self, account) -> bool:
        """Validate account configuration"""
        pass

    async def before_sign_in(self, page):
        """Hook before sign-in"""
        pass

    async def after_sign_in(self, page):
        """Hook after sign-in"""
        pass
