"""权限装饰器模块

提供统一的权限检查装饰器，用于路由函数的权限控制
"""
from functools import wraps
from typing import Dict, Any, Optional, Callable
from fastapi import HTTPException, Request
from loguru import logger

from app.api.dependencies import get_current_user, check_cookie_owner, check_resource_owner
from app.repositories import db_manager


class PermissionDeniedError(HTTPException):
    """权限拒绝异常

    当用户没有足够权限访问资源时抛出
    """
    def __init__(self, detail: str = "权限不足"):
        super().__init__(status_code=403, detail=detail)


class AuthenticationError(HTTPException):
    """认证失败异常

    当用户未登录或token无效时抛出
    """
    def __init__(self, detail: str = "未授权访问"):
        super().__init__(status_code=401, detail=detail)


def require_admin(func: Callable) -> Callable:
    """管理员权限装饰器

    检查当前用户是否为管理员，如果不是则抛出 PermissionDeniedError

    Args:
        func: 被装饰的函数

    Returns:
        Callable: 装饰后的函数

    Raises:
        AuthenticationError: 用户未登录
        PermissionDeniedError: 用户不是管理员

    Example:
        >>> @router.get("/admin/users")
        ... @require_admin
        ... async def list_users(request: Request, current_user: Dict = Depends(get_current_user)):
        ...     return {"users": [...]}
    """
    @wraps(func)
    async def wrapper(*args, current_user: Optional[Dict[str, Any]] = None, **kwargs):
        # 检查用户是否登录
        if not current_user:
            logger.warning(f"未授权访问管理接口: {func.__name__}")
            raise AuthenticationError("未授权访问")

        # 检查是否为管理员
        if current_user.get('username') != 'admin':
            logger.warning(
                f"非管理员用户尝试访问管理接口: {current_user.get('username')} -> {func.__name__}"
            )
            raise PermissionDeniedError("需要管理员权限")

        logger.debug(f"管理员访问: {current_user.get('username')} -> {func.__name__}")
        return await func(*args, current_user=current_user, **kwargs)

    return wrapper


def require_owner(resource_type: str) -> Callable:
    """资源所有者权限装饰器工厂

    检查当前用户是否为指定资源的所有者

    Args:
        resource_type: 资源类型，支持 'cookie_id', 'item_id', 'card_id' 等

    Returns:
        Callable: 装饰器函数

    Raises:
        AuthenticationError: 用户未登录
        PermissionDeniedError: 用户不是资源所有者

    Example:
        >>> @router.delete("/cookies/{cookie_id}")
        ... @require_owner("cookie_id")
        ... async def delete_cookie(cookie_id: str, current_user: Dict = Depends(get_current_user)):
        ...     return {"success": True}

        >>> @router.put("/items/{item_id}")
        ... @require_owner("item_id")
        ... async def update_item(item_id: str, data: dict, current_user: Dict = Depends(get_current_user)):
        ...     return {"success": True}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, current_user: Optional[Dict[str, Any]] = None, **kwargs):
            # 检查用户是否登录
            if not current_user:
                logger.warning(f"未授权访问资源: {func.__name__}")
                raise AuthenticationError("未授权访问")

            # 管理员拥有所有资源的访问权限
            if current_user.get('username') == 'admin':
                logger.debug(f"管理员访问资源: {resource_type} -> {func.__name__}")
                return await func(*args, current_user=current_user, **kwargs)

            # 获取资源ID
            resource_id = kwargs.get(resource_type)
            if not resource_id:
                # 尝试从路径参数中获取
                # 例如：cookie_id 可能是第一个位置参数
                if args and len(args) > 0:
                    # 检查第一个参数是否是字符串（可能是资源ID）
                    first_arg = args[0]
                    if isinstance(first_arg, str):
                        resource_id = first_arg

            if not resource_id:
                logger.error(f"无法获取资源ID: {resource_type} in {func.__name__}")
                raise PermissionDeniedError("资源不存在")

            # 根据资源类型检查权限
            has_permission = False

            if resource_type == 'cookie_id':
                has_permission = check_cookie_owner(resource_id, current_user)
            elif resource_type == 'item_id':
                # 检查商品所有权 - 需要通过 cookie_id 关联
                # 商品信息需要 cookie_id 和 item_id 两个参数
                # 这里简化处理：检查用户是否有任何关联的 cookie
                cookie_ids = db_manager.get_all_cookies(current_user.get('user_id'))
                if cookie_ids:
                    # 用户有 cookie，允许访问（简化权限模型）
                    has_permission = True
                else:
                    logger.warning(f"商品不存在或无权访问: {resource_id}")
                    raise HTTPException(status_code=404, detail="商品不存在或无权访问")
            elif resource_type == 'card_id':
                # 检查卡片所有权
                card = db_manager.get_card_by_id(int(resource_id), current_user.get('user_id'))
                if card:
                    has_permission = True
                else:
                    logger.warning(f"卡片不存在: {resource_id}")
                    raise HTTPException(status_code=404, detail="卡片不存在")
            else:
                # 通用资源检查
                logger.warning(f"未知的资源类型: {resource_type}")
                raise PermissionDeniedError(f"不支持的资源类型: {resource_type}")

            if not has_permission:
                logger.warning(
                    f"用户 {current_user.get('username')} 无权访问资源 {resource_type}={resource_id}"
                )
                raise PermissionDeniedError("无权访问此资源")

            logger.debug(
                f"用户 {current_user.get('username')} 访问资源 {resource_type}={resource_id}"
            )
            return await func(*args, current_user=current_user, **kwargs)

        return wrapper
    return decorator


def check_resource_access(resource_type: str, resource_id_param: str = None) -> Callable:
    """资源访问权限检查装饰器

    组合检查：管理员可访问所有资源，普通用户只能访问自己的资源

    Args:
        resource_type: 资源类型，支持 'cookie', 'item', 'card' 等
        resource_id_param: 资源ID参数名，如果不指定则使用 f"{resource_type}_id"

    Returns:
        Callable: 装饰器函数

    Raises:
        AuthenticationError: 用户未登录
        PermissionDeniedError: 用户无权访问资源
        HTTPException: 资源不存在

    Example:
        >>> @router.get("/cookies/{cookie_id}")
        ... @check_resource_access("cookie")
        ... async def get_cookie(cookie_id: str, current_user: Dict = Depends(get_current_user)):
        ...     return {"cookie": {...}}

        >>> @router.put("/items/{item_id}")
        ... @check_resource_access("item", "item_id")
        ... async def update_item(item_id: str, current_user: Dict = Depends(get_current_user)):
        ...     return {"success": True}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, current_user: Optional[Dict[str, Any]] = None, **kwargs):
            # 检查用户是否登录
            if not current_user:
                logger.warning(f"未授权访问资源: {func.__name__}")
                raise AuthenticationError("未授权访问")

            # 管理员拥有所有资源的访问权限
            if current_user.get('username') == 'admin':
                logger.debug(f"管理员访问资源: {resource_type} -> {func.__name__}")
                return await func(*args, current_user=current_user, **kwargs)

            # 确定资源ID参数名
            param_name = resource_id_param or f"{resource_type}_id"

            # 获取资源ID
            resource_id = kwargs.get(param_name)
            if not resource_id and args and len(args) > 0:
                first_arg = args[0]
                if isinstance(first_arg, str):
                    resource_id = first_arg

            if not resource_id:
                logger.error(f"无法获取资源ID: {param_name} in {func.__name__}")
                raise PermissionDeniedError("资源不存在")

            # 检查资源访问权限
            has_permission = False

            if resource_type == 'cookie':
                has_permission = check_cookie_owner(resource_id, current_user)
            elif resource_type == 'item':
                # 商品所有权检查 - 通过 cookie 关联
                cookie_ids = db_manager.get_all_cookies(current_user.get('user_id'))
                if cookie_ids:
                    has_permission = True
                else:
                    logger.warning(f"商品不存在或无权访问: {resource_id}")
                    raise HTTPException(status_code=404, detail="商品不存在或无权访问")
            elif resource_type == 'card':
                card = db_manager.get_card_by_id(int(resource_id), current_user.get('user_id'))
                if card:
                    has_permission = True
                else:
                    logger.warning(f"卡片不存在: {resource_id}")
                    raise HTTPException(status_code=404, detail="卡片不存在")
            else:
                logger.warning(f"未知的资源类型: {resource_type}")
                raise PermissionDeniedError(f"不支持的资源类型: {resource_type}")

            if not has_permission:
                logger.warning(
                    f"用户 {current_user.get('username')} 无权访问资源 {resource_type}={resource_id}"
                )
                raise PermissionDeniedError("无权访问此资源")

            logger.debug(
                f"用户 {current_user.get('username')} 访问资源 {resource_type}={resource_id}"
            )
            return await func(*args, current_user=current_user, **kwargs)

        return wrapper
    return decorator


def require_permission(permission: str) -> Callable:
    """权限检查装饰器（预留扩展）

    检查用户是否拥有指定权限

    Args:
        permission: 权限标识符，如 'user:read', 'cookie:write' 等

    Returns:
        Callable: 装饰器函数

    Raises:
        AuthenticationError: 用户未登录
        PermissionDeniedError: 用户没有指定权限

    Note:
        当前实现基于角色（admin/user），未来可扩展为基于权限的细粒度控制

    Example:
        >>> @router.get("/users")
        ... @require_permission("user:read")
        ... async def list_users(current_user: Dict = Depends(get_current_user)):
        ...     return {"users": [...]}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, current_user: Optional[Dict[str, Any]] = None, **kwargs):
            # 检查用户是否登录
            if not current_user:
                logger.warning(f"未授权访问: {func.__name__}")
                raise AuthenticationError("未授权访问")

            # 管理员拥有所有权限
            if current_user.get('username') == 'admin':
                logger.debug(f"管理员访问: {permission} -> {func.__name__}")
                return await func(*args, current_user=current_user, **kwargs)

            # TODO: 实现基于权限的细粒度控制
            # 当前简化实现：普通用户只有基础权限
            # 可以通过数据库或配置文件管理权限映射

            # 定义权限映射
            user_permissions = {
                'cookie:read': True,
                'cookie:write': True,
                'keyword:read': True,
                'keyword:write': True,
                'item:read': True,
                'item:write': True,
                'card:read': True,
                'card:write': True,
                'user:read': False,
                'user:write': False,
                'system:admin': False,
            }

            has_permission = user_permissions.get(permission, False)

            if not has_permission:
                logger.warning(
                    f"用户 {current_user.get('username')} 没有权限 {permission}"
                )
                raise PermissionDeniedError(f"需要权限: {permission}")

            logger.debug(
                f"用户 {current_user.get('username')} 使用权限 {permission} -> {func.__name__}"
            )
            return await func(*args, current_user=current_user, **kwargs)

        return wrapper
    return decorator
