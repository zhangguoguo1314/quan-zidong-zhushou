"""
通用工具函数。
"""
from datetime import datetime, timezone, timedelta
from typing import Optional


def to_beijing_iso(value: datetime) -> Optional[str]:
    """将时间统一转换为北京时间 (UTC+8) 后输出 ISO 格式字符串。

    适用于路由中手动构造字典返回时，统一时间格式。
    """
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    beijing_tz = timezone(timedelta(hours=8))
    return value.astimezone(beijing_tz).isoformat()


def to_beijing_str(value: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> Optional[str]:
    """将时间统一转换为北京时间 (UTC+8) 后输出指定格式字符串。

    适用于 CSV 导出等需要自定义格式的场景。
    """
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    beijing_tz = timezone(timedelta(hours=8))
    return value.astimezone(beijing_tz).strftime(fmt)
