"""认证依赖模块

提供统一的认证授权依赖注入函数
"""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any

security = HTTPBearer(auto_error=False)


def get_token_data(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
    """获取 token 数据，不验证认证状态"""
    from loguru import logger
    
    if not credentials:
        logger.debug("未提供认证凭据")
        return None
    
    token = credentials.credentials
    logger.debug(f"收到 token: {token[:20]}...")
    
    from app.repositories import db_manager
    session = db_manager.get_session(token)
    
    if session:
        logger.debug(f"Token 有效，用户：{session.get('username')}")
    else:
        logger.debug(f"Token 无效：{token[:20]}...")
    
    return session


def get_current_user(user_info: Optional[Dict[str, Any]] = Depends(get_token_data)) -> Optional[Dict[str, Any]]:
    """获取当前登录用户，如果未认证返回None而非抛出异常

    使用此依赖的路由需要自行处理None的情况
    """
    return user_info


def require_auth(user_info: Optional[Dict[str, Any]] = Depends(get_token_data)) -> Dict[str, Any]:
    """强制要求认证，未认证时返回401错误

    使用此依赖的路由不需要检查user_info是否为None
    """
    if not user_info:
        raise HTTPException(status_code=401, detail="未授权访问")
    return user_info


def get_optional_user(user_info: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Optional[Dict[str, Any]]:
    """获取可选的用户信息，允许未认证访问

    与 Depends(lambda: None) 的区别：
    - 正确解析Authorization头
    - 返回None时明确知道是未认证
    """
    return user_info


def check_resource_owner(resource_user_id: Optional[int], current_user: Dict[str, Any]) -> bool:
    """检查当前用户是否为资源所有者

    Args:
        resource_user_id: 资源的用户ID
        current_user: 当前登录用户信息

    Returns:
        bool: 是否为所有者或管理员
    """
    if current_user.get('username') == 'admin':
        return True

    if resource_user_id is None:
        return False

    return current_user.get('user_id') == resource_user_id


def check_cookie_owner(cookie_id: str, current_user: Dict[str, Any]) -> bool:
    """检查当前用户是否有权限操作指定Cookie

    Args:
        cookie_id: Cookie账号ID
        current_user: 当前登录用户信息

    Returns:
        bool: 是否有权限
    """
    if current_user.get('username') == 'admin':
        return True

    from app.repositories import db_manager
    cookie_details = db_manager.get_cookie_details(cookie_id)
    if not cookie_details:
        return False

    cookie_user_id = cookie_details.get('user_id')
    if cookie_user_id is None:
        return True

    return current_user.get('user_id') == cookie_user_id


def verify_admin_token(user_info: Optional[Dict[str, Any]] = Depends(get_token_data)) -> Dict[str, Any]:
    """验证管理员token

    使用此依赖的路由需要验证当前用户是否为管理员

    Returns:
        Dict[str, Any]: 用户信息

    Raises:
        HTTPException: 如果未授权或非管理员
    """
    if not user_info:
        raise HTTPException(status_code=401, detail="未授权访问")

    if user_info.get('username') != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")

    return user_info
