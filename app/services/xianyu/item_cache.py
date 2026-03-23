"""
闲鱼自动回复系统 - 商品缓存模块
负责商品信息的缓存管理，使用LRU策略
"""

import time
from typing import Dict, Optional, Tuple, List
from loguru import logger


class ItemCache:
    """商品缓存管理器 - 使用LRU策略"""

    CACHE_EXPIRY = 300
    MAX_CACHE_SIZE = 100

    def __init__(self):
        self._item_cache: Dict[str, Tuple[dict, float]] = {}
        self._cache_access_order: List[str] = []

    def get_item_info_cached(self, item_id: str) -> Optional[dict]:
        """获取缓存的商品信息

        Args:
            item_id: 商品ID

        Returns:
            Optional[dict]: 缓存的商品信息，如果缓存有效则返回，否则返回None
        """
        if item_id in self._item_cache:
            info, timestamp = self._item_cache[item_id]
            if time.time() - timestamp < self.CACHE_EXPIRY:
                self._update_lru_order(item_id)
                return info
            else:
                self._remove_from_cache(item_id)
        return None

    def set_item_info_cache(self, item_id: str, info: dict) -> None:
        """设置商品信息到缓存

        Args:
            item_id: 商品ID
            info: 商品信息字典
        """
        current_time = time.time()

        if len(self._item_cache) >= self.MAX_CACHE_SIZE and item_id not in self._item_cache:
            self._evict_lru()

        self._item_cache[item_id] = (info, current_time)
        self._update_lru_order(item_id)
        logger.debug(f"Item info cached: {item_id}")

    def invalidate_item_cache(self, item_id: str = None) -> None:
        """使缓存失效

        Args:
            item_id: 商品ID。如果为None，则使所有缓存失效。
        """
        if item_id:
            self._remove_from_cache(item_id)
            logger.debug(f"Item cache invalidated: {item_id}")
        else:
            self._item_cache.clear()
            self._cache_access_order.clear()
            logger.debug("All item caches invalidated")

    def _update_lru_order(self, item_id: str) -> None:
        """更新LRU访问顺序

        Args:
            item_id: 被访问的商品ID
        """
        if item_id in self._cache_access_order:
            self._cache_access_order.remove(item_id)
        self._cache_access_order.append(item_id)

    def _remove_from_cache(self, item_id: str) -> None:
        """从缓存中移除商品

        Args:
            item_id: 要移除的商品ID
        """
        if item_id in self._item_cache:
            del self._item_cache[item_id]
        if item_id in self._cache_access_order:
            self._cache_access_order.remove(item_id)

    def _evict_lru(self) -> None:
        """驱逐最久未使用的缓存项"""
        if self._cache_access_order:
            lru_item_id = self._cache_access_order.pop(0)
            if lru_item_id in self._item_cache:
                del self._item_cache[lru_item_id]
                logger.debug(f"LRU cache eviction: {lru_item_id}")

    def get_cache_stats(self) -> dict:
        """获取缓存统计信息

        Returns:
            dict: 缓存统计信息
        """
        return {
            'size': len(self._item_cache),
            'max_size': self.MAX_CACHE_SIZE,
            'expiry_seconds': self.CACHE_EXPIRY
        }
