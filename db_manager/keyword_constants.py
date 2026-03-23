"""Keyword常量定义模块

提供关键词相关的常量、验证规则和类型定义
"""
from typing import Set, Dict, Any

# 有效的匹配类型
VALID_MATCH_TYPES: Set[str] = {'contains', 'exact', 'regex', 'prefix', 'suffix', 'fuzzy'}

# 有效的关键词类型
VALID_KEYWORD_TYPES: Set[str] = {'text', 'image'}

# 有效的回复模式
VALID_REPLY_MODES: Set[str] = {'single', 'random', 'sequential'}

# 优先级范围
MIN_PRIORITY: int = 0
MAX_PRIORITY: int = 100
DEFAULT_PRIORITY: int = 0

# 默认值
DEFAULT_MATCH_TYPE: str = 'contains'
DEFAULT_KEYWORD_TYPE: str = 'text'
DEFAULT_REPLY_MODE: str = 'single'
DEFAULT_SEQUENCE_INDEX: int = 0
DEFAULT_TRIGGER_COUNT: int = 0


def validate_match_type(match_type: str) -> bool:
    """验证匹配类型是否有效

    Args:
        match_type: 匹配类型字符串

    Returns:
        bool: 是否有效
    """
    return match_type in VALID_MATCH_TYPES


def validate_priority(priority: int) -> bool:
    """验证优先级是否在有效范围内

    Args:
        priority: 优先级值

    Returns:
        bool: 是否有效
    """
    return isinstance(priority, int) and MIN_PRIORITY <= priority <= MAX_PRIORITY


def validate_reply_mode(reply_mode: str) -> bool:
    """验证回复模式是否有效

    Args:
        reply_mode: 回复模式字符串

    Returns:
        bool: 是否有效
    """
    return reply_mode in VALID_REPLY_MODES


def normalize_match_type(match_type: str) -> str:
    """规范化匹配类型，无效时返回默认值

    Args:
        match_type: 匹配类型字符串

    Returns:
        str: 有效则返回原值，否则返回默认值
    """
    if match_type not in VALID_MATCH_TYPES:
        return DEFAULT_MATCH_TYPE
    return match_type


def normalize_priority(priority: Any) -> int:
    """规范化优先级，无效时返回默认值

    Args:
        priority: 优先级值

    Returns:
        int: 有效则返回原值，否则返回默认值
    """
    if not validate_priority(priority):
        return DEFAULT_PRIORITY
    return priority


def build_keyword_data(row: tuple) -> Dict[str, Any]:
    """从数据库行构建关键词数据字典

    Args:
        row: 数据库查询返回的元组，包含:
            0: keyword, 1: reply, 2: item_id, 3: type,
            4: image_url, 5: match_type, 6: priority,
            7: reply_mode, 8: replies, 9: sequence_index,
            10: trigger_count, 11: conditions

    Returns:
        Dict[str, Any]: 关键词数据字典
    """
    return {
        'keyword': row[0],
        'reply': row[1],
        'item_id': row[2],
        'type': row[3] or DEFAULT_KEYWORD_TYPE,
        'image_url': row[4],
        'match_type': row[5] or DEFAULT_MATCH_TYPE,
        'priority': row[6] if row[6] is not None else DEFAULT_PRIORITY,
        'reply_mode': row[7] or DEFAULT_REPLY_MODE,
        'replies': row[8],
        'sequence_index': row[9] if row[9] is not None else DEFAULT_SEQUENCE_INDEX,
        'trigger_count': row[10] if row[10] is not None else DEFAULT_TRIGGER_COUNT,
        'conditions': row[11],
    }


def build_keyword_data_short(row: tuple) -> Dict[str, Any]:
    """从数据库行构建关键词数据字典（简短版本，用于基础查询）

    Args:
        row: 数据库查询返回的元组，包含:
            0: keyword, 1: reply, 2: item_id, 3: type,
            4: image_url, 5: priority, 6: reply_mode,
            7: replies, 8: sequence_index, 9: conditions

    Returns:
        Dict[str, Any]: 关键词数据字典
    """
    return {
        'keyword': row[0],
        'reply': row[1],
        'item_id': row[2],
        'type': row[3] or DEFAULT_KEYWORD_TYPE,
        'image_url': row[4],
        'priority': row[5] if row[5] is not None else DEFAULT_PRIORITY,
        'reply_mode': row[6] or DEFAULT_REPLY_MODE,
        'replies': row[7],
        'sequence_index': row[8] if row[8] is not None else DEFAULT_SEQUENCE_INDEX,
        'conditions': row[9],
    }
