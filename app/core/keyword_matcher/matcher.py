"""
匹配器核心模块

包含关键词匹配器的主逻辑，负责协调各个子模块完成匹配功能。
"""

import re
import time
import threading
from typing import Dict, List, Optional, Tuple, Any, Callable

from loguru import logger

from app.core.keyword_matcher.constants import (
    MATCH_TYPE_EXACT,
    MATCH_TYPE_CONTAINS,
    MATCH_TYPE_PREFIX,
    MATCH_TYPE_SUFFIX,
    MATCH_TYPE_REGEX,
    MATCH_TYPE_FUZZY,
    DEFAULT_FUZZY_THRESHOLD,
    MAX_MESSAGE_LENGTH,
    MATCH_TYPE_CONTAINS as DEFAULT_MATCH_TYPE,
)
from app.core.keyword_matcher.automaton import AutomatonBuilder
from app.core.keyword_matcher.regex_handler import RegexHandler
from app.core.keyword_matcher.fuzzy_handler import FuzzyHandler
from app.core.keyword_matcher.selector import Selector
from app.core.keyword_matcher.variables import VariablesHandler


class KeywordMatcher:
    """关键词匹配器 - 使用 Aho-Corasick 算法实现高效匹配

    特性：
    - 使用 Aho-Corasick 自动机实现 O(n) 时间复杂度的多模式匹配
    - 支持多账号独立缓存，每个账号维护独立的自动机
    - 线程安全，支持并发访问
    - 支持热更新，关键词变更时自动重建自动机
    - 支持图片类型关键词
    - 支持变量替换功能
    - 支持多种匹配类型：exact, contains, prefix, suffix, regex, fuzzy
    """

    def __init__(
        self,
        fuzzy_threshold: int = DEFAULT_FUZZY_THRESHOLD,
        sequence_index_updater: Optional[Callable] = None,
        trigger_count_updater: Optional[Callable] = None
    ):
        """初始化关键词匹配器

        Args:
            fuzzy_threshold: 模糊匹配的相似度阈值（0-100），默认80
            sequence_index_updater: 顺序回复索引更新回调函数
                签名: (cookie_id: str, keyword: str, item_id: Optional[str], new_index: int) -> bool
            trigger_count_updater: 触发次数更新回调函数
                签名: (cookie_id: str, keyword: str, item_id: Optional[str]) -> bool
        """
        self._automata: Dict[str, Any] = {}
        self._keywords_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = threading.RLock()
        self._stats: Dict[str, Dict[str, Any]] = {}
        self._regex_cache: Dict[str, Dict[str, re.Pattern]] = {}

        self._fuzzy_threshold = fuzzy_threshold
        self._sequence_index_updater = sequence_index_updater
        self._trigger_count_updater = trigger_count_updater

        # 初始化子模块
        self._automaton_builder = AutomatonBuilder(
            self._automata,
            self._keywords_cache,
            self._regex_cache,
            self._lock,
            self._stats
        )
        self._fuzzy_handler = FuzzyHandler(fuzzy_threshold)
        self._selector = Selector(
            sequence_index_updater,
            trigger_count_updater
        )
        self._variables_handler = VariablesHandler()

        logger.info(f"关键词匹配器初始化完成，模糊匹配阈值={fuzzy_threshold}")

    def build_automaton(self, cookie_id: str, keywords: List[Dict[str, Any]]) -> bool:
        """构建指定账号的关键词自动机

        Args:
            cookie_id: 账号ID
            keywords: 关键词数据列表，每个元素包含:
                - keyword: str, 关键词
                - reply: str, 回复内容
                - item_id: str, 商品ID（可选）
                - type: str, text/image
                - image_url: str, 图片URL
                - match_type: str, 匹配类型（exact/contains/prefix/suffix/regex/fuzzy）
                - fuzzy_threshold: int, 模糊匹配阈值（仅fuzzy类型有效）

        Returns:
            bool: 构建是否成功
        """
        return self._automaton_builder.build(cookie_id, keywords)

    def match(
        self,
        cookie_id: str,
        message: str,
        item_id: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """在消息中匹配关键词

        匹配优先级：
        1. 如果指定了商品ID，优先匹配该商品的关键词
        2. 如果商品ID匹配失败，匹配通用关键词（无商品ID）

        Args:
            cookie_id: 账号ID
            message: 待匹配的消息内容
            item_id: 商品ID（可选），用于优先匹配特定商品的关键词
            variables: 变量替换字典，如 {'用户名': '张三', '商品名': '测试商品'}
            context: 规则引擎上下文，包含时间、用户、商品、关键词等信息
                结构示例:
                {
                    'time': {'hour': 14, 'minute': 30, 'weekday': 3, 'timestamp': 1234567890},
                    'user': {'id': 'user123', 'is_new': True, 'purchase_count': 0, 'message_count': 1},
                    'item': {'id': 'item456', 'price': 99.0, 'category': '数码'},
                    'keyword': {'trigger_count': 5, 'message': '你好'}
                }

        Returns:
            Optional[Dict]: 匹配结果，包含:
                - keyword: str, 匹配的关键词
                - reply: str, 回复内容（已替换变量）
                - item_id: str, 商品ID
                - type: str, text/image
                - image_url: str, 图片URL
                - position: Tuple[int, int], 匹配位置 (start, end)
            如果没有匹配则返回 None
        """
        if not message or not message.strip():
            return None

        original_length = len(message)
        if original_length > MAX_MESSAGE_LENGTH:
            message = message[:MAX_MESSAGE_LENGTH]
            logger.warning(
                f"账号 {cookie_id} 消息过长({original_length}字符)，"
                f"已截断至{MAX_MESSAGE_LENGTH}字符进行匹配"
            )

        start_time = time.perf_counter()

        try:
            with self._lock:
                automaton = self._automata.get(cookie_id)
                keywords_cache = self._keywords_cache.get(cookie_id, [])
                regex_cache = self._regex_cache.get(cookie_id, {})

            if not automaton:
                logger.debug(f"账号 {cookie_id} 没有可用的自动机")
                return None

            message_lower = message.lower()

            matches = self._collect_matches(
                automaton, message, message_lower, keywords_cache, regex_cache, item_id
            )

            if not matches:
                self._update_stats(cookie_id, 'match_miss', 0, 0)
                return None

            result = self._selector.select_best(matches, item_id, cookie_id, context)

            if result:
                result = self._variables_handler.apply(result, variables or {})
                match_time = (time.perf_counter() - start_time) * 1000
                self._update_stats(cookie_id, 'match_hit', match_time, 1)

                logger.info(
                    f"账号 {cookie_id} 关键词匹配成功: "
                    f"关键词='{result['keyword']}', 类型={result.get('match_type')}, "
                    f"位置={result['position']}, 耗时={match_time:.2f}ms"
                )

                if cookie_id and self._trigger_count_updater:
                    try:
                        self._trigger_count_updater(
                            cookie_id,
                            result.get('keyword', ''),
                            result.get('item_id')
                        )
                    except Exception as e:
                        logger.error(f"更新触发次数失败: {e}")

                return result

            return None

        except Exception as e:
            logger.error(f"账号 {cookie_id} 关键词匹配失败: {e}")
            return None

    def _collect_matches(
        self,
        automaton: Any,
        message: str,
        message_lower: str,
        keywords_cache: List[Dict[str, Any]],
        regex_cache: Dict[str, re.Pattern],
        item_id: Optional[str]
    ) -> List[Tuple[int, int, Dict[str, Any]]]:
        """收集所有匹配结果

        Args:
            automaton: Aho-Corasick 自动机
            message: 原始消息
            message_lower: 小写消息
            keywords_cache: 关键词缓存
            regex_cache: 正则表达式缓存
            item_id: 商品ID

        Returns:
            List[Tuple[int, int, Dict[str, Any]]]: 匹配结果列表
        """
        matches: List[Tuple[int, int, Dict[str, Any]]] = []

        for end_pos, (idx, kw_data) in automaton.iter(message_lower):
            keyword = kw_data.get('keyword', '')
            start_pos = end_pos - len(keyword) + 1
            match_type = kw_data.get('match_type', DEFAULT_MATCH_TYPE)

            if self._verify_match(message, message_lower, keyword, match_type,
                                   kw_data, regex_cache, start_pos, end_pos):
                matches.append((start_pos, end_pos, kw_data))

        for kw_data in keywords_cache:
            match_type = kw_data.get('match_type', DEFAULT_MATCH_TYPE)

            if match_type not in (MATCH_TYPE_REGEX, MATCH_TYPE_FUZZY):
                continue

            keyword = kw_data.get('keyword', '')
            if not keyword:
                continue

            already_matched = any(
                m[2].get('keyword') == keyword and m[2].get('match_type') == match_type
                for m in matches
            )
            if already_matched:
                continue

            if match_type == MATCH_TYPE_REGEX:
                if RegexHandler.match(message, keyword, regex_cache):
                    matches.append((0, 0, kw_data))
            elif match_type == MATCH_TYPE_FUZZY:
                if self._fuzzy_handler.match(message, keyword, kw_data):
                    matches.append((0, 0, kw_data))

        for kw_data in keywords_cache:
            keyword = kw_data.get('keyword', '')
            match_type = kw_data.get('match_type', DEFAULT_MATCH_TYPE)

            if match_type != MATCH_TYPE_CONTAINS:
                continue

            if not keyword:
                continue

            keyword_lower = keyword.lower()
            keyword_len = len(keyword_lower)

            pos = message_lower.find(keyword_lower)
            while pos != -1:
                start_pos = pos
                end_pos = pos + keyword_len - 1

                already_exists = any(
                    m[0] == start_pos and m[2].get('keyword') == keyword and m[2].get('item_id') == kw_data.get('item_id')
                    for m in matches
                )

                if not already_exists:
                    matches.append((start_pos, end_pos, kw_data))

                pos = message_lower.find(keyword_lower, pos + 1)

        return matches

    def _verify_match(
        self,
        message: str,
        message_lower: str,
        keyword: str,
        match_type: str,
        kw_data: Dict[str, Any],
        regex_cache: Dict[str, re.Pattern],
        start_pos: int,
        end_pos: int
    ) -> bool:
        """根据匹配类型验证是否真正匹配

        Args:
            message: 原始消息
            message_lower: 小写消息
            keyword: 关键词
            match_type: 匹配类型
            kw_data: 关键词数据
            regex_cache: 正则表达式缓存
            start_pos: 起始位置
            end_pos: 结束位置

        Returns:
            bool: 是否匹配成功
        """
        keyword_lower = keyword.lower()

        if match_type == MATCH_TYPE_EXACT:
            return message_lower == keyword_lower
        elif match_type == MATCH_TYPE_CONTAINS:
            return True
        elif match_type == MATCH_TYPE_PREFIX:
            return message_lower.startswith(keyword_lower)
        elif match_type == MATCH_TYPE_SUFFIX:
            return message_lower.endswith(keyword_lower)
        elif match_type == MATCH_TYPE_REGEX:
            return RegexHandler.match(message, keyword, regex_cache)
        elif match_type == MATCH_TYPE_FUZZY:
            return self._fuzzy_handler.match(message, keyword, kw_data)
        else:
            logger.warning(f"未知的匹配类型: {match_type}，使用包含匹配")
            return True

    def rebuild(self, cookie_id: str, keywords: List[Dict[str, Any]]) -> bool:
        """热更新：重建指定账号的关键词自动机

        Args:
            cookie_id: 账号ID
            keywords: 新的关键词数据列表

        Returns:
            bool: 重建是否成功
        """
        logger.info(f"开始热更新账号 {cookie_id} 的关键词自动机")
        self.clear(cookie_id)
        return self.build_automaton(cookie_id, keywords)

    def clear(self, cookie_id: str) -> bool:
        """清除指定账号的自动机和缓存

        Args:
            cookie_id: 账号ID

        Returns:
            bool: 清除是否成功
        """
        try:
            with self._lock:
                if cookie_id in self._automata:
                    del self._automata[cookie_id]
                if cookie_id in self._keywords_cache:
                    del self._keywords_cache[cookie_id]
                if cookie_id in self._regex_cache:
                    del self._regex_cache[cookie_id]
                if cookie_id in self._stats:
                    del self._stats[cookie_id]

            logger.info(f"已清除账号 {cookie_id} 的关键词自动机和缓存")
            return True

        except Exception as e:
            logger.error(f"清除账号 {cookie_id} 的自动机失败: {e}")
            return False

    def clear_all(self) -> bool:
        """清除所有账号的自动机和缓存

        Returns:
            bool: 清除是否成功
        """
        try:
            with self._lock:
                self._automata.clear()
                self._keywords_cache.clear()
                self._regex_cache.clear()
                self._stats.clear()

            logger.info("已清除所有账号的关键词自动机和缓存")
            return True

        except Exception as e:
            logger.error(f"清除所有自动机失败: {e}")
            return False

    def get_stats(self, cookie_id: Optional[str] = None) -> Dict[str, Any]:
        """获取性能统计信息

        Args:
            cookie_id: 账号ID，如果为 None 则返回所有账号的统计

        Returns:
            Dict: 统计信息
        """
        with self._lock:
            if cookie_id:
                return self._stats.get(cookie_id, {})
            return dict(self._stats)

    def _update_stats(
        self,
        cookie_id: str,
        operation: str,
        time_ms: float,
        count: int
    ) -> None:
        """更新性能统计

        Args:
            cookie_id: 账号ID
            operation: 操作类型 (build/match_hit/match_miss)
            time_ms: 耗时（毫秒）
            count: 数量
        """
        with self._lock:
            if cookie_id not in self._stats:
                self._stats[cookie_id] = {
                    'build_count': 0,
                    'build_time_ms': 0,
                    'match_hit_count': 0,
                    'match_hit_time_ms': 0,
                    'match_miss_count': 0,
                    'keyword_count': 0,
                }

            stats = self._stats[cookie_id]

            if operation == 'build':
                stats['build_count'] += 1
                stats['build_time_ms'] += time_ms
                stats['keyword_count'] = count
            elif operation == 'match_hit':
                stats['match_hit_count'] += 1
                stats['match_hit_time_ms'] += time_ms
            elif operation == 'match_miss':
                stats['match_miss_count'] += 1

    def has_automaton(self, cookie_id: str) -> bool:
        """检查指定账号是否有可用的自动机

        Args:
            cookie_id: 账号ID

        Returns:
            bool: 是否存在自动机
        """
        with self._lock:
            return cookie_id in self._automata

    def get_keyword_count(self, cookie_id: str) -> int:
        """获取指定账号的关键词数量

        Args:
            cookie_id: 账号ID

        Returns:
            int: 关键词数量
        """
        with self._lock:
            return len(self._keywords_cache.get(cookie_id, []))

    def get_cached_keywords(self, cookie_id: str) -> List[Dict[str, Any]]:
        """获取指定账号的缓存关键词数据

        Args:
            cookie_id: 账号ID

        Returns:
            List[Dict]: 关键词数据列表的副本
        """
        with self._lock:
            return [kw.copy() for kw in self._keywords_cache.get(cookie_id, [])]

    def set_sequence_index_updater(self, updater: Optional[Callable]) -> None:
        """设置顺序回复索引更新回调函数

        Args:
            updater: 回调函数，签名为 (cookie_id: str, keyword: str, item_id: Optional[str], new_index: int) -> bool
        """
        self._sequence_index_updater = updater
        self._selector.set_sequence_index_updater(updater)
        logger.info("已设置顺序回复索引更新回调函数")

    def set_trigger_count_updater(self, updater: Optional[Callable]) -> None:
        """设置触发次数更新回调函数

        Args:
            updater: 回调函数，签名为 (cookie_id: str, keyword: str, item_id: Optional[str]) -> bool
        """
        self._trigger_count_updater = updater
        self._selector.set_trigger_count_updater(updater)
        logger.info("已设置触发次数更新回调函数")
