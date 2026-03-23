"""
自动免拼发货模块
提供自动免拼闲鱼订单发货功能
"""
import time
import aiohttp
from typing import Dict, Any
from loguru import logger
from app.base_delivery import (
    BaseDelivery,
    RetryExecutor,
    DEFAULT_RETRY_CONFIG
)


class SecureFreeshipping(BaseDelivery):
    """自动免拼发货处理器"""

    API_NAME = 'mtop.idle.groupon.activity.seller.freeshipping'

    async def auto_freeshipping(
        self,
        order_id: str,
        item_id: str,
        buyer_id: str
    ) -> Dict[str, Any]:
        """自动免拼发货

        使用统一的重试机制处理Token过期和网络异常。

        Args:
            order_id: 订单ID
            item_id: 商品ID
            buyer_id: 买家ID

        Returns:
            Dict containing success status and order_id or error message
        """
        # 使用RetryExecutor实现统一重试机制
        executor = RetryExecutor(
            config=self.retry_config,
            operation_name=f"自动免拼发货[{self.cookie_id}]",
            on_retry=self._handle_token_refresh_on_retry
        )
        return await executor.execute(self._do_auto_freeshipping, order_id, item_id, buyer_id)

    async def _do_auto_freeshipping(
        self,
        order_id: str,
        item_id: str,
        buyer_id: str
    ) -> Dict[str, Any]:
        """执行自动免拼发货的实际逻辑

        Args:
            order_id: 订单ID
            item_id: 商品ID
            buyer_id: 买家ID

        Returns:
            Dict containing success status and order_id or error message

        Raises:
            TokenExpiredError: 当检测到Token相关错误时
            NetworkError: 当发生网络异常时
        """
        # 首次执行时检查Token
        if not self.current_token or \
           (time.time() - self.last_token_refresh_time) >= self.token_refresh_interval:
            await self.refresh_token_if_needed()

        # 构建请求数据
        data_dict = {
            "bizOrderId": order_id,
            "itemId": int(item_id),
            "buyerId": int(buyer_id)
        }

        logger.info(f"【{self.cookie_id}】免拼发货请求参数: data_dict = {data_dict}")

        # 使用公共API执行方法
        return await self._execute_delivery_api(
            self.API_NAME,
            order_id,
            data_dict
        )


# 兼容旧版本的函数接口
async def secure_freeshipping(
    session: aiohttp.ClientSession,
    cookies_str: str,
    order_id: str,
    item_id: str,
    buyer_id: str,
    cookie_id: str = "default"
) -> Dict[str, Any]:
    """自动免拼发货（兼容旧版本接口）

    Args:
        session: HTTP会话
        cookies_str: Cookie字符串
        order_id: 订单ID
        item_id: 商品ID
        buyer_id: 买家ID
        cookie_id: Cookie标识

    Returns:
        Dict containing success status and order_id or error message
    """
    freeshipping = SecureFreeshipping(session, cookies_str, cookie_id)
    return await freeshipping.auto_freeshipping(order_id, item_id, buyer_id)
