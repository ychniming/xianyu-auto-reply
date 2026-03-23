"""
闲鱼自动回复系统 - 商品管理模块
负责商品信息获取、保存、批量处理等功能
使用组合模式整合缓存、数据库和API模块
"""

from typing import Dict, Any, Optional

from app.services.xianyu.item_cache import ItemCache
from app.services.xianyu.item_db import ItemDBManager
from app.services.xianyu.item_api import ItemAPI


class ItemManager:
    """商品管理器 - 负责商品信息获取和管理

    使用组合模式整合：
    - ItemCache: 缓存管理
    - ItemDBManager: 数据库操作
    - ItemAPI: API调用
    """

    def __init__(self, parent):
        """初始化商品管理器

        Args:
            parent: XianyuLive实例，用于访问共享属性
        """
        self.parent = parent

        self.item_cache = ItemCache()
        self.item_db = ItemDBManager(parent)
        self.item_api = ItemAPI(parent)

    def get_item_info_cached(self, item_id: str) -> Optional[dict]:
        """获取缓存的商品信息

        Args:
            item_id: 商品ID

        Returns:
            Optional[dict]: 缓存的商品信息
        """
        return self.item_cache.get_item_info_cached(item_id)

    def set_item_info_cache(self, item_id: str, info: dict) -> None:
        """设置商品信息到缓存

        Args:
            item_id: 商品ID
            info: 商品信息字典
        """
        self.item_cache.set_item_info_cache(item_id, info)

    def invalidate_item_cache(self, item_id: str = None) -> None:
        """使缓存失效

        Args:
            item_id: 商品ID。如果为None，则使所有缓存失效。
        """
        self.item_cache.invalidate_item_cache(item_id)

    async def save_item_info_to_db(self, item_id: str, item_detail: str = None, item_title: str = None) -> None:
        """保存商品信息到数据库

        Args:
            item_id: 商品ID
            item_detail: 商品详情
            item_title: 商品标题
        """
        await self.item_db.save_item_info_to_db(item_id, item_detail, item_title)

    async def save_item_detail_only(self, item_id: str, item_detail: str) -> bool:
        """仅保存商品详情

        Args:
            item_id: 商品ID
            item_detail: 商品详情

        Returns:
            bool: 保存是否成功
        """
        return await self.item_db.save_item_detail_only(item_id, item_detail)

    async def fetch_item_detail_from_api(self, item_id: str) -> str:
        """从外部API获取商品详情

        Args:
            item_id: 商品ID

        Returns:
            str: 商品详情文本
        """
        return await self.item_db.fetch_item_detail_from_api(item_id)

    async def save_items_list_to_db(self, items_list):
        """批量保存商品列表信息到数据库

        Args:
            items_list: 商品列表

        Returns:
            int: 保存成功的数量
        """
        return await self.item_db.save_items_list_to_db(items_list)

    async def get_item_info(self, item_id: str, retry_count: int = 0) -> Dict[str, Any]:
        """获取商品信息，自动处理token失效的情况

        优先使用缓存，如果缓存无效则调用API

        Args:
            item_id: 商品ID
            retry_count: 重试次数

        Returns:
            Dict[str, Any]: 商品信息
        """
        if retry_count == 0:
            cached_info = self.item_cache.get_item_info_cached(item_id)
            if cached_info:
                return cached_info

        item_info = await self.item_api.get_item_info(item_id, retry_count)

        if isinstance(item_info, dict) and 'error' not in item_info:
            self.item_cache.set_item_info_cache(item_id, item_info)

        return item_info

    async def get_item_list_info(self, page_number: int = 1, page_size: int = 20, retry_count: int = 0) -> Dict[str, Any]:
        """获取商品列表信息

        Args:
            page_number: 页码
            page_size: 每页数量
            retry_count: 重试次数

        Returns:
            Dict[str, Any]: 商品列表信息
        """
        return await self.item_api.get_item_list_info(page_number, page_size, retry_count)

    async def get_all_items(self, page_size: int = 20, max_pages: int = None) -> Dict[str, Any]:
        """获取所有商品信息（自动分页）

        Args:
            page_size: 每页数量
            max_pages: 最大页数

        Returns:
            Dict[str, Any]: 所有商品信息
        """
        return await self.item_api.get_all_items(page_size, max_pages)
