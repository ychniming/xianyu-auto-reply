"""
闲鱼自动回复系统 - 自动发货处理模块
处理自动发货、自动确认发货、免拼发货等逻辑
使用组合模式整合验证器、提取器、规则处理器和确认处理器
"""

import time
from typing import Optional, Dict, Any

from loguru import logger
from app.services.xianyu.common import safe_str

from app.services.xianyu.delivery_validator import DeliveryValidator
from app.services.xianyu.order_id_extractor import OrderIdExtractor
from app.services.xianyu.delivery_rules import DeliveryRules
from app.services.xianyu.delivery_confirm import DeliveryConfirm


class DeliveryHandler:
    """自动发货处理器

    使用组合模式整合：
    - DeliveryValidator: 验证发货内容
    - OrderIdExtractor: 订单ID提取
    - DeliveryRules: 规则匹配和内容获取
    - DeliveryConfirm: 确认发货
    """

    def __init__(self, parent):
        """初始化发货处理器

        Args:
            parent: 父类 XianyuLive 实例
        """
        self.parent = parent

        self.validator = DeliveryValidator(parent)
        self.extractor = OrderIdExtractor(parent)
        self.rules = DeliveryRules(parent)
        self.confirm = DeliveryConfirm(parent)

    def _validate_delivery_content(self, content: str):
        """验证发货内容"""
        return self.validator._validate_delivery_content(content)

    def _is_auto_delivery_trigger(self, message: str) -> bool:
        """检查消息是否为自动发货触发关键字"""
        return self.validator._is_auto_delivery_trigger(message)

    def _extract_order_id(self, message: dict) -> Optional[str]:
        """从消息中提取订单ID"""
        return self.extractor._extract_order_id(message)

    def can_auto_delivery(self, order_id: str) -> bool:
        """检查是否可以进行自动发货（防重复发货）"""
        if not order_id:
            return True

        current_time = time.time()
        last_delivery = self.parent.last_delivery_time.get(order_id, 0)

        if current_time - last_delivery < self.parent.delivery_cooldown:
            logger.info(f"【{self.parent.cookie_id}】订单 {order_id} 在冷却期内，跳过自动发货")
            return False

        return True

    def mark_delivery_sent(self, order_id: str) -> None:
        """标记订单已发货"""
        if order_id:
            self.parent.last_delivery_time[order_id] = time.time()
            logger.debug(f"【{self.parent.cookie_id}】标记订单 {order_id} 已发货")
        else:
            logger.debug(f"【{self.parent.cookie_id}】无订单ID，跳过发货标记")

    async def _handle_auto_delivery(self, websocket, message: dict, send_user_name: str, send_user_id: str,
                                   item_id: str, chat_id: str, msg_time: str) -> None:
        """统一处理自动发货逻辑"""
        try:
            order_id = self._extract_order_id(message)

            if order_id:
                logger.info(f'[{msg_time}] 【{self.parent.cookie_id}】提取到订单ID: {order_id}，将在自动发货时处理确认发货')
            else:
                logger.warning(f'[{msg_time}] 【{self.parent.cookie_id}】❌ 未能提取到订单ID')

            if not self.can_auto_delivery(order_id):
                return

            user_url = f'https://www.goofish.com/personal?userId={send_user_id}'

            try:
                item_title = "待获取商品信息"

                logger.info(f"【{self.parent.cookie_id}】准备自动发货: item_id={item_id}, item_title={item_title}")

                delivery_content = await self._auto_delivery(item_id, item_title, order_id)

                if delivery_content:
                    self.mark_delivery_sent(order_id)

                    if delivery_content.startswith("__IMAGE_SEND__"):
                        image_data = delivery_content.replace("__IMAGE_SEND__", "")
                        if "|" in image_data:
                            card_id_str, image_url = image_data.split("|", 1)
                            try:
                                card_id = int(card_id_str)
                            except ValueError:
                                logger.error(f"无效的卡券ID: {card_id_str}")
                                card_id = None
                        else:
                            card_id = None
                            image_url = image_data

                        try:
                            await self.parent.send_image_msg(websocket, chat_id, send_user_id, image_url, card_id=card_id)
                            logger.info(f'[{msg_time}] 【自动发货图片】已向 {user_url} 发送图片: {image_url}')
                            await self.parent.send_delivery_failure_notification(send_user_name, send_user_id, item_id, "发货成功")
                        except Exception as e:
                            logger.error(f"自动发货图片失败: {safe_str(e)}")
                            await self.parent.send_msg(websocket, chat_id, send_user_id, "抱歉，图片发送失败，请联系客服。")
                            await self.parent.send_delivery_failure_notification(send_user_name, send_user_id, item_id, "图片发送失败")
                    else:
                        await self.parent.send_msg(websocket, chat_id, send_user_id, delivery_content)
                        logger.info(f'[{msg_time}] 【自动发货】已向 {user_url} 发送发货内容')
                        await self.parent.send_delivery_failure_notification(send_user_name, send_user_id, item_id, "发货成功")
                else:
                    logger.warning(f'[{msg_time}] 【自动发货】未找到匹配的发货规则或获取发货内容失败')
                    await self.parent.send_delivery_failure_notification(send_user_name, send_user_id, item_id, "未找到匹配的发货规则或获取发货内容失败")

            except Exception as e:
                logger.error(f"自动发货处理异常: {safe_str(e)}")
                await self.parent.send_delivery_failure_notification(send_user_name, send_user_id, item_id, f"自动发货处理异常: {str(e)}")

        except Exception as e:
            logger.error(f"统一自动发货处理异常: {self._safe_str(e)}")

    async def _auto_delivery(self, item_id: str, item_title: str = None, order_id: str = None) -> Optional[str]:
        """自动发货主流程"""
        try:
            from db_manager import db_manager

            logger.info(f"Auto delivery start: item_id={item_id}")

            search_text = await self.rules._get_item_search_text(item_id, item_title)
            logger.info(f"Search text: {search_text[:100]}...")

            is_multi_spec = db_manager.get_item_multi_spec_status(self.parent.cookie_id, item_id)
            spec_name, spec_value = await self._get_item_spec_info(item_id, order_id, is_multi_spec)

            rule = self.rules._match_delivery_rule(search_text, spec_name, spec_value)
            if not rule:
                return None

            await self._save_item_info_if_needed(item_id, search_text, rule)

            self.rules._log_match_result(rule, spec_name, spec_value)

            await self.confirm._execute_delay_if_needed(rule)

            await self.confirm._confirm_delivery_if_needed(order_id)

            delivery_content = await self.rules._get_delivery_content(rule, order_id)
            if delivery_content:
                db_manager.increment_delivery_times(rule['id'])
                logger.info(f"Auto delivery success: rule_id={rule['id']}, len={len(delivery_content)}")
                return delivery_content

            return None

        except Exception as e:
            logger.error(f"Auto delivery failed: {safe_str(e)}")
            return None

    async def _save_item_info_if_needed(self, item_id: str, search_text: str, rule: Dict[str, Any]) -> None:
        """根据需要保存商品信息"""
        try:
            from db_manager import db_manager
            db_item_info = db_manager.get_item_info(self.parent.cookie_id, item_id)
            if db_item_info:
                item_title = db_item_info.get('item_title', '').strip()
                if item_title:
                    await self.parent.save_item_info_to_db(item_id, search_text, item_title)
        except Exception:
            pass

    async def _get_item_spec_info(self, item_id: str, order_id: Optional[str], is_multi_spec: bool) -> tuple:
        """获取多规格商品的规格信息"""
        if not is_multi_spec or not order_id:
            return None, None

        try:
            order_detail = await self.confirm.fetch_order_detail_info(order_id)
            if order_detail:
                spec_name = order_detail.get('spec_name', '')
                spec_value = order_detail.get('spec_value', '')
                if spec_name and spec_value:
                    logger.info(f"Got spec info: {spec_name} = {spec_value}")
                    return spec_name, spec_value
        except Exception as e:
            logger.error(f"Get order spec info failed: {safe_str(e)}")

        return None, None

    async def auto_confirm(self, order_id: str, retry_count: int = 0) -> Dict[str, Any]:
        """自动确认发货"""
        return await self.confirm.auto_confirm(order_id, retry_count)

    async def auto_freeshipping(self, order_id: str, item_id: str, buyer_id: str, retry_count: int = 0) -> Dict[str, Any]:
        """自动免拼发货"""
        return await self.confirm.auto_freeshipping(order_id, item_id, buyer_id, retry_count)

    async def fetch_order_detail_info(self, order_id: str) -> Optional[Dict[str, Any]]:
        """获取订单详情信息"""
        return await self.confirm.fetch_order_detail_info(order_id)

    def _safe_str(self, obj) -> str:
        """安全转换为字符串"""
        return safe_str(obj)
