# -*- coding: utf-8 -*-
"""Common utilities for xianyu modules"""


def safe_str(e: Exception) -> str:
    """Safely convert exception to string
    
    Args:
        e: Exception instance
        
    Returns:
        str: Safe string representation of the exception
    """
    try:
        return str(e)
    except Exception:
        try:
            return repr(e)
        except Exception:
            return "Unknown error"


SYSTEM_MESSAGE_PATTERNS = [
    '[我已拍下，待付款]',
    '[你关闭了订单，钱款已原路退返]',
    '发来一条消息',
    '发来一条新消息',
    '[买家确认收货，交易成功]',
    '快给ta一个评价吧~',
    '快给ta一个评价吧～',
    '卖家人不错？送Ta闲鱼小红花',
    '[你已确认收货，交易成功]',
    '[你已发货]'
]
