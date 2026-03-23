"""
闲鱼自动回复系统 - 发货确认模块
负责自动确认发货和免拼发货
"""

import asyncio
import time
from typing import Dict, Any, Optional
from loguru import logger

from utils.xianyu.common import safe_str


class DeliveryConfirm:
    """发货确认处理器"""

    def __init__(self, parent):
        self.parent = parent

    def _safe_str(self, obj) -> str:
        """安全转换为字符串"""
        return safe_str(obj)

    async def auto_confirm(self, order_id: str, retry_count: int = 0) -> Dict[str, Any]:
        """自动确认发货

        Args:
            order_id: 订单ID
            retry_count: 重试次数

        Returns:
            Dict[str, Any]: 确认结果
        """
        try:
            logger.debug(f"【{self.parent.cookie_id}】开始确认发货，订单ID: {order_id}")

            from app.secure_confirm_ultra import SecureConfirm

            secure_confirm = SecureConfirm(self.parent.session, self.parent.cookies_str, self.parent.cookie_id)

            secure_confirm.current_token = self.parent.current_token
            secure_confirm.last_token_refresh_time = self.parent.last_token_refresh_time
            secure_confirm.token_refresh_interval = self.parent.token_refresh_interval
            secure_confirm.refresh_token = self.parent.refresh_token

            return await secure_confirm.auto_confirm(order_id, retry_count)

        except Exception as e:
            logger.error(f"【{self.parent.cookie_id}】加密确认模块调用失败: {safe_str(e)}")
            return {"error": f"加密确认模块调用失败: {safe_str(e)}", "order_id": order_id}

    async def auto_freeshipping(self, order_id: str, item_id: str, buyer_id: str, retry_count: int = 0) -> Dict[str, Any]:
        """自动免拼发货

        Args:
            order_id: 订单ID
            item_id: 商品ID
            buyer_id: 买家ID
            retry_count: 重试次数

        Returns:
            Dict[str, Any]: 免拼发货结果
        """
        try:
            logger.debug(f"【{self.parent.cookie_id}】开始免拼发货，订单ID: {order_id}")

            from app.secure_freeshipping_ultra import SecureFreeshipping

            secure_freeshipping = SecureFreeshipping(self.parent.session, self.parent.cookies_str, self.parent.cookie_id)

            secure_freeshipping.current_token = self.parent.current_token
            secure_freeshipping.last_token_refresh_time = self.parent.last_token_refresh_time
            secure_freeshipping.token_refresh_interval = self.parent.token_refresh_interval
            secure_freeshipping.refresh_token = self.parent.refresh_token

            return await secure_freeshipping.auto_freeshipping(order_id, item_id, buyer_id, retry_count)

        except Exception as e:
            logger.error(f"【{self.parent.cookie_id}】加密免拼发货模块调用失败: {self._safe_str(e)}")
            return {"error": f"加密免拼发货模块调用失败: {self._safe_str(e)}", "order_id": order_id}

    async def _execute_delay_if_needed(self, rule: Dict[str, Any]) -> None:
        """根据规则执行延迟

        Args:
            rule: 发货规则
        """
        delay_seconds = rule.get('card_delay_seconds', 0)
        if delay_seconds and delay_seconds > 0:
            logger.info(f"Executing delay: {delay_seconds}s")
            await asyncio.sleep(delay_seconds)
            logger.info("Delay completed")

    async def _confirm_delivery_if_needed(self, order_id: Optional[str]) -> None:
        """根据需要确认发货

        Args:
            order_id: 订单ID
        """
        if not order_id:
            return

        if not self.parent.is_auto_confirm_enabled():
            logger.info(f"Auto confirm disabled, skipping: {order_id}")
            return

        current_time = time.time()
        should_confirm = True

        if order_id in self.parent.confirmed_orders:
            last_confirm_time = self.parent.confirmed_orders[order_id]
            if current_time - last_confirm_time < self.parent.order_confirm_cooldown:
                logger.info(f"Order {order_id} already confirmed within cooldown")
                should_confirm = False

        if should_confirm:
            logger.info(f"Auto confirming: order_id={order_id}")
            confirm_result = await self.auto_confirm(order_id)
            if confirm_result.get('success'):
                self.parent.confirmed_orders[order_id] = current_time
                logger.info(f"🎉 Auto confirm success: {order_id}")
            else:
                logger.warning(f"⚠️ Auto confirm failed: {confirm_result.get('error', 'unknown')}")

    async def fetch_order_detail_info(self, order_id: str) -> Optional[Dict[str, Any]]:
        """获取订单详情信息

        Args:
            order_id: 订单ID

        Returns:
            Optional[Dict[str, Any]]: 订单详情
        """
        try:
            logger.info(f"【{self.parent.cookie_id}】开始获取订单详情: {order_id}")

            from utils.order_detail_fetcher import fetch_order_detail_simple

            cookie_string = self.parent.cookies_str
            logger.debug(f"【{self.parent.cookie_id}】使用Cookie长度: {len(cookie_string) if cookie_string else 0}")

            result = await fetch_order_detail_simple(order_id, cookie_string, headless=True)

            if result:
                logger.info(f"【{self.parent.cookie_id}】订单详情获取成功: {order_id}")
                logger.info(f"【{self.parent.cookie_id}】页面标题: {result.get('title', '未知')}")

                spec_name = result.get('spec_name', '')
                spec_value = result.get('spec_value', '')

                if spec_name and spec_value:
                    logger.info(f"【{self.parent.cookie_id}】📋 规格名称: {spec_name}")
                    logger.info(f"【{self.parent.cookie_id}】📝 规格值: {spec_value}")
                    logger.info(f"【{self.parent.cookie_id}】🛍️ 订单 {order_id} 规格信息: {spec_name} -> {spec_value}")
                else:
                    logger.warning(f"【{self.parent.cookie_id}】未获取到有效的规格信息")
                    logger.warning(f"【{self.parent.cookie_id}】⚠️ 订单 {order_id} 规格信息获取失败")

                return result
            else:
                logger.warning(f"【{self.parent.cookie_id}】订单详情获取失败: {order_id}")
                return None

        except Exception as e:
            logger.error(f"【{self.parent.cookie_id}】获取订单详情异常: {safe_str(e)}")
            return None
