"""
自动机模块

负责构建和管理 Aho-Corasick 自动机，提供高效的关键词匹配能力。
"""

import re
import time
import threading
from typing import Dict, List, Any

import ahocorasick
from loguru import logger

from app.core.keyword_matcher.regex_handler import RegexHandler
from app.core.keyword_matcher.constants import (
    MATCH_TYPE_REGEX,
    MAX_REGEX_LENGTH,
    MAX_REGEX_NESTING_DEPTH,
    MAX_REGEX_QUANTIFIER_REPEAT,
)


class AutomatonBuilder:
    """自动机构建器

    负责为每个账号构建和维护独立的 Aho-Corasick 自动机。
    """

    def __init__(
        self,
        automata: Dict[str, ahocorasick.Automaton],
        keywords_cache: Dict[str, List[Dict[str, Any]]],
        regex_cache: Dict[str, Dict[str, re.Pattern]],
        lock: threading.RLock,
        stats: Dict[str, Dict[str, Any]]
    ):
        """初始化自动机构建器

        Args:
            automata: 自动机场
            keywords_cache: 关键词数据缓存
            regex_cache: 正则表达式缓存
            lock: 线程锁
            stats: 性能统计
        """
        self._automata = automata
        self._keywords_cache = keywords_cache
        self._regex_cache = regex_cache
        self._lock = lock
        self._stats = stats

    def build(
        self,
        cookie_id: str,
        keywords: List[Dict[str, Any]]
    ) -> bool:
        """构建指定账号的关键词自动机

        Args:
            cookie_id: 账号ID
            keywords: 关键词数据列表

        Returns:
            bool: 构建是否成功
        """
        if not keywords:
            logger.warning(f"账号 {cookie_id} 关键词列表为空，跳过自动机构建")
            return False

        start_time = time.perf_counter()

        with self._lock:
            try:
                automaton = ahocorasick.Automaton()
                regex_cache: Dict[str, re.Pattern] = {}

                for idx, kw_data in enumerate(keywords):
                    keyword = kw_data.get('keyword', '')
                    if not keyword:
                        continue

                    match_type = kw_data.get('match_type', 'contains')

                    if match_type == MATCH_TYPE_REGEX:
                        try:
                            is_safe, error_msg = RegexHandler.validate_regex_safety(keyword)
                            if not is_safe:
                                logger.warning(
                                    f"账号 {cookie_id} 正则表达式不安全: {keyword}, 原因: {error_msg}"
                                )
                                continue

                            compiled_pattern = re.compile(keyword, re.IGNORECASE)
                            regex_cache[keyword] = compiled_pattern
                            logger.debug(f"账号 {cookie_id} 预编译正则表达式: {keyword}")
                        except re.error as e:
                            logger.warning(
                                f"账号 {cookie_id} 正则表达式编译失败: {keyword}, 错误: {e}"
                            )
                            continue

                    keyword_lower = keyword.lower()
                    automaton.add_word(keyword_lower, (idx, kw_data))

                automaton.make_automaton()

                self._automata[cookie_id] = automaton
                self._keywords_cache[cookie_id] = keywords
                self._regex_cache[cookie_id] = regex_cache

                build_time = (time.perf_counter() - start_time) * 1000
                self._update_stats(cookie_id, 'build', build_time, len(keywords))

                logger.info(
                    f"账号 {cookie_id} 自动机构建完成: "
                    f"关键词数量={len(keywords)}, 正则数量={len(regex_cache)}, 耗时={build_time:.2f}ms"
                )

                return True

            except Exception as e:
                logger.error(f"账号 {cookie_id} 自动机构建失败: {e}")
                if cookie_id in self._automata:
                    del self._automata[cookie_id]
                if cookie_id in self._keywords_cache:
                    del self._keywords_cache[cookie_id]
                if cookie_id in self._regex_cache:
                    del self._regex_cache[cookie_id]
                return False

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
            operation: 操作类型
            time_ms: 耗时（毫秒）
            count: 数量
        """
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
