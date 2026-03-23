"""中间件配置模块

提供FastAPI应用的中间件配置
"""
import time
import asyncio
from typing import Callable
from fastapi import FastAPI, Request
from starlette.responses import Response

from app.utils.logging_config import (
    set_trace_id, set_request_id, generate_trace_id
)
from .limiter import limiter


def setup_middleware(app: FastAPI) -> None:
    """配置应用中间件

    Args:
        app: FastAPI应用实例
    """
    from .metrics import setup_metrics

    setup_metrics(app)

    app.middleware("http")(http_middleware)


async def http_middleware(request: Request, call_next: Callable) -> Response:
    """HTTP请求日志中间件

    Args:
        request: HTTP请求
        call_next: 下一个处理器

    Returns:
        HTTP响应
    """
    from loguru import logger
    from app.repositories import db_manager

    start_time = time.time()

    trace_id = generate_trace_id()
    set_trace_id(trace_id)
    set_request_id(trace_id)

    user_info = "未登录"
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            token_data = db_manager.get_session(token)
            if token_data:
                user_info = f"【{token_data['username']}#{token_data['user_id']}】"
    except Exception:
        pass

    logger.info(f"API请求: {request.method} {request.url.path} [trace:{trace_id}]")

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(f"API响应: {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s) [trace:{trace_id}]")

    response.headers["X-Trace-Id"] = trace_id

    return response


async def periodic_cleanup_sessions() -> None:
    """定期清理过期会话的后台任务"""
    from loguru import logger
    from app.repositories import db_manager

    while True:
        try:
            await asyncio.sleep(3600)
            cleaned = db_manager.cleanup_expired_sessions()
            if cleaned > 0:
                logger.info(f"定期清理了 {cleaned} 个过期会话")
        except Exception as e:
            logger.error(f"定期清理会话失败: {e}")


def create_startup_handler(static_dir: str):
    """创建启动事件处理器

    Args:
        static_dir: 静态文件目录
    """
    async def startup_event() -> None:
        from loguru import logger
        import os
        from app.repositories import db_manager

        if not os.path.exists(static_dir):
            os.makedirs(static_dir, exist_ok=True)

        uploads_dir = os.path.join(static_dir, 'uploads', 'images')
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir, exist_ok=True)
            logger.info(f"创建图片上传目录: {uploads_dir}")

        cleaned = db_manager.cleanup_expired_sessions()
        if cleaned > 0:
            logger.info(f"启动时清理了 {cleaned} 个过期会话")

        asyncio.create_task(periodic_cleanup_sessions())

    return startup_event


__all__ = [
    'setup_middleware',
    'http_middleware',
    'periodic_cleanup_sessions',
    'create_startup_handler',
]
