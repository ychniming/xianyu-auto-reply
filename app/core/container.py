"""依赖注入容器模块

提供统一的服务实例管理，支持单例模式、线程安全和 FastAPI 依赖注入。
"""

import threading
from typing import Any, Callable, Dict, Optional, TypeVar, Generic
from functools import lru_cache

from fastapi import Depends

from loguru import logger


T = TypeVar('T')


class ServiceContainer:
    """服务容器 - 单例模式管理服务实例

    提供线程安全的服务实例存储和获取，支持服务工厂函数注册。

    Attributes:
        _instance: 单例实例
        _lock: 线程锁
        _services: 服务实例字典
        _factories: 服务工厂函数字典
    """

    _instance: Optional['ServiceContainer'] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> 'ServiceContainer':
        """创建单例实例

        Returns:
            ServiceContainer: 服务容器实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._services: Dict[str, Any] = {}
                    cls._instance._factories: Dict[str, Callable] = {}
                    logger.info("服务容器初始化完成")
        return cls._instance

    def register(self, name: str, instance: Any) -> None:
        """注册服务实例

        Args:
            name: 服务名称
            instance: 服务实例
        """
        with self._lock:
            self._services[name] = instance
            logger.debug(f"服务实例已注册: {name}")

    def register_factory(self, name: str, factory: Callable[[], Any]) -> None:
        """注册服务工厂函数

        Args:
            name: 服务名称
            factory: 服务工厂函数，无参数，返回服务实例
        """
        with self._lock:
            self._factories[name] = factory
            logger.debug(f"服务工厂已注册: {name}")

    def get(self, name: str) -> Optional[Any]:
        """获取服务实例

        优先从已注册的实例中获取，如果没有则尝试使用工厂函数创建。

        Args:
            name: 服务名称

        Returns:
            服务实例，如果不存在则返回 None
        """
        # 先尝试从实例缓存获取
        if name in self._services:
            return self._services[name]

        # 尝试使用工厂函数创建
        with self._lock:
            if name in self._factories:
                factory = self._factories[name]
                instance = factory()
                self._services[name] = instance
                logger.debug(f"通过工厂函数创建服务实例: {name}")
                return instance

        logger.warning(f"服务实例不存在: {name}")
        return None

    def remove(self, name: str) -> bool:
        """移除服务实例

        Args:
            name: 服务名称

        Returns:
            bool: 是否成功移除
        """
        with self._lock:
            if name in self._services:
                del self._services[name]
                logger.debug(f"服务实例已移除: {name}")
                return True
            if name in self._factories:
                del self._factories[name]
                logger.debug(f"服务工厂已移除: {name}")
                return True
        return False

    def clear(self) -> None:
        """清空所有服务实例和工厂"""
        with self._lock:
            self._services.clear()
            self._factories.clear()
            logger.info("所有服务实例已清空")

    def list_services(self) -> Dict[str, str]:
        """列出所有已注册的服务

        Returns:
            Dict[str, str]: 服务名称到类型的映射
        """
        with self._lock:
            result = {}
            for name, instance in self._services.items():
                result[name] = type(instance).__name__
            for name in self._factories:
                if name not in result:
                    result[name] = "Factory"
            return result


# 全局服务容器实例
_container: Optional[ServiceContainer] = None
_container_lock: threading.Lock = threading.Lock()


def get_container() -> ServiceContainer:
    """获取全局服务容器实例

    Returns:
        ServiceContainer: 服务容器实例
    """
    global _container
    if _container is None:
        with _container_lock:
            if _container is None:
                _container = ServiceContainer()
    return _container


# ==================== 数据库管理器依赖 ====================

@lru_cache(maxsize=1)
def _get_db_manager_instance():
    """获取数据库管理器实例（带缓存）

    Returns:
        DBManager: 数据库管理器实例
    """
    from app.repositories import db_manager
    return db_manager


def get_db_manager():
    """获取数据库管理器依赖

    用于 FastAPI 依赖注入。

    Returns:
        DBManager: 数据库管理器实例

    Example:
        @app.get("/api/users")
        async def get_users(db = Depends(get_db_manager)):
            return db.get_all_users()
    """
    return _get_db_manager_instance()


# ==================== Cookie 管理器依赖 ====================

def get_cookie_manager():
    """获取 Cookie 管理器依赖

    用于 FastAPI 依赖注入。

    Returns:
        CookieManager: Cookie 管理器实例

    Example:
        @app.get("/api/cookies")
        async def list_cookies(manager = Depends(get_cookie_manager)):
            return manager.list_cookies()
    """
    from app.core.cookie_manager import manager
    if manager is None:
        raise RuntimeError(
            "CookieManager 未初始化，请确保在 Start.py 中正确初始化"
        )
    return manager


# ==================== AI 回复引擎依赖 ====================

@lru_cache(maxsize=1)
def _get_ai_reply_engine_instance():
    """获取 AI 回复引擎实例（带缓存）

    Returns:
        AIReplyEngine: AI 回复引擎实例
    """
    from app.core.ai_reply_engine import ai_reply_engine
    return ai_reply_engine


def get_ai_reply_engine():
    """获取 AI 回复引擎依赖

    用于 FastAPI 依赖注入。

    Returns:
        AIReplyEngine: AI 回复引擎实例

    Example:
        @app.post("/api/ai/reply")
        async def generate_reply(
            message: str,
            engine = Depends(get_ai_reply_engine)
        ):
            return engine.generate_reply(message, ...)
    """
    return _get_ai_reply_engine_instance()


# ==================== 关键词匹配器依赖 ====================

@lru_cache(maxsize=1)
def _get_keyword_matcher_instance():
    """获取关键词匹配器实例（带缓存）

    Returns:
        KeywordMatcher: 关键词匹配器实例
    """
    from app.core.keyword_matcher import keyword_matcher
    return keyword_matcher


def get_keyword_matcher():
    """获取关键词匹配器依赖

    用于 FastAPI 依赖注入。

    Returns:
        KeywordMatcher: 关键词匹配器实例

    Example:
        @app.post("/api/keywords/match")
        async def match_keyword(
            message: str,
            matcher = Depends(get_keyword_matcher)
        ):
            return matcher.match(cookie_id, message)
    """
    return _get_keyword_matcher_instance()


# ==================== 便捷函数 ====================

def init_services() -> None:
    """初始化所有服务实例

    在应用启动时调用，确保所有服务实例已创建并注册到容器中。
    """
    container = get_container()

    # 注册数据库管理器
    db = get_db_manager()
    container.register('db_manager', db)

    # 注册 AI 回复引擎
    ai_engine = get_ai_reply_engine()
    container.register('ai_reply_engine', ai_engine)

    # 注册关键词匹配器
    matcher = get_keyword_matcher()
    container.register('keyword_matcher', matcher)

    # Cookie 管理器需要异步初始化，注册工厂函数
    container.register_factory(
        'cookie_manager',
        lambda: get_cookie_manager()
    )

    logger.info("所有服务实例初始化完成")


def get_service(name: str) -> Optional[Any]:
    """获取服务实例的便捷函数

    Args:
        name: 服务名称

    Returns:
        服务实例
    """
    container = get_container()
    return container.get(name)


# ==================== 导出 ====================

__all__ = [
    # 容器类
    'ServiceContainer',
    'get_container',

    # 依赖注入函数
    'get_db_manager',
    'get_cookie_manager',
    'get_ai_reply_engine',
    'get_keyword_matcher',

    # 便捷函数
    'init_services',
    'get_service',
]
