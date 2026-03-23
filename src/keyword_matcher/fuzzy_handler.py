"""
模糊匹配模块

负责使用 rapidfuzz 库进行模糊匹配，支持相似度计算和阈值判断。
"""

from typing import Dict, Any

from loguru import logger

from src.keyword_matcher.constants import DEFAULT_FUZZY_THRESHOLD

# 尝试导入 rapidfuzz
try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    logger.warning("rapidfuzz 未安装，模糊匹配功能将不可用")


class FuzzyHandler:
    """模糊匹配处理器

    使用 rapidfuzz 库实现模糊匹配功能，支持相似度计算。
    """

    def __init__(self, fuzzy_threshold: int = DEFAULT_FUZZY_THRESHOLD):
        """初始化模糊匹配处理器

        Args:
            fuzzy_threshold: 默认模糊匹配阈值（0-100）
        """
        self._fuzzy_threshold = fuzzy_threshold

    def match(
        self,
        message: str,
        keyword: str,
        kw_data: Dict[str, Any]
    ) -> bool:
        """模糊匹配

        Args:
            message: 消息内容
            keyword: 关键词
            kw_data: 关键词数据

        Returns:
            bool: 相似度是否超过阈值
        """
        if not RAPIDFUZZ_AVAILABLE:
            logger.warning("rapidfuzz 未安装，无法进行模糊匹配")
            return False

        try:
            threshold = kw_data.get('fuzzy_threshold', self._fuzzy_threshold)

            similarity = fuzz.partial_ratio(message.lower(), keyword.lower())

            if similarity >= threshold:
                logger.debug(
                    f"模糊匹配成功: 关键词='{keyword}', 相似度={similarity}%, 阈值={threshold}%"
                )
                return True

            return False

        except Exception as e:
            logger.warning(f"模糊匹配失败: {keyword}, 错误: {e}")
            return False
