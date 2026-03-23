"""卡券和发货规则辅助函数模块

提供卡券、发货规则数据操作中的重复代码提取
"""
import json
from typing import Dict, Any, Optional, Tuple


def _parse_api_config(api_config: Any) -> Dict[str, Any]:
    """解析api_config JSON字符串

    Args:
        api_config: 原始api_config值，可能是JSON字符串或字典

    Returns:
        Dict[str, Any]: 解析后的字典，解析失败返回空字典
    """
    if api_config:
        try:
            return json.loads(api_config) if isinstance(api_config, str) else api_config
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


def _build_card_from_row(row: Tuple) -> Dict[str, Any]:
    """从数据库行构建卡券字典

    Args:
        row: 数据库查询返回的行，元组格式
             (id, name, type, api_config, text_content, data_content,
              image_url, description, enabled, delay_seconds,
              is_multi_spec, spec_name, spec_value, user_id,
              created_at, updated_at)

    Returns:
        Dict[str, Any]: 卡券数据字典
    """
    api_config = _parse_api_config(row[3])
    return {
        'id': row[0],
        'name': row[1],
        'type': row[2],
        'api_config': api_config,
        'text_content': row[4],
        'data_content': row[5],
        'image_url': row[6],
        'description': row[7],
        'enabled': bool(row[8]),
        'delay_seconds': row[9],
        'is_multi_spec': bool(row[10]) if row[10] is not None else False,
        'spec_name': row[11],
        'spec_value': row[12],
        'user_id': row[13],
        'created_at': row[14],
        'updated_at': row[15]
    }


def _build_rule_from_row(row: Tuple) -> Dict[str, Any]:
    """从数据库行构建发货规则字典（基础版本）

    Args:
        row: 数据库查询返回的行，元组格式
             (id, keyword, card_id, delivery_count, enabled,
              description, delivery_times, user_id,
              card_name, card_type)

    Returns:
        Dict[str, Any]: 发货规则数据字典
    """
    return {
        'id': row[0],
        'keyword': row[1],
        'card_id': row[2],
        'delivery_count': row[3],
        'enabled': bool(row[4]),
        'description': row[5],
        'delivery_times': row[6],
        'user_id': row[7],
        'card_name': row[8],
        'card_type': row[9]
    }


def _build_rule_with_spec_from_row(row: Tuple) -> Dict[str, Any]:
    """从数据库行构建发货规则字典（包含规格信息）

    用于get_delivery_rules_by_keyword方法

    Args:
        row: 数据库查询返回的行，元组格式
             (id, keyword, card_id, delivery_count, enabled,
              description, delivery_times,
              card_name, card_type,
              card_delay_seconds, card_description,
              is_multi_spec, spec_name, spec_value)

    Returns:
        Dict[str, Any]: 发货规则数据字典（包含卡券详细信息）
    """
    return {
        'id': row[0],
        'keyword': row[1],
        'card_id': row[2],
        'delivery_count': row[3],
        'enabled': bool(row[4]),
        'description': row[5],
        'delivery_times': row[6],
        'card_name': row[7],
        'card_type': row[8],
        'card_delay_seconds': row[9],
        'card_description': row[10],
        'is_multi_spec': bool(row[11]) if row[11] is not None else False,
        'spec_name': row[12],
        'spec_value': row[13]
    }


def _build_rule_with_spec_name_from_row(row: Tuple) -> Dict[str, Any]:
    """从数据库行构建发货规则字典（包含规格名称和值）

    用于get_delivery_rules_by_keyword_and_spec方法

    Args:
        row: 数据库查询返回的行，元组格式
             (id, keyword, card_id, delivery_count, enabled,
              description, delivery_times, user_id,
              card_name, card_type,
              spec_name, spec_value)

    Returns:
        Dict[str, Any]: 发货规则数据字典
    """
    return {
        'id': row[0],
        'keyword': row[1],
        'card_id': row[2],
        'delivery_count': row[3],
        'enabled': bool(row[4]),
        'description': row[5],
        'delivery_times': row[6],
        'user_id': row[7],
        'card_name': row[8],
        'card_type': row[9]
    }
