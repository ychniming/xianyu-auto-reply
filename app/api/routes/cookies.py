"""Cookie管理路由模块

提供Cookie账号的增删改查接口
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, validator, constr
from typing import Optional, Dict, Any
from loguru import logger
import re

from app.api.dependencies import get_current_user, check_cookie_owner
from app.api.response import success, created, updated, deleted

router = APIRouter(prefix="", tags=["账号管理"])

# -------------------- 请求/响应模型 --------------------
RESERVED_IDS = {'admin', 'root', 'system', 'test', 'null', 'undefined', 'default'}

class CookieIn(BaseModel):
    id: constr(min_length=1, max_length=100) = Field(
        ...,
        description="Cookie账号ID",
        example="my_account_1"
    )
    value: constr(min_length=10, max_length=10000) = Field(
        ...,
        description="Cookie值",
        example="cookie_value_here"
    )
    
    @validator('id')
    def validate_id(cls, v):
        if not v or not v.strip():
            raise ValueError('Cookie ID不能为空')
        v = v.strip()
        if v.lower() in RESERVED_IDS:
            raise ValueError(f'Cookie ID不能使用保留名称: {v}')
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', v):
            raise ValueError('Cookie ID只能包含字母、数字、下划线、连字符和点')
        return v
    
    @validator('value')
    def validate_value(cls, v):
        if not v or not v.strip():
            raise ValueError('Cookie值不能为空')
        return v.strip()


class CookieStatusIn(BaseModel):
    enabled: bool = Field(..., description="启用状态")


class CookieDetails(BaseModel):
    id: str
    value: str
    enabled: bool
    auto_confirm: bool


# -------------------- Cookie路由 --------------------
@router.get("/cookies")
def list_cookies(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """获取当前用户的Cookie列表（公开接口）"""
    from src import cookie_manager
    if cookie_manager.manager is None:
        return success(data=[])

    from app.repositories import db_manager
    if current_user is None:
        return success(data=[])
    user_id = current_user['user_id']
    user_cookies = db_manager.get_all_cookies(user_id)
    return success(data=list(user_cookies.keys()))


@router.get("/cookies/details")
def get_cookies_details(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """获取所有Cookie的详细信息"""
    from src import cookie_manager
    if cookie_manager.manager is None:
        return success(data=[])

    from app.repositories import db_manager
    if current_user is None:
        return success(data=[])
    user_id = current_user['user_id']
    user_cookies = db_manager.get_all_cookies(user_id)

    result = []
    for cookie_id, cookie_value in user_cookies.items():
        cookie_enabled = cookie_manager.manager.get_cookie_status(cookie_id)
        auto_confirm = db_manager.get_auto_confirm(cookie_id)
        result.append({
            'id': cookie_id,
            'value': cookie_value,
            'enabled': cookie_enabled,
            'auto_confirm': auto_confirm
        })
    return success(data=result)


@router.post("/cookies")
def add_cookie(item: CookieIn, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """添加Cookie账号"""
    from src import cookie_manager
    if cookie_manager.manager is None:
        raise HTTPException(status_code=500, detail="CookieManager 未就绪")

    if current_user is None:
        raise HTTPException(status_code=401, detail="请先登录")

    try:
        user_id = current_user['user_id']
        from app.repositories import db_manager

        logger.info(f"尝试添加Cookie: {item.id}, 当前用户ID: {user_id}")

        existing_cookies = db_manager.get_all_cookies()
        if item.id in existing_cookies:
            user_cookies = db_manager.get_all_cookies(user_id)
            if item.id not in user_cookies:
                logger.warning(f"Cookie ID冲突: {item.id} 已被其他用户使用")
                raise HTTPException(status_code=400, detail="该Cookie ID已被其他用户使用")

        db_manager.save_cookie(item.id, item.value, user_id)
        cookie_manager.manager.add_cookie(item.id, item.value, user_id=user_id)
        logger.info(f"Cookie添加成功: {item.id}")
        return created(data={"id": item.id}, message="Cookie添加成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加Cookie失败: {item.id} - {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put('/cookies/{cid}')
def update_cookie(cid: str, item: CookieIn, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """更新Cookie"""
    from src import cookie_manager
    if cookie_manager.manager is None:
        raise HTTPException(status_code=500, detail='CookieManager 未就绪')

    try:
        user_id = current_user['user_id'] if current_user else None

        if user_id is not None:
            if not check_cookie_owner(cid, current_user):
                raise HTTPException(status_code=403, detail="无权限操作该Cookie")

        from app.repositories import db_manager

        db_manager.save_cookie(cid, item.value, user_id)
        cookie_manager.manager.update_cookie(cid, item.value)
        return updated(message="Cookie更新成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put('/cookies/{cid}/status')
def update_cookie_status(cid: str, status: CookieStatusIn, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """更新Cookie启用状态"""
    from src import cookie_manager

    try:
        user_id = current_user['user_id'] if current_user else None

        if user_id is not None:
            if not check_cookie_owner(cid, current_user):
                raise HTTPException(status_code=403, detail="无权限操作该Cookie")

        from app.repositories import db_manager
        cookie_manager.manager.update_cookie_status(cid, status.enabled)
        db_manager.save_cookie_status(cid, status.enabled)
        return updated(message="状态更新成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/cookies/{cid}/auto-confirm")
def update_auto_confirm(cid: str, enabled: bool = True, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """更新自动确认发货设置"""
    try:
        user_id = current_user['user_id'] if current_user else None

        if user_id is not None:
            if not check_cookie_owner(cid, current_user):
                raise HTTPException(status_code=403, detail="无权限操作该Cookie")

        from app.repositories import db_manager
        db_manager.update_auto_confirm(cid, enabled)
        return updated(message="自动确认设置更新成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/cookies/{cid}/auto-confirm")
def get_auto_confirm(cid: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """获取自动确认发货设置"""
    try:
        user_id = current_user['user_id'] if current_user else None

        if user_id is not None:
            if not check_cookie_owner(cid, current_user):
                raise HTTPException(status_code=403, detail="无权限操作该Cookie")

        from app.repositories import db_manager
        auto_confirm = db_manager.get_auto_confirm(cid)
        return success(data={'auto_confirm': auto_confirm})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/cookies/{cid}")
def delete_cookie(cid: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """删除Cookie"""
    from src import cookie_manager

    try:
        user_id = current_user['user_id'] if current_user else None

        if user_id is not None:
            if not check_cookie_owner(cid, current_user):
                raise HTTPException(status_code=403, detail="无权限操作该Cookie")

        from app.repositories import db_manager
        cookie_manager.manager.remove_cookie(cid)
        db_manager.delete_cookie(cid)
        return deleted(message="Cookie删除成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
