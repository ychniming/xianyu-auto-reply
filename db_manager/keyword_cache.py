"""Keyword缓存管理模块

提供关键词匹配器缓存的刷新和管理功能
"""
from typing import List, Dict, Any, TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from .keyword_repo import KeywordRepository

# 延迟导入，避免循环依赖
_keyword_matcher = None


def _get_keyword_matcher():
    """获取关键词匹配器单例（延迟导入）

    Returns:
        keyword_matcher: 关键词匹配器实例
    """
    global _keyword_matcher
    if _keyword_matcher is None:
        from src.keyword_matcher import keyword_matcher
        _keyword_matcher = keyword_matcher
    return _keyword_matcher


class KeywordCacheManager:
    """关键词缓存管理器

    负责刷新和管理关键词匹配器缓存
    """

    def __init__(self, repository: 'KeywordRepository'):
        """初始化缓存管理器

        Args:
            repository: KeywordRepository实例引用
        """
        self._repo = repository
        self._db = repository._db
        self.conn = repository.conn
        self.lock = repository.lock

    def _get_keywords_with_type_unlocked(self, cookie_id: str) -> List[Dict[str, Any]]:
        """获取指定Cookie的关键字列表（包含类型信息）- 不加锁版本

        仅供在已持有锁的方法内部调用，避免重复加锁。

        Args:
            cookie_id: 账号ID

        Returns:
            List[Dict[str, Any]]: 关键词列表
        """
        try:
            cursor = self.conn.cursor()
            self._db._execute_sql(cursor,
                """SELECT keyword, reply, item_id, type, image_url,
                          priority, reply_mode, replies, sequence_index, conditions
                   FROM keywords WHERE cookie_id = ?""",
                (cookie_id,)
            )

            results = []
            for row in cursor.fetchall():
                keyword_data = {
                    'keyword': row[0],
                    'reply': row[1],
                    'item_id': row[2],
                    'type': row[3] or 'text',
                    'image_url': row[4],
                    'priority': row[5] if row[5] is not None else 0,
                    'reply_mode': row[6] or 'single',
                    'replies': row[7],
                    'sequence_index': row[8] if row[8] is not None else 0,
                    'conditions': row[9],
                }
                results.append(keyword_data)

            return results
        except Exception as e:
            logger.error(f"获取关键字失败: {e}")
            return []

    def refresh_cache_unlocked(self, cookie_id: str) -> bool:
        """刷新关键词匹配器缓存 - 不在锁内调用

        当关键词发生变更时调用此方法，重建对应账号的自动机。
        此方法会获取锁，不应在已持有锁的上下文中调用。

        Args:
            cookie_id: 账号ID

        Returns:
            bool: 刷新是否成功
        """
        with self.lock:
            return self._refresh_cache_locked(cookie_id)

    def _refresh_cache_locked(self, cookie_id: str) -> bool:
        """刷新关键词匹配器缓存 - 在锁内调用

        当关键词发生变更时调用此方法，重建对应账号的自动机。
        此方法不加锁，必须在已持有锁的上下文中调用。

        Args:
            cookie_id: 账号ID

        Returns:
            bool: 刷新是否成功
        """
        try:
            matcher = _get_keyword_matcher()
            if matcher is None:
                logger.warning("关键词匹配器未初始化，跳过缓存刷新")
                return False

            # 获取该账号的所有关键词（包含类型信息）- 使用不加锁版本
            keywords = self._get_keywords_with_type_unlocked(cookie_id)

            if keywords:
                # 重建自动机
                success = matcher.rebuild(cookie_id, keywords)
                if success:
                    logger.info(f"关键词缓存刷新成功: {cookie_id}, 关键词数量: {len(keywords)}")
                else:
                    logger.warning(f"关键词缓存刷新失败: {cookie_id}")
                return success
            else:
                # 没有关键词，清除缓存
                matcher.clear(cookie_id)
                logger.info(f"关键词缓存已清除: {cookie_id}（无关键词）")
                return True

        except Exception as e:
            logger.error(f"刷新关键词缓存失败: {cookie_id}, 错误: {e}")
            return False

    def clear_cache(self, cookie_id: str) -> bool:
        """清除指定账号的关键词缓存

        Args:
            cookie_id: 账号ID

        Returns:
            bool: 清除是否成功
        """
        try:
            matcher = _get_keyword_matcher()
            if matcher is None:
                logger.warning("关键词匹配器未初始化，跳过缓存清除")
                return False

            matcher.clear(cookie_id)
            logger.info(f"关键词缓存已清除: {cookie_id}")
            return True

        except Exception as e:
            logger.error(f"清除关键词缓存失败: {cookie_id}, 错误: {e}")
            return False

    def rebuild_cache(self, cookie_id: str, keywords: List[Dict[str, Any]]) -> bool:
        """手动重建指定账号的关键词缓存

        Args:
            cookie_id: 账号ID
            keywords: 关键词列表

        Returns:
            bool: 重建是否成功
        """
        try:
            matcher = _get_keyword_matcher()
            if matcher is None:
                logger.warning("关键词匹配器未初始化，跳过缓存重建")
                return False

            if keywords:
                success = matcher.rebuild(cookie_id, keywords)
                if success:
                    logger.info(f"关键词缓存重建成功: {cookie_id}, 关键词数量: {len(keywords)}")
                else:
                    logger.warning(f"关键词缓存重建失败: {cookie_id}")
                return success
            else:
                matcher.clear(cookie_id)
                logger.info(f"关键词缓存重建成功: {cookie_id}（无关键词）")
                return True

        except Exception as e:
            logger.error(f"重建关键词缓存失败: {cookie_id}, 错误: {e}")
            return False
