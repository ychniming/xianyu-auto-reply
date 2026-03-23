"""
正则表达式处理模块

负责正则表达式的安全性验证和匹配操作。
"""

import re
import threading
from typing import Dict, Tuple

from loguru import logger

from app.core.keyword_matcher.constants import (
    REGEX_TIMEOUT,
    MAX_REGEX_LENGTH,
    MAX_REGEX_NESTING_DEPTH,
    MAX_REGEX_QUANTIFIER_REPEAT,
)


class RegexHandler:
    """正则表达式处理器

    提供正则表达式的安全性验证和匹配功能，支持超时保护。
    """

    @staticmethod
    def validate_regex_safety(pattern: str) -> Tuple[bool, str]:
        """验证正则表达式的安全性

        检查正则表达式是否存在DoS攻击风险，包括：
        1. 长度限制
        2. 嵌套深度检查
        3. 重复量词检查

        Args:
            pattern: 正则表达式模式

        Returns:
            Tuple[bool, str]: (是否安全, 错误消息)
        """
        if len(pattern) > MAX_REGEX_LENGTH:
            return False, f"正则表达式过长（{len(pattern)}字符），最大允许{MAX_REGEX_LENGTH}字符"

        depth = 0
        max_depth = 0
        for char in pattern:
            if char == '(':
                depth += 1
                max_depth = max(max_depth, depth)
            elif char == ')':
                depth -= 1

        if max_depth > MAX_REGEX_NESTING_DEPTH:
            return False, f"正则表达式嵌套深度过深（{max_depth}层），最大允许{MAX_REGEX_NESTING_DEPTH}层"

        quantifier_pattern = re.compile(r'\{(\d+),?(\d*)\}')
        for match in quantifier_pattern.finditer(pattern):
            min_repeat = int(match.group(1))
            max_repeat = int(match.group(2)) if match.group(2) else min_repeat

            if min_repeat > MAX_REGEX_QUANTIFIER_REPEAT or max_repeat > MAX_REGEX_QUANTIFIER_REPEAT:
                return False, f"正则表达式重复次数过大（{match.group(0)}），最大允许{MAX_REGEX_QUANTIFIER_REPEAT}次"

        dangerous_patterns = [
            r'\([^)]*\)\s*[\*\+]',
            r'\([^)]*\)\s*\{',
        ]

        for dangerous in dangerous_patterns:
            if re.search(dangerous, pattern):
                return False, "正则表达式包含危险的回溯模式，可能导致性能问题"

        return True, ""

    @staticmethod
    def match(
        message: str,
        keyword: str,
        regex_cache: Dict[str, re.Pattern]
    ) -> bool:
        """正则匹配（带超时保护）

        Args:
            message: 消息内容
            keyword: 正则表达式模式
            regex_cache: 正则表达式缓存

        Returns:
            bool: 是否匹配成功
        """
        compiled_pattern = regex_cache.get(keyword)
        if not compiled_pattern:
            try:
                compiled_pattern = re.compile(keyword, re.IGNORECASE)
            except re.error as e:
                logger.warning(f"正则表达式编译失败: {keyword}, 错误: {e}")
                return False

        try:
            result = [False]
            exception = [None]

            def _match():
                try:
                    result[0] = compiled_pattern.search(message) is not None
                except Exception as e:
                    exception[0] = e

            thread = threading.Thread(target=_match)
            thread.start()
            thread.join(timeout=REGEX_TIMEOUT)

            if thread.is_alive():
                logger.warning(f"正则匹配超时（>{REGEX_TIMEOUT}秒）: {keyword}")
                return False

            if exception[0]:
                logger.warning(f"正则匹配异常: {keyword}, 错误: {exception[0]}")
                return False

            return result[0]

        except Exception as e:
            logger.warning(f"正则匹配失败: {keyword}, 错误: {e}")
            return False
