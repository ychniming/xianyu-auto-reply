"""
闲鱼自动回复系统 - 发货验证模块
负责验证发货内容的合法性
"""

import re
from typing import Optional, Tuple
from loguru import logger


class DeliveryValidator:
    """发货内容验证器"""

    MAX_DELIVERY_CONTENT_LENGTH = 5000

    def __init__(self, parent):
        self.parent = parent

    def _validate_delivery_content(self, content: str) -> Tuple[bool, Optional[str]]:
        """验证发货内容

        Args:
            content: 要验证的发货内容

        Returns:
            Tuple[bool, Optional[str]]: (是否验证通过, 错误信息)
        """
        if not content or not content.strip():
            return False, "发货内容不能为空或仅包含空白字符"

        if len(content) > self.MAX_DELIVERY_CONTENT_LENGTH:
            return False, f"发货内容长度超过限制: {len(content)} > {self.MAX_DELIVERY_CONTENT_LENGTH} 字符"

        if hasattr(self.parent, '_mask_sensitive'):
            sensitive_patterns = [
                (r'[a-zA-Z0-9_-]{20,}', "可能的API密钥或Token"),
                (r'password[=:]\s*\S+', "密码信息"),
                (r'passwd[=:]\s*\S+', "密码信息"),
                (r'pwd[=:]\s*\S+', "密码信息"),
                (r'secret[=:]\s*\S+', "密钥信息"),
                (r'private[_-]?key[=:]\s*\S+', "私钥信息"),
                (r'cookie[=:]\s*\S+', "Cookie信息"),
                (r'session[=:]\s*\S+', "Session信息"),
            ]

            for pattern, desc in sensitive_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    masked_content = self.parent._mask_sensitive(content, 10, 10)
                    logger.warning(f"发货内容可能包含{desc}，已脱敏处理: {masked_content}")
                    return True, None

        return True, None

    def _is_auto_delivery_trigger(self, message: str) -> bool:
        """检查消息是否为自动发货触发关键字

        Args:
            message: 消息内容

        Returns:
            bool: 是否为触发关键字
        """
        auto_delivery_keywords = [
            '[我已付款，等待你发货]',
            '[已付款，待发货]',
            '我已付款，等待你发货',
            '[记得及时发货]',
        ]

        for keyword in auto_delivery_keywords:
            if keyword in message:
                return True

        return False
