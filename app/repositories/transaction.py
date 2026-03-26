"""事务管理模块

提供数据库事务管理功能，包括上下文管理器和装饰器
"""
import functools
import threading
from contextlib import contextmanager
from typing import Optional, Callable, Any, Generator
from loguru import logger


class TransactionManager:
    """事务管理器

    管理数据库事务的生命周期，支持嵌套事务
    """

    def __init__(self, db_manager):
        """初始化事务管理器

        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager
        # 使用线程本地存储跟踪嵌套事务深度
        self._local = threading.local()

    def _get_depth(self) -> int:
        """获取当前线程的事务嵌套深度"""
        return getattr(self._local, 'depth', 0)

    def _set_depth(self, depth: int) -> None:
        """设置当前线程的事务嵌套深度"""
        self._local.depth = depth

    def _get_savepoint_name(self) -> str:
        """生成保存点名称"""
        depth = self._get_depth()
        return f"savepoint_{depth}"

    def begin_transaction(self) -> None:
        """开始事务

        如果已经在事务中，则创建保存点
        """
        with self.db_manager.lock:
            depth = self._get_depth()

            if depth == 0:
                # 开始新事务
                cursor = self.db_manager.conn.cursor()
                cursor.execute("BEGIN")
                logger.debug("开始新事务")
            else:
                # 创建保存点支持嵌套事务
                savepoint_name = self._get_savepoint_name()
                cursor = self.db_manager.conn.cursor()
                cursor.execute(f"SAVEPOINT {savepoint_name}")
                logger.debug(f"创建保存点: {savepoint_name}")

            self._set_depth(depth + 1)

    def commit(self) -> None:
        """提交事务

        如果在嵌套事务中，则释放保存点
        """
        with self.db_manager.lock:
            depth = self._get_depth()

            if depth <= 0:
                logger.warning("没有活动的事务可以提交")
                return

            if depth == 1:
                # 提交最外层事务
                self.db_manager.conn.commit()
                logger.debug("提交事务")
            else:
                # 释放保存点
                savepoint_name = f"savepoint_{depth - 1}"
                cursor = self.db_manager.conn.cursor()
                cursor.execute(f"RELEASE SAVEPOINT {savepoint_name}")
                logger.debug(f"释放保存点: {savepoint_name}")

            self._set_depth(depth - 1)

    def rollback(self) -> None:
        """回滚事务

        如果在嵌套事务中，则回滚到保存点
        """
        with self.db_manager.lock:
            depth = self._get_depth()

            if depth <= 0:
                logger.warning("没有活动的事务可以回滚")
                return

            if depth == 1:
                # 回滚整个事务
                self.db_manager.conn.rollback()
                logger.debug("回滚事务")
            else:
                # 回滚到保存点
                savepoint_name = f"savepoint_{depth - 1}"
                cursor = self.db_manager.conn.cursor()
                cursor.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                logger.debug(f"回滚到保存点: {savepoint_name}")

            self._set_depth(depth - 1)

    @contextmanager
    def with_transaction(self) -> Generator[None, None, None]:
        """事务上下文管理器

        自动管理事务的开始、提交和回滚

        Yields:
            None

        Example:
            with transaction_manager.with_transaction():
                db_manager.save_cookie(...)
                db_manager.save_keywords(...)
        """
        self.begin_transaction()
        try:
            yield
            self.commit()
        except Exception as e:
            logger.error(f"事务执行失败，正在回滚: {e}")
            self.rollback()
            raise


def transactional(func: Callable) -> Callable:
    """事务装饰器

    为函数自动包装事务，支持同步和异步函数

    Args:
        func: 要包装的函数

    Returns:
        包装后的函数

    Example:
        @transactional
        def save_data():
            db_manager.save_cookie(...)
            db_manager.save_keywords(...)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        """同步函数包装器"""
        # 从参数中获取 db_manager
        # 优先从 self 获取（如果是方法）
        db_manager = None
        if args and hasattr(args[0], 'db_manager'):
            db_manager = args[0].db_manager
        elif args and hasattr(args[0], 'conn'):
            db_manager = args[0]
        else:
            # 尝试从 kwargs 获取
            db_manager = kwargs.get('db_manager')

        if db_manager is None:
            logger.warning("无法获取数据库管理器，跳过事务包装")
            return func(*args, **kwargs)

        # 创建事务管理器
        tx_manager = TransactionManager(db_manager)

        # 在事务中执行函数
        with tx_manager.with_transaction():
            return func(*args, **kwargs)

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        """异步函数包装器"""
        # 从参数中获取 db_manager
        db_manager = None
        if args and hasattr(args[0], 'db_manager'):
            db_manager = args[0].db_manager
        elif args and hasattr(args[0], 'conn'):
            db_manager = args[0]
        else:
            db_manager = kwargs.get('db_manager')

        if db_manager is None:
            logger.warning("无法获取数据库管理器，跳过事务包装")
            return await func(*args, **kwargs)

        # 创建事务管理器
        tx_manager = TransactionManager(db_manager)

        # 在事务中执行函数
        with tx_manager.with_transaction():
            return await func(*args, **kwargs)

    # 根据函数类型返回对应的包装器
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return wrapper


def with_transaction_decorator(db_manager_getter: Callable = None) -> Callable:
    """带参数的事务装饰器工厂

    Args:
        db_manager_getter: 获取 db_manager 的函数，默认从第一个参数获取

    Returns:
        装饰器函数

    Example:
        @with_transaction_decorator(lambda self: self.db_manager)
        def save_data(self):
            self.db_manager.save_cookie(...)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 获取 db_manager
            if db_manager_getter:
                db_manager = db_manager_getter(*args, **kwargs)
            elif args and hasattr(args[0], 'db_manager'):
                db_manager = args[0].db_manager
            elif args and hasattr(args[0], 'conn'):
                db_manager = args[0]
            else:
                db_manager = kwargs.get('db_manager')

            if db_manager is None:
                logger.warning("无法获取数据库管理器，跳过事务包装")
                return func(*args, **kwargs)

            # 创建事务管理器
            tx_manager = TransactionManager(db_manager)

            # 在事务中执行函数
            with tx_manager.with_transaction():
                return func(*args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # 获取 db_manager
            if db_manager_getter:
                db_manager = db_manager_getter(*args, **kwargs)
            elif args and hasattr(args[0], 'db_manager'):
                db_manager = args[0].db_manager
            elif args and hasattr(args[0], 'conn'):
                db_manager = args[0]
            else:
                db_manager = kwargs.get('db_manager')

            if db_manager is None:
                logger.warning("无法获取数据库管理器，跳过事务包装")
                return await func(*args, **kwargs)

            # 创建事务管理器
            tx_manager = TransactionManager(db_manager)

            # 在事务中执行函数
            with tx_manager.with_transaction():
                return await func(*args, **kwargs)

        # 根据函数类型返回对应的包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper

    return decorator
