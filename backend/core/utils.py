"""
通用工具函数。
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict


# ============================================================
#  常用时区选项列表（供前端选择）
# ============================================================
TIMEZONE_OPTIONS: List[Dict[str, str]] = [
    {"value": "Asia/Shanghai",       "label": "中国标准时间 (UTC+8)"},
    {"value": "Asia/Taipei",         "label": "台北时间 (UTC+8)"},
    {"value": "Asia/Hong_Kong",      "label": "香港时间 (UTC+8)"},
    {"value": "Asia/Singapore",      "label": "新加坡时间 (UTC+8)"},
    {"value": "Asia/Tokyo",          "label": "日本标准时间 (UTC+9)"},
    {"value": "Asia/Seoul",          "label": "韩国标准时间 (UTC+9)"},
    {"value": "Asia/Kolkata",        "label": "印度标准时间 (UTC+5:30)"},
    {"value": "Asia/Bangkok",        "label": "曼谷时间 (UTC+7)"},
    {"value": "Asia/Dubai",          "label": "迪拜时间 (UTC+4)"},
    {"value": "Europe/London",       "label": "伦敦时间 (UTC+0/+1)"},
    {"value": "Europe/Paris",       "label": "巴黎时间 (UTC+1/+2)"},
    {"value": "Europe/Berlin",       "label": "柏林时间 (UTC+1/+2)"},
    {"value": "Europe/Moscow",       "label": "莫斯科时间 (UTC+3)"},
    {"value": "America/New_York",   "label": "纽约时间 (UTC-5/-4)"},
    {"value": "America/Chicago",     "label": "芝加哥时间 (UTC-6/-5)"},
    {"value": "America/Denver",      "label": "丹佛时间 (UTC-7/-6)"},
    {"value": "America/Los_Angeles", "label": "洛杉矶时间 (UTC-8/-7)"},
    {"value": "Pacific/Auckland",    "label": "奥克兰时间 (UTC+12/+13)"},
    {"value": "Australia/Sydney",    "label": "悉尼时间 (UTC+10/+11)"},
    {"value": "UTC",                 "label": "UTC 协调世界时 (UTC+0)"},
]


def _get_tz(tz_name: str) -> timezone:
    """根据 IANA 时区名称获取 timezone 对象。

    优先使用 zoneinfo（Python 3.9+），不可用时回退到常见偏移量映射。
    """
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(tz_name)
    except ImportError:
        pass

    # 回退映射（仅覆盖常见时区）
    _offset_map = {
        "Asia/Shanghai": timedelta(hours=8),
        "Asia/Taipei": timedelta(hours=8),
        "Asia/Hong_Kong": timedelta(hours=8),
        "Asia/Singapore": timedelta(hours=8),
        "Asia/Tokyo": timedelta(hours=9),
        "Asia/Seoul": timedelta(hours=9),
        "Asia/Kolkata": timedelta(hours=5, minutes=30),
        "Asia/Bangkok": timedelta(hours=7),
        "Asia/Dubai": timedelta(hours=4),
        "Europe/London": timedelta(0),
        "Europe/Paris": timedelta(hours=1),
        "Europe/Berlin": timedelta(hours=1),
        "Europe/Moscow": timedelta(hours=3),
        "America/New_York": timedelta(hours=-5),
        "America/Chicago": timedelta(hours=-6),
        "America/Denver": timedelta(hours=-7),
        "America/Los_Angeles": timedelta(hours=-8),
        "Pacific/Auckland": timedelta(hours=12),
        "Australia/Sydney": timedelta(hours=10),
        "UTC": timedelta(0),
    }
    offset = _offset_map.get(tz_name, timedelta(hours=8))  # 默认 UTC+8
    return timezone(offset)


def to_tz_iso(value: datetime, tz_name: str = "Asia/Shanghai") -> Optional[str]:
    """将时间转换为指定时区后输出 ISO 格式字符串。

    Args:
        value: 数据库中的 datetime（通常为 UTC naive datetime）
        tz_name: IANA 时区名称，如 "Asia/Shanghai"、"America/New_York"
    """
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    tz = _get_tz(tz_name)
    return value.astimezone(tz).isoformat()


def to_tz_str(value: datetime, tz_name: str = "Asia/Shanghai", fmt: str = "%Y-%m-%d %H:%M:%S") -> Optional[str]:
    """将时间转换为指定时区后输出指定格式字符串。

    适用于 CSV 导出等需要自定义格式的场景。
    """
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    tz = _get_tz(tz_name)
    return value.astimezone(tz).strftime(fmt)


# ============ 向后兼容别名 ============
def to_beijing_iso(value: datetime) -> Optional[str]:
    """将时间统一转换为北京时间 (UTC+8) 后输出 ISO 格式字符串。"""
    return to_tz_iso(value, "Asia/Shanghai")


def to_beijing_str(value: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> Optional[str]:
    """将时间统一转换为北京时间 (UTC+8) 后输出指定格式字符串。"""
    return to_tz_str(value, "Asia/Shanghai", fmt)
