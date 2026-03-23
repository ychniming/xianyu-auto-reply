"""
Cookie管理器模块

管理多账号Cookie及其对应的XianyuLive任务和关键字
"""

from __future__ import annotations

import asyncio
import time
from typing import Dict, List, Optional, Tuple, Any, Union

from loguru import logger

from app.repositories import db_manager
from app.core.constants import (
    KEYWORDS_CACHE_EXPIRY,
    ASYNC_TASK_TIMEOUT,
    DEFAULT_ENABLED,
    DEFAULT_AUTO_CONFIRM,
)


class CookieManager:
    """管理多账号Cookie及其对应的XianyuLive任务和关键字

    提供线程安全的Cookie增删改查操作，支持关键字缓存和任务管理。

    Attributes:
        loop: 异步事件循环
        cookies: 账号ID到Cookie值的映射
        tasks: 账号ID到异步任务的映射
        keywords: 账号ID到关键字列表的映射
        cookie_status: 账号ID到启用状态的映射
        auto_confirm_settings: 账号ID到自动确认发货设置的映射
    """

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        """初始化Cookie管理器

        Args:
            loop: 异步事件循环
        """
        self.loop: asyncio.AbstractEventLoop = loop
        self.cookies: Dict[str, str] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        self.keywords: Dict[str, List[Tuple[str, str]]] = {}
        self.cookie_status: Dict[str, bool] = {}
        self.auto_confirm_settings: Dict[str, bool] = {}

        # Keywords cache with expiry
        self._keywords_cache: Dict[str, List[Tuple[str, str]]] = {}
        self._keywords_cache_timestamp: Dict[str, float] = {}
        self._keywords_cache_valid: Dict[str, bool] = {}

        self._load_from_db()

    def _load_from_db(self) -> None:
        """从数据库加载所有Cookie、关键字和状态"""
        try:
            # 加载所有Cookie
            self.cookies = db_manager.get_all_cookies()
            # 加载所有关键字
            self.keywords = db_manager.get_all_keywords()
            # 加载所有Cookie状态（默认启用）
            self.cookie_status = db_manager.get_all_cookie_status()
            # 加载所有auto_confirm设置
            self.auto_confirm_settings = {}
            for cookie_id in self.cookies.keys():
                # 为没有状态记录的Cookie设置默认启用状态
                if cookie_id not in self.cookie_status:
                    self.cookie_status[cookie_id] = DEFAULT_ENABLED
                # 加载auto_confirm设置
                self.auto_confirm_settings[cookie_id] = db_manager.get_auto_confirm(cookie_id)
            logger.info(
                f"从数据库加载了 {len(self.cookies)} 个Cookie、"
                f"{len(self.keywords)} 组关键字、{len(self.cookie_status)} 个状态记录和 "
                f"{len(self.auto_confirm_settings)} 个自动确认设置"
            )
        except Exception as e:
            logger.error(f"从数据库加载数据失败: {e}")

    def reload_from_db(self) -> bool:
        """重新从数据库加载所有数据（用于备份导入后刷新）

        Returns:
            bool: 加载是否成功
        """
        logger.info("重新从数据库加载数据...")
        old_cookies_count = len(self.cookies)
        old_keywords_count = len(self.keywords)

        # 重新加载数据
        self._load_from_db()

        new_cookies_count = len(self.cookies)
        new_keywords_count = len(self.keywords)

        logger.info(
            f"数据重新加载完成: Cookie {old_cookies_count} -> {new_cookies_count}, "
            f"关键字组 {old_keywords_count} -> {new_keywords_count}"
        )
        return True

    # ------------------------ 内部协程 ------------------------

    async def _run_xianyu(
        self,
        cookie_id: str,
        cookie_value: str,
        user_id: Optional[int] = None
    ) -> None:
        """在事件循环中启动XianyuLive.main

        Args:
            cookie_id: 账号ID
            cookie_value: Cookie值
            user_id: 用户ID
        """
        logger.info(f"【{cookie_id}】_run_xianyu方法开始执行...")

        try:
            logger.info(f"【{cookie_id}】正在导入XianyuLive...")
            from app.core.XianyuAutoAsync import XianyuLive  # 延迟导入，避免循环
            logger.info(f"【{cookie_id}】XianyuLive导入成功")

            logger.info(f"【{cookie_id}】开始创建XianyuLive实例...")
            logger.info(f"【{cookie_id}】Cookie值长度: {len(cookie_value)}")
            live = XianyuLive(cookie_value, cookie_id=cookie_id, user_id=user_id)
            logger.info(f"【{cookie_id}】XianyuLive实例创建成功，开始调用main()...")
            await live.main()
        except asyncio.CancelledError:
            logger.info(f"XianyuLive 任务已取消: {cookie_id}")
        except Exception as e:
            logger.error(f"XianyuLive 任务异常({cookie_id}): {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")

    async def _add_cookie_async(
        self,
        cookie_id: str,
        cookie_value: str,
        user_id: Optional[int] = None,
        save_to_db: bool = True
    ) -> None:
        """异步添加Cookie并启动任务

        Args:
            cookie_id: 账号ID
            cookie_value: Cookie值
            user_id: 用户ID
            save_to_db: 是否保存到数据库（扫码登录时已保存，传False避免重复）
        """
        if cookie_id in self.tasks:
            raise ValueError("Cookie ID already exists")
        self.cookies[cookie_id] = cookie_value

        if save_to_db:
            db_manager.save_cookie(cookie_id, cookie_value, user_id)

        if user_id is None:
            cookie_info = db_manager.get_cookie_details(cookie_id)
            if cookie_info:
                user_id = cookie_info.get("user_id")

        task = self.loop.create_task(self._run_xianyu(cookie_id, cookie_value, user_id))
        self.tasks[cookie_id] = task
        logger.info(f"已启动账号任务: {cookie_id} (用户ID: {user_id})")

    async def _remove_cookie_async(self, cookie_id: str) -> None:
        """异步移除Cookie并停止任务

        Args:
            cookie_id: 账号ID
        """
        task = self.tasks.pop(cookie_id, None)
        if task:
            task.cancel()
        self.cookies.pop(cookie_id, None)
        self.keywords.pop(cookie_id, None)
        # 从数据库删除
        db_manager.delete_cookie(cookie_id)
        logger.info(f"已移除账号: {cookie_id}")

    # ------------------------ 对外线程安全接口 ------------------------

    def add_cookie(
        self,
        cookie_id: str,
        cookie_value: str,
        kw_list: Optional[List[Tuple[str, str]]] = None,
        user_id: Optional[int] = None,
        save_to_db: bool = True
    ) -> Union[asyncio.Task, asyncio.Future]:
        """线程安全新增Cookie并启动任务

        Args:
            cookie_id: 账号ID
            cookie_value: Cookie值
            kw_list: 关键字列表，每项为(keyword, reply)元组
            user_id: 用户ID
            save_to_db: 是否保存到数据库（扫码登录时已保存，传False避免重复）

        Returns:
            asyncio.Task或asyncio.Future: 异步任务或Future对象
        """
        if kw_list is not None:
            self.keywords[cookie_id] = kw_list
        else:
            self.keywords.setdefault(cookie_id, [])
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        if current_loop and current_loop == self.loop:
            return self.loop.create_task(self._add_cookie_async(cookie_id, cookie_value, user_id, save_to_db))
        else:
            fut = asyncio.run_coroutine_threadsafe(
                self._add_cookie_async(cookie_id, cookie_value, user_id, save_to_db), self.loop
            )
            return fut.result()

    def remove_cookie(self, cookie_id: str) -> Union[asyncio.Task, asyncio.Future]:
        """线程安全移除Cookie并停止任务

        Args:
            cookie_id: 账号ID

        Returns:
            asyncio.Task或asyncio.Future: 异步任务或Future对象
        """
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        if current_loop and current_loop == self.loop:
            return self.loop.create_task(self._remove_cookie_async(cookie_id))
        else:
            fut = asyncio.run_coroutine_threadsafe(self._remove_cookie_async(cookie_id), self.loop)
            return fut.result()

    def update_cookie(self, cookie_id: str, new_value: str) -> Union[asyncio.Task, asyncio.Future]:
        """替换指定账号的Cookie并重启任务

        Args:
            cookie_id: 账号ID
            new_value: 新的Cookie值

        Returns:
            asyncio.Task或asyncio.Future: 异步任务或Future对象
        """
        async def _update() -> None:
            # 获取原有的user_id和关键词
            original_user_id: Optional[int] = None
            original_keywords: List[Tuple[str, str]] = []
            original_status: bool = DEFAULT_ENABLED

            cookie_info = db_manager.get_cookie_details(cookie_id)
            if cookie_info:
                original_user_id = cookie_info.get("user_id")

            # 保存原有的关键词和状态
            if cookie_id in self.keywords:
                original_keywords = self.keywords[cookie_id].copy()
            if cookie_id in self.cookie_status:
                original_status = self.cookie_status[cookie_id]

            # 先移除任务（但不删除数据库记录）
            task = self.tasks.pop(cookie_id, None)
            if task:
                task.cancel()

            # 更新Cookie值（保持原有user_id，不删除关键词）
            self.cookies[cookie_id] = new_value
            db_manager.save_cookie(cookie_id, new_value, original_user_id)

            # 恢复关键词和状态
            self.keywords[cookie_id] = original_keywords
            self.cookie_status[cookie_id] = original_status

            # 重新启动任务
            task = self.loop.create_task(self._run_xianyu(cookie_id, new_value, original_user_id))
            self.tasks[cookie_id] = task

            logger.info(
                f"已更新Cookie并重启任务: {cookie_id} "
                f"(用户ID: {original_user_id}, 关键词: {len(original_keywords)}条)"
            )

        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        if current_loop and current_loop == self.loop:
            return self.loop.create_task(_update())
        else:
            fut = asyncio.run_coroutine_threadsafe(_update(), self.loop)
            return fut.result()

    def update_keywords(self, cookie_id: str, kw_list: List[Tuple[str, str]]) -> None:
        """线程安全更新关键字

        Args:
            cookie_id: 账号ID
            kw_list: 关键字列表，每项为(keyword, reply)元组
        """
        self.keywords[cookie_id] = kw_list
        # 保存到数据库
        db_manager.save_keywords(cookie_id, kw_list)
        # Invalidate cache to force refresh on next access
        self.invalidate_keywords_cache(cookie_id)
        logger.info(f"更新关键字: {cookie_id} -> {len(kw_list)} 条")

    # 查询接口

    def list_cookies(self) -> List[str]:
        """获取所有Cookie账号ID列表

        Returns:
            List[str]: 账号ID列表
        """
        return list(self.cookies.keys())

    def get_keywords(self, cookie_id: str) -> List[Tuple[str, str]]:
        """获取指定账号的关键字列表

        Args:
            cookie_id: 账号ID

        Returns:
            List[Tuple[str, str]]: 关键字列表，每项为(keyword, reply)元组
        """
        return self.keywords.get(cookie_id, [])

    def get_keywords_cached(self, cookie_id: str) -> List[Tuple[str, str]]:
        """获取关键字列表（带缓存支持）

        如果缓存有效则直接返回，否则从数据库刷新。

        Args:
            cookie_id: 账号ID

        Returns:
            List[Tuple[str, str]]: 关键字列表，每项为(keyword, reply)元组
        """
        current_time = time.time()

        # Check if cache is valid
        if self._is_keywords_cache_valid(cookie_id, current_time):
            return self._keywords_cache.get(cookie_id, [])

        # Refresh cache from database
        return self._refresh_keywords_cache(cookie_id)

    def _is_keywords_cache_valid(self, cookie_id: str, current_time: float) -> bool:
        """检查关键字缓存是否有效

        Args:
            cookie_id: 账号ID
            current_time: 当前时间戳

        Returns:
            bool: 缓存是否有效
        """
        if not self._keywords_cache_valid.get(cookie_id, False):
            return False

        cache_time = self._keywords_cache_timestamp.get(cookie_id, 0)
        return (current_time - cache_time) < KEYWORDS_CACHE_EXPIRY

    def _refresh_keywords_cache(self, cookie_id: str) -> List[Tuple[str, str]]:
        """从数据库刷新关键字缓存

        Args:
            cookie_id: 账号ID

        Returns:
            List[Tuple[str, str]]: 关键字列表，每项为(keyword, reply)元组
        """
        try:
            keywords = db_manager.get_keywords(cookie_id)
            current_time = time.time()

            self._keywords_cache[cookie_id] = keywords
            self._keywords_cache_timestamp[cookie_id] = current_time
            self._keywords_cache_valid[cookie_id] = True

            # Also update the in-memory keywords dict
            self.keywords[cookie_id] = keywords

            logger.debug(f"Keywords cache refreshed for {cookie_id}: {len(keywords)} keywords")
            return keywords
        except Exception as e:
            logger.error(f"Failed to refresh keywords cache for {cookie_id}: {e}")
            return self._keywords_cache.get(cookie_id, [])

    def invalidate_keywords_cache(self, cookie_id: Optional[str] = None) -> None:
        """使关键字缓存失效

        Args:
            cookie_id: 账号ID，如果为None则使所有缓存失效
        """
        if cookie_id:
            self._keywords_cache_valid[cookie_id] = False
            logger.debug(f"Keywords cache invalidated for {cookie_id}")
        else:
            self._keywords_cache_valid.clear()
            logger.debug("All keywords caches invalidated")

    def update_cookie_status(self, cookie_id: str, enabled: bool) -> None:
        """更新Cookie的启用/禁用状态

        Args:
            cookie_id: 账号ID
            enabled: 是否启用

        Raises:
            ValueError: 如果Cookie ID不存在
        """
        if cookie_id not in self.cookies:
            raise ValueError(f"Cookie ID {cookie_id} 不存在")

        old_status = self.cookie_status.get(cookie_id, DEFAULT_ENABLED)
        self.cookie_status[cookie_id] = enabled
        # 保存到数据库
        db_manager.save_cookie_status(cookie_id, enabled)
        logger.info(f"更新Cookie状态: {cookie_id} -> {'启用' if enabled else '禁用'}")

        # 如果状态发生变化，需要启动或停止任务
        if old_status != enabled:
            if enabled:
                # 启用账号：启动任务
                self._start_cookie_task(cookie_id)
            else:
                # 禁用账号：停止任务
                self._stop_cookie_task(cookie_id)

    def get_cookie_status(self, cookie_id: str) -> bool:
        """获取Cookie的启用状态

        Args:
            cookie_id: 账号ID

        Returns:
            bool: 是否启用
        """
        return self.cookie_status.get(cookie_id, DEFAULT_ENABLED)

    def get_enabled_cookies(self) -> Dict[str, str]:
        """获取所有启用的Cookie

        Returns:
            Dict[str, str]: 启用的Cookie字典，键为账号ID，值为Cookie值
        """
        return {
            cid: value
            for cid, value in self.cookies.items()
            if self.cookie_status.get(cid, DEFAULT_ENABLED)
        }

    def _start_cookie_task(self, cookie_id: str) -> None:
        """启动指定Cookie的任务

        Args:
            cookie_id: 账号ID
        """
        if cookie_id in self.tasks:
            logger.warning(f"Cookie任务已存在，跳过启动: {cookie_id}")
            return

        cookie_value = self.cookies.get(cookie_id)
        if not cookie_value:
            logger.error(f"Cookie值不存在，无法启动任务: {cookie_id}")
            return

        try:
            # 获取Cookie对应的user_id
            cookie_info = db_manager.get_cookie_details(cookie_id)
            user_id = cookie_info.get("user_id") if cookie_info else None

            # 使用异步方式启动任务
            if hasattr(self.loop, "is_running") and self.loop.is_running():
                # 事件循环正在运行，使用run_coroutine_threadsafe
                fut = asyncio.run_coroutine_threadsafe(
                    self._add_cookie_async(cookie_id, cookie_value, user_id),
                    self.loop
                )
                fut.result(timeout=ASYNC_TASK_TIMEOUT)
            else:
                # 事件循环未运行，直接创建任务
                task = self.loop.create_task(self._run_xianyu(cookie_id, cookie_value, user_id))
                self.tasks[cookie_id] = task

            logger.info(f"成功启动Cookie任务: {cookie_id}")
        except Exception as e:
            logger.error(f"启动Cookie任务失败: {cookie_id}, {e}")

    def _stop_cookie_task(self, cookie_id: str) -> None:
        """停止指定Cookie的任务

        Args:
            cookie_id: 账号ID
        """
        if cookie_id not in self.tasks:
            logger.warning(f"Cookie任务不存在，跳过停止: {cookie_id}")
            return

        try:
            task = self.tasks[cookie_id]
            if not task.done():
                task.cancel()
                logger.info(f"已取消Cookie任务: {cookie_id}")
            del self.tasks[cookie_id]
            logger.info(f"成功停止Cookie任务: {cookie_id}")
        except Exception as e:
            logger.error(f"停止Cookie任务失败: {cookie_id}, {e}")

    def update_auto_confirm_setting(self, cookie_id: str, auto_confirm: bool) -> None:
        """实时更新账号的自动确认发货设置

        Args:
            cookie_id: 账号ID
            auto_confirm: 是否开启自动确认发货
        """
        try:
            # 更新内存中的设置
            self.auto_confirm_settings[cookie_id] = auto_confirm
            logger.info(
                f"更新账号 {cookie_id} 自动确认发货设置: {'开启' if auto_confirm else '关闭'}"
            )

            # 如果账号正在运行，通知XianyuLive实例更新设置
            if cookie_id in self.tasks and not self.tasks[cookie_id].done():
                # 这里可以通过某种方式通知正在运行的XianyuLive实例
                # 由于XianyuLive会从数据库读取设置，所以数据库已经更新就足够了
                logger.info(f"账号 {cookie_id} 正在运行，自动确认发货设置已实时生效")
        except Exception as e:
            logger.error(f"更新自动确认发货设置失败: {cookie_id}, {e}")

    def get_auto_confirm_setting(self, cookie_id: str) -> bool:
        """获取账号的自动确认发货设置

        Args:
            cookie_id: 账号ID

        Returns:
            bool: 是否开启自动确认发货
        """
        return self.auto_confirm_settings.get(cookie_id, DEFAULT_AUTO_CONFIRM)


# 在 Start.py 中会把此变量赋值为具体实例
manager: Optional[CookieManager] = None
