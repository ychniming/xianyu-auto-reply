"""Reply Server路由模块

FastAPI应用主模块，组合所有路由
"""
import os
import time
import asyncio
import uuid
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, UploadFile, File, APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

from loguru import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .limiter import limiter
from .middleware import setup_middleware, create_startup_handler
from .metrics import setup_metrics, REQUEST_COUNT, REQUEST_LATENCY, ACTIVE_REQUESTS
from .models import RequestModel, ResponseData, ResponseModel
from .helpers import read_html_file
from .dependencies import require_auth

from .routes import auth, cookies, keywords, cards, items, settings, admin


limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])


def match_reply(cookie_id: str, message: str) -> Optional[str]:
    """根据 cookie_id 及消息内容匹配回复

    Args:
        cookie_id: Cookie账号ID
        message: 用户发送的消息

    Returns:
        Optional[str]: 匹配的回复内容，未匹配返回None
    """
    from app.core import cookie_manager
    mgr = cookie_manager.manager
    if mgr is None:
        return None

    if not mgr.get_cookie_status(cookie_id):
        return None

    if mgr.get_keywords(cookie_id):
        for k, r in mgr.get_keywords(cookie_id):
            if k in message:
                return r

    return None


def get_user_log_prefix(user_info: Dict[str, Any] = None) -> str:
    """获取用户日志前缀

    Args:
        user_info: 用户信息字典

    Returns:
        str: 日志前缀字符串
    """
    if user_info:
        return f"【{user_info['username']}#{user_info['user_id']}】"
    return "【系统】"


def log_with_user(level: str, message: str, user_info: Dict[str, Any] = None) -> None:
    """带用户信息的日志记录

    Args:
        level: 日志级别 (info/error/warning/debug)
        message: 日志消息
        user_info: 用户信息字典
    """
    prefix = get_user_log_prefix(user_info)
    full_message = f"{prefix} {message}"

    log_func = getattr(logger, level.lower(), logger.info)
    log_func(full_message)


def create_app() -> FastAPI:
    """创建并配置FastAPI应用

    Returns:
        FastAPI: 配置好的FastAPI应用实例
    """
    app = FastAPI(
        title="Xianyu Auto Reply API",
        version="1.0.0",
        description="闲鱼自动回复系统API",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    setup_middleware(app)
    logger.info("Rate limiting middleware initialized: 100 requests/minute default limit")

    # 获取项目根目录
    project_root = Path(__file__).parent.parent.parent
    static_dir = str(project_root / 'static')

    backup_router = APIRouter(prefix="", tags=["备份"])

    app.include_router(auth.router)
    app.include_router(cookies.router)
    app.include_router(keywords.router)
    app.include_router(cards.router)
    app.include_router(items.router)
    app.include_router(settings.router)
    app.include_router(admin.router)
    app.include_router(backup_router)

    pages_router = _create_pages_router(static_dir)
    app.include_router(pages_router)

    app.add_event_handler("startup", create_startup_handler(static_dir))

    _register_api_routes(app)

    logger.info("Application setup complete")

    return app


def _create_pages_router(static_dir: str) -> APIRouter:
    """创建页面路由

    Args:
        static_dir: 静态文件目录

    Returns:
        APIRouter: 页面路由实例
    """
    router = APIRouter(prefix="", tags=["页面"])

    @router.get('/')
    async def root() -> HTMLResponse:
        return read_html_file(Path(static_dir), 'login.html')

    @router.get('/login.html')
    async def login_page() -> HTMLResponse:
        return read_html_file(Path(static_dir), 'login.html')

    @router.get('/register.html')
    async def register_page() -> HTMLResponse:
        return read_html_file(Path(static_dir), 'register.html')

    @router.get('/admin')
    async def admin_page() -> HTMLResponse:
        return read_html_file(Path(static_dir), 'index.html')

    @router.get('/user_management.html')
    async def user_management_page() -> HTMLResponse:
        return read_html_file(Path(static_dir), 'user_management.html')

    @router.get('/log_management.html')
    async def log_management_page() -> HTMLResponse:
        return read_html_file(Path(static_dir), 'log_management.html')

    @router.get('/data_management.html')
    async def data_management_page() -> HTMLResponse:
        return read_html_file(Path(static_dir), 'data_management.html')

    @router.get('/item_search.html')
    async def item_search_page() -> HTMLResponse:
        return read_html_file(Path(static_dir), 'item_search.html')

    @router.get("/static/{path:path}")
    async def serve_static(request: Request, path: str):
        from fastapi.responses import FileResponse
        file_path = os.path.join(static_dir, path)
        if os.path.exists(file_path):
            response = FileResponse(file_path)
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        return {"detail": "Not found"}, 404

    return router


def _register_api_routes(app: FastAPI) -> None:
    """注册API路由

    Args:
        app: FastAPI应用实例
    """
    @app.get('/health')
    @limiter.exempt
    async def health_check(request: Request) -> JSONResponse:
        """健康检查端点"""
        try:
            from app.core import cookie_manager
            manager_status = "ok" if cookie_manager.manager is not None else "error"

            from app.repositories import db_manager
            try:
                db_manager.get_all_cookies()
                db_status = "ok"
            except Exception:
                db_status = "error"

            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()

            status = {
                "status": "healthy" if manager_status == "ok" and db_status == "ok" else "unhealthy",
                "timestamp": time.time(),
                "services": {
                    "cookie_manager": manager_status,
                    "database": db_status
                },
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_info.percent,
                    "memory_available": memory_info.available
                }
            }

            if status["status"] == "unhealthy":
                raise HTTPException(status_code=503, detail=status)

            return JSONResponse(status)

        except HTTPException:
            raise
        except Exception as e:
            return JSONResponse({
                "status": "unhealthy",
                "timestamp": time.time(),
                "error": str(e)
            })

    @app.get('/api/health')
    @limiter.exempt
    async def api_health_check(request: Request) -> JSONResponse:
        """API 健康检查端点"""
        try:
            from app.core import cookie_manager
            manager_status = "ok" if cookie_manager.manager is not None else "error"

            from app.repositories import db_manager
            try:
                db_manager.get_all_cookies()
                db_status = "ok"
            except Exception:
                db_status = "error"

            status = {
                "status": "healthy" if manager_status == "ok" and db_status == "ok" else "unhealthy",
                "timestamp": time.time(),
                "services": {
                    "cookie_manager": manager_status,
                    "database": db_status
                }
            }

            return JSONResponse(status)
        except Exception as e:
            return JSONResponse({
                "status": "unhealthy",
                "timestamp": time.time(),
                "error": str(e)
            })

    @app.get('/api/info')
    @limiter.exempt
    async def api_info(request: Request) -> Dict[str, Any]:
        """API 信息端点"""
        return {
            "name": "闲鱼管理系统 API",
            "version": "1.0.0",
            "status": "running",
            "timestamp": time.time()
        }

    @app.post("/xianyu/reply", response_model=ResponseModel)
    async def xianyu_reply(req: RequestModel) -> Dict[str, Any]:
        """自动回复接口"""
        msg_template = match_reply(req.cookie_id, req.send_message)
        if not msg_template:
            from app.repositories import db_manager
            default_reply_settings = db_manager.get_default_reply(req.cookie_id)

            if default_reply_settings and default_reply_settings.get('enabled', False):
                msg_template = default_reply_settings.get('reply_content', '')

            if not msg_template:
                raise HTTPException(status_code=404, detail="未找到匹配的回复规则且未设置默认回复")

        try:
            send_msg = msg_template.format(
                send_user_id=req.send_user_id,
                send_user_name=req.send_user_name,
                send_message=req.send_message,
            )
        except Exception:
            send_msg = msg_template

        return {"code": 200, "data": {"send_msg": send_msg}}

    @app.post("/upload-image")
    async def upload_image(file: UploadFile = File(...)) -> Dict[str, Any]:
        """图片上传接口"""
        try:
            from app.utils.image_uploader import upload_image as do_upload
            contents = await file.read()
            image_url = await do_upload(contents)
            if image_url:
                return {'success': True, 'url': image_url}
            else:
                return {'success': False, 'error': '上传失败'}
        except Exception as e:
            logger.error(f"图片上传失败: {e}")
            return {'success': False, 'error': str(e)}

    def _save_cookie_from_login(result: Dict[str, Any], user_id: int = None) -> bool:
        """从登录结果保存Cookie（内部辅助函数）

        Args:
            result: 登录结果字典
            user_id: 用户ID，默认为1

        Returns:
            bool: 是否成功保存Cookie
        """
        from app.repositories import db_manager
        from app.core import cookie_manager

        if not (result.get('status') == 'success' and result.get('cookies') and result.get('unb')):
            return False

        cookie_value = result['cookies']
        unb = result.get('unb')

        if not unb:
            logger.error("扫码登录成功但UNB为空")
            result['save_cookie_error'] = 'UNB为空，登录失败'
            # 即使没有unb，也返回account_info让前端可以处理
            result['account_info'] = {
                'account_id': None,
                'is_new_account': False,
                'user_id': user_id,
                'error': 'UNB为空'
            }
            return False

        cookie_id = unb
        existing = db_manager.get_cookie_by_id(cookie_id)

        if user_id is None:
            user_id = 1

        try:
            if not existing:
                db_manager.save_cookie(cookie_id, cookie_value, user_id)
                db_manager.save_cookie_status(cookie_id, True)
                logger.info("扫码登录成功，已保存新Cookie")

                if cookie_manager and cookie_manager.manager:
                    cookie_manager.manager.add_cookie(cookie_id, cookie_value, user_id=user_id, save_to_db=False)
            else:
                db_manager.save_cookie(cookie_id, cookie_value)
                db_manager.save_cookie_status(cookie_id, True)
                logger.info("扫码登录成功，已更新Cookie")

                if cookie_manager and cookie_manager.manager:
                    cookie_manager.manager.update_cookie(cookie_id, cookie_value)

            # 无论保存是否成功，都返回account_info给前端
            result['account_info'] = {
                'account_id': cookie_id,
                'is_new_account': not existing,
                'user_id': user_id if not existing else None
            }
            return True
        except Exception as e:
            logger.error(f"保存Cookie到数据库失败: {e}")
            result['save_cookie_error'] = str(e)
            # 即使保存失败，也返回account_info让前端可以处理
            result['account_info'] = {
                'account_id': cookie_id,
                'is_new_account': not existing,
                'user_id': user_id if not existing else None,
                'error': str(e)
            }
            return False

    @app.post("/qr-login/generate")
    @limiter.limit("5/minute")
    async def generate_qr_code(
        request: Request,
        current_user: Dict[str, Any] = Depends(require_auth)
    ) -> Dict[str, Any]:
        """生成扫码登录二维码（需认证）
        
        Args:
            current_user: 当前登录用户
            
        Returns:
            Dict包含session_id和qr_code_url
        """
        try:
            from app.utils.qr_login import qr_login_manager
            user_id = current_user.get('user_id')
            result = await qr_login_manager.generate_qr_code(user_id=user_id)
            return result
        except Exception as e:
            logger.error(f"生成二维码失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/qr-login/check/{session_id}")
    @limiter.limit("30/minute")
    async def check_qr_login(
        request: Request,
        session_id: str,
        current_user: Dict[str, Any] = Depends(require_auth)
    ) -> Dict[str, Any]:
        """检查扫码登录状态（需认证）
        
        Args:
            request: FastAPI请求对象
            session_id: 会话ID
            current_user: 当前登录用户
            
        Returns:
            Dict包含状态信息
        """
        try:
            from app.utils.qr_login import qr_login_manager

            user_id = current_user.get('user_id')
            result = await qr_login_manager.check_login(session_id, user_id=user_id)

            if result.get('status') == 'success':
                try:
                    _save_cookie_from_login(result, user_id)
                except Exception as e:
                    logger.error(f"保存Cookie失败：{e}")
                    result['save_cookie_error'] = str(e)
                    # 确保即使保存失败也返回account_info
                    if 'account_info' not in result:
                        result['account_info'] = {
                            'account_id': result.get('unb'),
                            'is_new_account': False,
                            'user_id': user_id,
                            'error': str(e)
                        }

            return result
        except Exception as e:
            logger.error(f"检查扫码状态失败：{e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/qr-login/recheck/{session_id}")
    @limiter.limit("10/minute")
    async def recheck_qr_login(
        request: Request,
        session_id: str,
        current_user: Dict[str, Any] = Depends(require_auth)
    ) -> Dict[str, Any]:
        """重新检查扫码登录状态（需认证）

        Args:
            session_id: 会话ID
            current_user: 当前登录用户

        Returns:
            Dict包含状态信息
        """
        try:
            from app.utils.qr_login import qr_login_manager

            user_id = current_user.get('user_id')
            result = await qr_login_manager.recheck_login(session_id, user_id=user_id)

            if result.get('status') == 'success':
                try:
                    _save_cookie_from_login(result, user_id)
                except Exception as e:
                    logger.error(f"保存Cookie失败：{e}")
                    result['save_cookie_error'] = str(e)
                    # 确保即使保存失败也返回account_info
                    if 'account_info' not in result:
                        result['account_info'] = {
                            'account_id': result.get('unb'),
                            'is_new_account': False,
                            'user_id': user_id,
                            'error': str(e)
                        }

            return result
        except Exception as e:
            logger.error(f"重新检查扫码状态失败：{e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/backup/export")
    async def export_backup() -> StreamingResponse:
        """导出备份"""
        try:
            from app.repositories import db_manager
            import io
            import json

            backup_data = db_manager.export_backup()
            json_str = json.dumps(backup_data, indent=2, ensure_ascii=False)

            output = io.BytesIO()
            output.write(json_str.encode('utf-8'))
            output.seek(0)

            return StreamingResponse(
                output,
                media_type='application/json',
                headers={'Content-Disposition': 'attachment;filename=backup.json'}
            )
        except Exception as e:
            logger.error(f"导出备份失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/backup/import")
    @limiter.limit("1/minute")
    async def import_backup(request: Request, file: UploadFile = File(...)) -> Dict[str, Any]:
        """导入备份"""
        try:
            from app.repositories import db_manager
            import json

            contents = await file.read()
            backup_data = json.loads(contents)

            if db_manager.import_backup(backup_data):
                return {'msg': 'success'}
            else:
                raise HTTPException(status_code=500, detail="导入失败")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"导入备份失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))


app = create_app()

__all__ = ['app', 'limiter', 'REQUEST_COUNT', 'REQUEST_LATENCY', 'ACTIVE_REQUESTS']
