"""卡券和发货规则路由模块

提供卡券、发货规则的增删改查接口
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.api.dependencies import get_current_user

router = APIRouter(prefix="", tags=["卡券管理"])

# -------------------- 请求/响应模型 --------------------
class CardCreate(BaseModel):
    name: str
    type: str
    api_config: Optional[Dict] = None
    text_content: Optional[str] = None
    data_content: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    delay_seconds: int = 0
    is_multi_spec: bool = False
    spec_name: Optional[str] = None
    spec_value: Optional[str] = None


class CardUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    api_config: Optional[Dict] = None
    text_content: Optional[str] = None
    data_content: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    delay_seconds: Optional[int] = None
    is_multi_spec: Optional[bool] = None
    spec_name: Optional[str] = None
    spec_value: Optional[str] = None


class DeliveryRuleCreate(BaseModel):
    keyword: str
    card_id: int
    delivery_count: int = 1
    enabled: bool = True
    description: Optional[str] = None


class DeliveryRuleUpdate(BaseModel):
    keyword: Optional[str] = None
    card_id: Optional[int] = None
    delivery_count: Optional[int] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None


# -------------------- 卡券路由 --------------------
@router.get("/cards")
def list_cards(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """获取所有卡券"""
    try:
        from app.repositories import db_manager
        user_id = current_user['user_id'] if current_user else None
        return db_manager.get_all_cards(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cards")
def create_card(card: CardCreate, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """创建卡券"""
    try:
        from app.repositories import db_manager
        user_id = current_user['user_id'] if current_user else None
        card_id = db_manager.create_card(
            name=card.name,
            card_type=card.type,
            api_config=card.api_config,
            text_content=card.text_content,
            data_content=card.data_content,
            image_url=card.image_url,
            description=card.description,
            delay_seconds=card.delay_seconds,
            is_multi_spec=card.is_multi_spec,
            spec_name=card.spec_name,
            spec_value=card.spec_value,
            user_id=user_id
        )
        return {'msg': 'created', 'id': card_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cards/{card_id}")
def get_card(card_id: int, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """获取卡券详情"""
    try:
        from app.repositories import db_manager
        user_id = current_user['user_id'] if current_user else None
        card = db_manager.get_card_by_id(card_id, user_id)
        if not card:
            raise HTTPException(status_code=404, detail="卡券不存在")
        return card
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/cards/{card_id}")
def update_card(card_id: int, card: CardUpdate, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """更新卡券"""
    try:
        from app.repositories import db_manager
        user_id = current_user['user_id'] if current_user else None
        db_manager.update_card(
            card_id=card_id,
            name=card.name,
            card_type=card.type,
            api_config=card.api_config,
            text_content=card.text_content,
            data_content=card.data_content,
            image_url=card.image_url,
            description=card.description,
            enabled=card.enabled,
            delay_seconds=card.delay_seconds,
            is_multi_spec=card.is_multi_spec,
            spec_name=card.spec_name,
            spec_value=card.spec_value,
            user_id=user_id
        )
        return {'msg': 'updated'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/cards/{card_id}/image")
async def update_card_image(card_id: int, file: UploadFile = File(...), current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """更新卡券图片"""
    try:
        from app.utils.image_uploader import upload_image
        from app.repositories import db_manager

        contents = await file.read()
        image_url = await upload_image(contents)

        if image_url:
            db_manager.update_card_image_url(card_id, image_url)
            return {'msg': 'updated', 'image_url': image_url}
        else:
            raise HTTPException(status_code=500, detail="图片上传失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cards/{card_id}")
def delete_card(card_id: int, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """删除卡券"""
    try:
        from app.repositories import db_manager
        db_manager.delete_card(card_id)
        return {'msg': 'deleted'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- 发货规则路由 --------------------
@router.get("/delivery-rules")
def list_delivery_rules(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """获取所有发货规则"""
    try:
        from app.repositories import db_manager
        user_id = current_user['user_id'] if current_user else None
        return db_manager.get_all_delivery_rules(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delivery-rules")
def create_delivery_rule(rule: DeliveryRuleCreate, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """创建发货规则"""
    try:
        from app.repositories import db_manager
        user_id = current_user['user_id'] if current_user else None
        rule_id = db_manager.create_delivery_rule(
            keyword=rule.keyword,
            card_id=rule.card_id,
            delivery_count=rule.delivery_count,
            enabled=rule.enabled,
            description=rule.description,
            user_id=user_id
        )
        return {'msg': 'created', 'id': rule_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/delivery-rules/{rule_id}")
def get_delivery_rule(rule_id: int, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """获取发货规则详情"""
    try:
        from app.repositories import db_manager
        user_id = current_user['user_id'] if current_user else None
        rule = db_manager.get_delivery_rule_by_id(rule_id, user_id)
        if not rule:
            raise HTTPException(status_code=404, detail="规则不存在")
        return rule
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/delivery-rules/{rule_id}")
def update_delivery_rule(rule_id: int, rule: DeliveryRuleUpdate, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """更新发货规则"""
    try:
        from app.repositories import db_manager
        user_id = current_user['user_id'] if current_user else None
        db_manager.update_delivery_rule(
            rule_id=rule_id,
            keyword=rule.keyword,
            card_id=rule.card_id,
            delivery_count=rule.delivery_count,
            enabled=rule.enabled,
            description=rule.description,
            user_id=user_id
        )
        return {'msg': 'updated'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delivery-rules/{rule_id}")
def delete_delivery_rule(rule_id: int, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """删除发货规则"""
    try:
        from app.repositories import db_manager
        user_id = current_user['user_id'] if current_user else None
        db_manager.delete_delivery_rule(rule_id, user_id)
        return {'msg': 'deleted'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
