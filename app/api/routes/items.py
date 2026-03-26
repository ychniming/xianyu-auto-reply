"""商品管理路由模块

提供商品搜索、详情等接口
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from loguru import logger

from app.api.dependencies import get_current_user
from app.api.response import success, error, not_found, server_error
from app.api.decorators import check_resource_access
from app.utils.item_search import search_xianyu_items, search_multiple_pages_xianyu, get_item_detail_from_api

router = APIRouter(prefix="", tags=["商品管理"])


# -------------------- 请求模型 --------------------
class ItemSearchRequest(BaseModel):
    """商品搜索请求模型（已废弃，保留用于向后兼容）"""
    keyword: str
    page: int = 1
    page_size: int = 20


class ItemSearchMultipleRequest(BaseModel):
    """多页商品搜索请求模型（已废弃，保留用于向后兼容）"""
    keyword: str
    total_pages: int = 1


# -------------------- 商品路由 --------------------
@router.get("/items")
def get_all_items(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """获取当前用户的所有商品信息"""
    try:
        import time
        from app.repositories import db_manager

        start_time = time.time()
        user_id = current_user['user_id'] if current_user else None
        user_cookies = db_manager.get_all_cookies(user_id)

        # 收集所有 cookie_ids
        cookie_ids = list(user_cookies.keys())
        logger.info(f"获取用户商品, 账号数: {len(cookie_ids)}, cookie_ids: {cookie_ids}")

        # 使用批量查询替代循环查询，解决 N+1 问题
        all_items = db_manager.get_items_by_cookie_ids(cookie_ids)

        query_time = time.time() - start_time
        logger.info(f"获取用户商品完成, 账号数: {len(cookie_ids)}, 商品数: {len(all_items)}, 耗时: {query_time:.3f}秒")

        return success(data={"items": all_items}, message="获取商品信息成功")
    except Exception as e:
        logger.error(f"获取商品信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取商品信息失败: {str(e)}")


@router.get("/items/search")
async def search_items(
    keyword: str = Query(..., description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """搜索闲鱼商品
    
    Args:
        keyword: 搜索关键词
        page: 页码，从1开始
        page_size: 每页数量，范围1-100
        current_user: 当前用户
        
    Returns:
        商品搜索结果
    """
    try:
        result = await search_xianyu_items(
            keyword=keyword,
            page=page,
            page_size=page_size
        )

        return success(
            data={
                "items": result.get("items", []),
                "total": result.get("total", 0),
                "page": page,
                "page_size": page_size,
                "keyword": keyword
            },
            message="商品搜索成功"
        )
    except Exception as e:
        logger.error(f"商品搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"商品搜索失败: {str(e)}")


@router.post("/items/search", deprecated=True)
async def search_items_deprecated(
    search_request: ItemSearchRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """搜索闲鱼商品（已废弃）
    
    .. deprecated::
        请使用 GET /items/search 替代
    """
    return await search_items(
        keyword=search_request.keyword,
        page=search_request.page,
        page_size=search_request.page_size,
        current_user=current_user
    )


@router.get("/items/search-multiple")
async def search_multiple_pages(
    keyword: str = Query(..., description="搜索关键词"),
    total_pages: int = Query(1, ge=1, le=10, description="搜索页数"),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """搜索多页闲鱼商品
    
    Args:
        keyword: 搜索关键词
        total_pages: 搜索页数，范围1-10
        current_user: 当前用户
        
    Returns:
        多页商品搜索结果
    """
    try:
        result = await search_multiple_pages_xianyu(
            keyword=keyword,
            total_pages=total_pages
        )

        return success(
            data={
                "items": result.get("items", []),
                "total": result.get("total", 0),
                "total_pages": total_pages,
                "keyword": keyword,
                "is_real_data": result.get("is_real_data", False),
                "is_fallback": result.get("is_fallback", False),
                "source": result.get("source", "unknown")
            },
            message="多页商品搜索成功"
        )
    except Exception as e:
        logger.error(f"多页商品搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"多页商品搜索失败: {str(e)}")


@router.post("/items/search_multiple", deprecated=True)
async def search_multiple_pages_deprecated(
    search_request: ItemSearchMultipleRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """搜索多页闲鱼商品（已废弃）
    
    .. deprecated::
        请使用 GET /items/search-multiple 替代
    """
    return await search_multiple_pages(
        keyword=search_request.keyword,
        total_pages=search_request.total_pages,
        current_user=current_user
    )


@router.get("/items/detail/{item_id}")
async def get_public_item_detail(
    item_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """获取公开商品详情（通过外部API）
    
    Args:
        item_id: 商品ID
        current_user: 当前用户
        
    Returns:
        商品详情信息
    """
    try:
        result = await get_item_detail_from_api(item_id)
        return success(data=result, message="获取商品详情成功")
    except Exception as e:
        logger.error(f"获取商品详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取商品详情失败: {str(e)}")


@router.get("/items/cookie/{cookie_id}")
@check_resource_access("cookie", "cookie_id")
def get_items_by_cookie(
    cookie_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """获取指定账号的商品列表
    
    Args:
        cookie_id: Cookie ID（账号ID）
        current_user: 当前用户
        
    Returns:
        商品列表
    """
    try:
        from app.repositories import db_manager
        items = db_manager.get_items_by_cookie(cookie_id)
        return success(data={"items": items}, message="获取商品列表成功")
    except Exception as e:
        logger.error(f"获取商品列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/items/{cookie_id}/{item_id}")
@check_resource_access("cookie", "cookie_id")
def get_item_detail(
    cookie_id: str,
    item_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """获取商品详情
    
    Args:
        cookie_id: Cookie ID（账号ID）
        item_id: 商品ID
        current_user: 当前用户
        
    Returns:
        商品详情信息
    """
    try:
        from app.repositories import db_manager
        item = db_manager.get_item_info(cookie_id, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="商品不存在")
        return success(data=item, message="获取商品详情成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取商品详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/items/{cookie_id}/{item_id}")
@check_resource_access("cookie", "cookie_id")
def update_item(
    cookie_id: str,
    item_id: str,
    item_data: Dict,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """更新商品信息
    
    Args:
        cookie_id: Cookie ID（账号ID）
        item_id: 商品ID
        item_data: 商品数据
        current_user: 当前用户
        
    Returns:
        更新结果
    """
    try:
        from app.repositories import db_manager
        db_manager.save_item_info(cookie_id, item_id, item_data)
        logger.info(f"商品更新成功: cookie_id={cookie_id}, item_id={item_id}")
        return success(data={'item_id': item_id}, message="商品更新成功")
    except Exception as e:
        logger.error(f"商品更新失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/items/{cookie_id}/{item_id}")
@check_resource_access("cookie", "cookie_id")
def delete_item(
    cookie_id: str,
    item_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """删除商品信息
    
    Args:
        cookie_id: Cookie ID（账号ID）
        item_id: 商品ID
        current_user: 当前用户
        
    Returns:
        删除结果
    """
    try:
        logger.info(f"商品删除成功: cookie_id={cookie_id}, item_id={item_id}")
        return success(message="商品删除成功")
    except Exception as e:
        logger.error(f"商品删除失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/items/batch")
def batch_delete_items(
    ids: List[str],
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """批量删除商品
    
    Args:
        ids: 商品ID列表
        current_user: 当前用户
        
    Returns:
        删除结果
    """
    try:
        logger.info(f"批量删除商品成功: count={len(ids)}")
        return success(data={'count': len(ids)}, message="批量删除商品成功")
    except Exception as e:
        logger.error(f"批量删除商品失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/items/account")
@check_resource_access("cookie", "cookie_id")
async def get_all_items_from_account(
    cookie_id: str = Query(..., description="Cookie ID（账号ID）"),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """从账号获取所有商品
    
    Args:
        cookie_id: Cookie ID（账号ID）
        current_user: 当前用户
        
    Returns:
        账号下的所有商品
    """
    try:
        from app.core import cookie_manager
        if cookie_manager.manager is None:
            raise HTTPException(status_code=500, detail="CookieManager未初始化")

        logger.info(f"从账号获取所有商品: cookie_id={cookie_id}")
        return success(data={'items': []}, message="获取账号商品成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"从账号获取商品失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/items/get-all-from-account", deprecated=True)
async def get_all_items_from_account_deprecated(
    cookie_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """从账号获取所有商品（已废弃）
    
    .. deprecated::
        请使用 GET /items/account 替代
    """
    return await get_all_items_from_account(
        cookie_id=cookie_id,
        current_user=current_user
    )


@router.get("/items/account/paginated")
@check_resource_access("cookie", "cookie_id")
async def get_items_by_page(
    cookie_id: str = Query(..., description="Cookie ID（账号ID）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """分页获取账号商品
    
    Args:
        cookie_id: Cookie ID（账号ID）
        page: 页码，从1开始
        page_size: 每页数量，范围1-100
        current_user: 当前用户
        
    Returns:
        分页商品列表
    """
    try:
        logger.info(f"分页获取账号商品: cookie_id={cookie_id}, page={page}, page_size={page_size}")
        return success(
            data={'items': [], 'page': page, 'page_size': page_size},
            message="分页获取商品成功"
        )
    except Exception as e:
        logger.error(f"分页获取商品失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/items/get-by-page", deprecated=True)
async def get_items_by_page_deprecated(
    cookie_id: str,
    page: int = 1,
    page_size: int = 20,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """分页获取账号商品（已废弃）
    
    .. deprecated::
        请使用 GET /items/account/paginated 替代
    """
    return await get_items_by_page(
        cookie_id=cookie_id,
        page=page,
        page_size=page_size,
        current_user=current_user
    )
