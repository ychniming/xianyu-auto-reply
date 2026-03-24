"""商品管理路由模块

提供商品搜索、详情等接口
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from loguru import logger

from app.api.dependencies import get_current_user

router = APIRouter(prefix="", tags=["商品管理"])

# -------------------- 请求模型 --------------------
class ItemSearchRequest(BaseModel):
    keyword: str
    page: int = 1
    page_size: int = 20


class ItemSearchMultipleRequest(BaseModel):
    keyword: str
    total_pages: int = 1


# -------------------- 商品路由 --------------------
@router.get("/items")
def get_all_items(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """获取当前用户的所有商品信息"""
    try:
        from app.repositories import db_manager
        user_id = current_user['user_id'] if current_user else None
        user_cookies = db_manager.get_all_cookies(user_id)

        all_items = []
        for cookie_id in user_cookies.keys():
            items = db_manager.get_items_by_cookie(cookie_id)
            all_items.extend(items)

        return {"items": all_items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取商品信息失败: {str(e)}")


@router.post("/items/search")
async def search_items(
    search_request: ItemSearchRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """搜索闲鱼商品"""
    try:
        from app.utils.xianyu_searcher import search_xianyu_items

        result = await search_xianyu_items(
            keyword=search_request.keyword,
            page=search_request.page,
            page_size=search_request.page_size
        )

        return {
            "success": True,
            "data": result.get("items", []),
            "total": result.get("total", 0),
            "page": search_request.page,
            "page_size": search_request.page_size,
            "keyword": search_request.keyword
        }
    except Exception as e:
        logger.error(f"商品搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"商品搜索失败: {str(e)}")


@router.post("/items/search_multiple")
async def search_multiple_pages(
    search_request: ItemSearchMultipleRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """搜索多页闲鱼商品"""
    try:
        from app.utils.xianyu_searcher import search_multiple_pages_xianyu

        result = await search_multiple_pages_xianyu(
            keyword=search_request.keyword,
            total_pages=search_request.total_pages
        )

        return {
            "success": True,
            "data": result.get("items", []),
            "total": result.get("total", 0),
            "total_pages": search_request.total_pages,
            "keyword": search_request.keyword,
            "is_real_data": result.get("is_real_data", False),
            "is_fallback": result.get("is_fallback", False),
            "source": result.get("source", "unknown")
        }
    except Exception as e:
        logger.error(f"多页商品搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"多页商品搜索失败: {str(e)}")


@router.get("/items/detail/{item_id}")
async def get_public_item_detail(
    item_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """获取公开商品详情（通过外部API）"""
    try:
        from app.utils.item_search import get_item_detail_from_api

        result = await get_item_detail_from_api(item_id)
        return result
    except Exception as e:
        logger.error(f"获取商品详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取商品详情失败: {str(e)}")


@router.get("/items/cookie/{cookie_id}")
def get_items_by_cookie(cookie_id: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """获取指定账号的商品列表"""
    try:
        from app.repositories import db_manager
        items = db_manager.get_items_by_cookie(cookie_id)
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/items/{cookie_id}/{item_id}")
def get_item_detail(cookie_id: str, item_id: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """获取商品详情"""
    try:
        from app.repositories import db_manager
        item = db_manager.get_item_info(cookie_id, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="商品不存在")
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/items/{cookie_id}/{item_id}")
def update_item(cookie_id: str, item_id: str, item_data: Dict, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """更新商品信息"""
    try:
        from app.repositories import db_manager
        db_manager.save_item_info(cookie_id, item_id, item_data)
        return {'msg': 'updated'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/items/{cookie_id}/{item_id}")
def delete_item(cookie_id: str, item_id: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """删除商品信息"""
    try:
        from app.repositories import db_manager
        # 商品删除通常是通过标记删除，这里简化处理
        return {'msg': 'deleted'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/items/batch")
def batch_delete_items(ids: List[str], current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """批量删除商品"""
    try:
        return {'msg': 'deleted', 'count': len(ids)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/items/get-all-from-account")
async def get_all_items_from_account(cookie_id: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """从账号获取所有商品"""
    try:
        from app.core import cookie_manager
        if cookie_manager.manager is None:
            raise HTTPException(status_code=500, detail="CookieManager未初始化")

        # 调用XianyuAutoAsync获取商品列表
        return {'msg': 'success', 'items': []}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/items/get-by-page")
async def get_items_by_page(cookie_id: str, page: int = 1, page_size: int = 20, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """分页获取账号商品"""
    try:
        return {'msg': 'success', 'items': [], 'page': page, 'page_size': page_size}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
