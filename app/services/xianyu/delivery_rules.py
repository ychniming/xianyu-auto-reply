"""
闲鱼自动回复系统 - 发货规则模块
负责匹配发货规则和获取发货内容
"""

import json
from typing import Optional, Dict, Any
from loguru import logger

from app.services.xianyu.common import safe_str


class DeliveryRules:
    """发货规则处理器"""

    def __init__(self, parent):
        self.parent = parent

    def _safe_str(self, obj) -> str:
        """安全转换为字符串"""
        return safe_str(obj)

    async def _get_item_search_text(self, item_id: str, item_title: Optional[str] = None) -> str:
        """获取用于规则匹配的搜索文本

        Args:
            item_id: 商品ID
            item_title: 默认商品标题

        Returns:
            str: 搜索文本
        """
        search_text = item_title

        if item_id and item_id != "未知商品":
            try:
                item_info = await self.parent.get_item_info(item_id)
                if item_info and 'data' in item_info:
                    data = item_info['data']
                    item_data = data['itemDO']
                    shareData = item_data['shareData']
                    shareInfoJsonString = shareData['shareInfoJsonString']

                    try:
                        share_info = json.loads(shareInfoJsonString)
                        content = share_info.get('contentParams', {}).get('mainParams', {}).get('content', '')
                        if content:
                            search_text = content
                            logger.info(f"API extracted content: {content[:100]}...")
                        else:
                            search_text = shareInfoJsonString
                    except (json.JSONDecodeError, Exception) as e:
                        logger.warning(f"API JSON parse failed: {safe_str(e)}")
                        search_text = shareInfoJsonString
                else:
                    raise Exception("API response format异常")
            except Exception as e:
                logger.warning(f"API get item info failed: {self._safe_str(e)}, trying DB")
                search_text = await self._get_search_text_from_db(item_id, item_title)

        return search_text or item_id or "未知商品"

    async def _get_search_text_from_db(self, item_id: str, item_title: Optional[str] = None) -> str:
        """从数据库获取搜索文本

        Args:
            item_id: 商品ID
            item_title: 默认商品标题

        Returns:
            str: 搜索文本
        """
        from db_manager import db_manager

        try:
            db_item_info = db_manager.get_item_info(self.parent.cookie_id, item_id)
            if db_item_info:
                item_title_db = db_item_info.get('item_title', '') or ''
                item_detail_db = db_item_info.get('item_detail', '') or ''

                if not item_detail_db.strip():
                    try:
                        fetched_detail = await self.parent.fetch_item_detail_from_api(item_id)
                        if fetched_detail:
                            await self.parent.save_item_detail_only(item_id, fetched_detail)
                            item_detail_db = fetched_detail
                    except Exception as api_e:
                        logger.warning(f"External API failed: {item_id}, {self._safe_str(api_e)}")

                search_parts = []
                if item_title_db.strip():
                    search_parts.append(item_title_db.strip())
                if item_detail_db.strip():
                    search_parts.append(item_detail_db.strip())

                if search_parts:
                    search_text = ' '.join(search_parts)
                    logger.info(f"DB search text: title='{item_title_db}', detail len={len(item_detail_db)}")
                    return search_text
        except Exception as db_e:
            logger.debug(f"DB get item info failed: {self._safe_str(db_e)}")

        return item_title or item_id

    def _match_delivery_rule(self, search_text: str, spec_name: Optional[str] = None, spec_value: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """匹配发货规则

        Args:
            search_text: 搜索文本
            spec_name: 规格名称
            spec_value: 规格值

        Returns:
            Optional[Dict]: 匹配的规则
        """
        from db_manager import db_manager

        delivery_rules = []

        if spec_name and spec_value:
            logger.info(f"Trying exact match: {search_text[:50]}... [{spec_name}:{spec_value}]")
            delivery_rules = db_manager.get_delivery_rules_by_keyword_and_spec(search_text, spec_name, spec_value)
            if delivery_rules:
                logger.info(f"✅ Exact match found: {len(delivery_rules)} rules")

        if not delivery_rules:
            logger.info(f"Trying fallback match: {search_text[:50]}...")
            delivery_rules = db_manager.get_delivery_rules_by_keyword(search_text)
            if delivery_rules:
                logger.info(f"✅ Fallback match found: {len(delivery_rules)} rules")

        if not delivery_rules:
            logger.warning(f"No matching rules: {search_text[:50]}...")
            return None

        return delivery_rules[0]

    def _log_match_result(self, rule: Dict[str, Any], spec_name: Optional[str], spec_value: Optional[str]) -> None:
        """记录规则匹配结果

        Args:
            rule: 匹配的规则
            spec_name: 规格名称
            spec_value: 规格值
        """
        if rule.get('is_multi_spec'):
            if spec_name and spec_value:
                logger.info(f"🎯 Exact match: {rule['keyword']} -> {rule['card_name']} [{rule['spec_name']}:{rule['spec_value']}]")
            else:
                logger.info(f"⚠️ Multi-spec rule but no order spec: {rule['keyword']} -> {rule['card_name']}")
        else:
            logger.info(f"✅ Normal match: {rule['keyword']} -> {rule['card_name']} ({rule['card_type']})")

    async def _get_delivery_content(self, rule: Dict[str, Any], order_id: Optional[str]) -> Optional[str]:
        """获取发货内容

        Args:
            rule: 匹配的规则
            order_id: 订单ID

        Returns:
            Optional[str]: 发货内容
        """
        if not order_id:
            logger.info(f"⚠️ No order ID, skipping delivery content processing")
            return None

        logger.info(f"Processing delivery content: {rule['keyword']} -> {rule['card_name']} ({rule['card_type']})")

        delivery_content = None
        card_type = rule['card_type']

        if card_type == 'api':
            delivery_content = await self.parent._get_api_card_content(rule)
        elif card_type == 'text':
            delivery_content = rule['text_content']
        elif card_type == 'data':
            from db_manager import db_manager
            delivery_content = db_manager.consume_batch_data(rule['card_id'])
        elif card_type == 'image':
            image_url = rule.get('image_url')
            if image_url:
                delivery_content = f"__IMAGE_SEND__{rule['card_id']}|{image_url}"
                logger.info(f"Image delivery: {image_url} (card_id: {rule['card_id']})")
            else:
                logger.error(f"Image card missing URL: card_id={rule['card_id']}")

        if not delivery_content:
            logger.warning(f"Get delivery content failed: rule_id={rule['id']}")
            return None

        is_valid, error_msg = self.parent._validate_delivery_content(delivery_content)
        if not is_valid:
            logger.error(f"Delivery content validation failed: {error_msg}, rule_id={rule['id']}")
            return None

        final_content = self.parent._process_delivery_content_with_description(
            delivery_content, rule.get('card_description', '')
        )

        is_valid, error_msg = self.parent._validate_delivery_content(final_content)
        if not is_valid:
            logger.error(f"Post-process validation failed: {error_msg}, rule_id={rule['id']}")
            return None

        return final_content
