"""
闲鱼自动回复系统 - WebSocket核心模块
负责WebSocket连接管理、心跳、消息收发等核心功能
"""

import asyncio
import json
import re
import time
import base64
import os
import sys
from typing import Optional, Dict, Any, List, AsyncIterator
from loguru import logger
import websockets
import aiohttp

from utils.xianyu_utils import (
    generate_mid, generate_uuid, trans_cookies,
    generate_device_id, generate_sign
)
from configs.config import (
    WEBSOCKET_URL, HEARTBEAT_INTERVAL, HEARTBEAT_TIMEOUT,
    TOKEN_REFRESH_INTERVAL, TOKEN_RETRY_INTERVAL, config, COOKIES_STR,
    LOG_CONFIG, DEFAULT_HEADERS, WEBSOCKET_HEADERS,
    APP_CONFIG, API_ENDPOINTS
)

# 导入拆分出的处理器模块
from utils.xianyu.xianyu_message_handler import MessageHandler
from utils.xianyu.xianyu_delivery_handler import DeliveryHandler
from utils.xianyu.xianyu_notification_handler import NotificationHandler
from utils.xianyu.token_manager import TokenManager
from utils.xianyu.item_manager import ItemManager
from utils.xianyu.image_message_manager import ImageMessageManager


class _Constants:
    """系统常量类 - 消除魔法数字"""
    # 防重复机制时间配置（秒）
    NOTIFICATION_COOLDOWN = 300        # 通知防重复：5分钟
    DELIVERY_COOLDOWN = 600            # 发货防重复：10分钟
    ORDER_CONFIRM_COOLDOWN = 600       # 确认发货防重复：10分钟

    # 超时配置（秒）
    REGISTER_TIMEOUT = 5.0             # 注册响应超时
    SYNC_TIMEOUT = 5.0                # 同步响应超时
    API_TIMEOUT = 10                   # API调用超时
    SESSION_TIMEOUT = 30               # Session超时

    # 图片尺寸
    DEFAULT_IMAGE_WIDTH = 800
    DEFAULT_IMAGE_HEIGHT = 600

    # Token验证
    MIN_TOKEN_LENGTH = 10

    # 重试配置
    MAX_API_RETRIES = 4
    API_RETRY_WAIT_BASE = 2            # 重试等待时间基数（秒）

    # WebSocket连接参数关键字
    EXTRA_HEADERS_KEYWORDS = ["extra_headers", "unexpected keyword argument"]
    ADDITIONAL_HEADERS_KEYWORDS = ["additional_headers", "unexpected keyword argument"]

    # 错误码判断
    WS_NORMAL_CLOSE_KEYWORDS = ["1000", "sent", "received"]


# 实例化常量（供类外部使用）
CONSTANTS = _Constants()


def _setup_logger():
    """配置日志"""
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"xianyu_{time.strftime('%Y-%m-%d')}.log")
    log_format = LOG_CONFIG.get('format', '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>')
    logger.remove()
    logger.add(log_path, rotation=LOG_CONFIG.get('rotation', '1 day'), retention=LOG_CONFIG.get('retention', '7 days'), compression=LOG_CONFIG.get('compression', 'zip'), level=LOG_CONFIG.get('level', 'INFO'), format=log_format, encoding='utf-8', enqueue=True)
    logger.add(sys.stdout, level=LOG_CONFIG.get('level', 'INFO'), format=log_format, enqueue=True)


_setup_logger()


class XianyuLive:
    """闲鱼WebSocket核心类"""

    # 辅助方法（供拆分模块调用）
    def _safe_str(self, e: Exception) -> str:
        """安全地将异常转换为字符串"""
        try:
            return str(e)
        except Exception:
            try:
                return repr(e)
            except Exception:
                return "未知错误"

    def generate_mid(self) -> str:
        """生成消息ID"""
        return generate_mid()

    def __init__(self, cookies_str: Optional[str] = None, cookie_id: str = "default", user_id: int = None):
        """初始化闲鱼直播类"""
        logger.info(f"【{cookie_id}】开始初始化XianyuLive...")

        if not cookies_str:
            cookies_str = COOKIES_STR
        if not cookies_str:
            raise ValueError("未提供cookies，请在global_config.yml中配置COOKIES_STR或通过参数传入")

        logger.info(f"【{cookie_id}】解析cookies...")
        self.cookies = trans_cookies(cookies_str)
        logger.info(f"【{cookie_id}】cookies解析完成，包含字段: {list(self.cookies.keys())}")

        self.cookie_id = cookie_id  # 唯一账号标识
        self.cookies_str = cookies_str  # 保存原始cookie字符串
        self.user_id = user_id  # 保存用户ID，用于token刷新时保持正确的所有者关系
        self.base_url = WEBSOCKET_URL

        if 'unb' not in self.cookies:
            raise ValueError(f"【{cookie_id}】Cookie中缺少必需的'unb'字段，当前字段: {list(self.cookies.keys())}")

        self.myid = self.cookies['unb']
        logger.info(f"【{cookie_id}】用户ID: {self.myid}")
        self.device_id = generate_device_id(self.myid)

        # 心跳相关配置
        self.heartbeat_interval = HEARTBEAT_INTERVAL
        self.heartbeat_timeout = HEARTBEAT_TIMEOUT
        self.last_heartbeat_time = 0
        self.last_heartbeat_response = 0
        self.heartbeat_task = None
        self.token_refresh_task = None
        self.ws = None
        self.connection_restart_flag = False  # 连接重启标志

        # 通知防重复机制
        self.last_notification_time = {}  # 记录每种通知类型的最后发送时间
        self.notification_cooldown = CONSTANTS.NOTIFICATION_COOLDOWN

        # 自动发货防重复机制
        self.last_delivery_time = {}  # 记录每个商品的最后发货时间
        self.delivery_cooldown = CONSTANTS.DELIVERY_COOLDOWN

        # 自动确认发货防重复机制
        self.confirmed_orders = {}  # 记录已确认发货的订单，防止重复确认
        self.order_confirm_cooldown = CONSTANTS.ORDER_CONFIRM_COOLDOWN

        self.session = None  # 用于API调用的aiohttp session

        # 初始化拆分出的处理器
        self.message_handler = MessageHandler(self)
        self.delivery_handler = DeliveryHandler(self)
        self.notification_handler = NotificationHandler(self)
        self.token_manager = TokenManager(self)
        self.item_manager = ItemManager(self)
        self.image_message_manager = ImageMessageManager(self)

    # -------------------- WebSocket连接降级策略 --------------------

    async def _use_websocket_with_fallback(
        self,
        headers: Optional[Dict[str, str]],
        connection_handler
    ) -> None:
        """统一的WebSocket连接建立方法，支持降级策略

        Args:
            headers: WebSocket连接头信息
            connection_handler: 连接建立后的处理函数，接收websocket参数
        """
        extra_headers = headers.copy() if headers else {}

        try:
            # 策略1: 尝试 extra_headers 参数（较新版本）
            websocket = await websockets.connect(
                self.base_url,
                extra_headers=extra_headers
            )
            logger.info(f"【{self.cookie_id}】WebSocket连接建立成功（extra_headers）!")
        except Exception as e:
            error_msg = self._safe_str(e)
            if any(keyword in error_msg for keyword in CONSTANTS.EXTRA_HEADERS_KEYWORDS):
                logger.warning("websockets库不支持extra_headers参数，尝试additional_headers")
                try:
                    # 策略2: 尝试 additional_headers 参数
                    websocket = await websockets.connect(
                        self.base_url,
                        additional_headers=extra_headers
                    )
                    logger.info(f"【{self.cookie_id}】WebSocket连接建立成功（additional_headers）!")
                except Exception as e2:
                    error_msg2 = self._safe_str(e2)
                    if any(keyword in error_msg2 for keyword in CONSTANTS.ADDITIONAL_HEADERS_KEYWORDS):
                        # 策略3: 使用基础连接模式
                        logger.warning("websockets库不支持headers参数，使用基础连接模式")
                        websocket = await websockets.connect(self.base_url)
                        logger.info(f"【{self.cookie_id}】WebSocket连接建立成功（基础模式）!")
                    else:
                        raise e2
            else:
                raise e

        # 执行连接后的处理逻辑
        try:
            await connection_handler(websocket)
        finally:
            await websocket.close()

    # -------------------- 防重复发货相关方法（供拆分模块调用） --------------------

    def is_auto_confirm_enabled(self) -> bool:
        """检查当前账号是否启用自动确认发货"""
        try:
            from db_manager import db_manager
            return db_manager.get_auto_confirm(self.cookie_id)
        except Exception as e:
            logger.error(f"【{self.cookie_id}】获取自动确认发货设置失败: {self._safe_str(e)}")
            return True  # 出错时默认启用

    # -------------------- Token刷新相关方法 --------------------

    async def refresh_token(self) -> Optional[str]:
        """刷新token"""
        return await self.token_manager.refresh_token()

    async def update_config_cookies(self) -> None:
        """更新数据库中的cookies"""
        await self.token_manager._update_config_cookies()

    @property
    def current_token(self) -> Optional[str]:
        """获取当前token"""
        return self.token_manager.current_token

    @property
    def last_token_refresh_time(self) -> float:
        """获取上次token刷新时间"""
        return self.token_manager.last_token_refresh_time

    @property
    def token_refresh_interval(self) -> float:
        """获取token刷新间隔"""
        return self.token_manager.token_refresh_interval

    @property
    def token_retry_interval(self) -> float:
        """获取token重试间隔"""
        return self.token_manager.token_retry_interval

    # -------------------- 商品信息相关方法 --------------------

    async def save_item_info_to_db(self, item_id: str, item_detail: str = None, item_title: str = None) -> None:
        """保存商品信息到数据库"""
        await self.item_manager.save_item_info_to_db(item_id, item_detail, item_title)

    async def save_item_detail_only(self, item_id: str, item_detail: str) -> bool:
        """仅保存商品详情（不影响标题等基本信息）"""
        return await self.item_manager.save_item_detail_only(item_id, item_detail)

    async def fetch_item_detail_from_api(self, item_id: str) -> str:
        """从外部API获取商品详情"""
        return await self.item_manager.fetch_item_detail_from_api(item_id)

    async def save_items_list_to_db(self, items_list: List[Dict[str, Any]]) -> int:
        """批量保存商品列表信息到数据库（并发安全）"""
        return await self.item_manager.save_items_list_to_db(items_list)

    async def _fetch_missing_item_details(self, items_need_detail: List[Dict[str, str]]) -> int:
        """批量获取缺失的商品详情"""
        return await self.item_manager._fetch_missing_item_details(items_need_detail)

    async def get_item_info(self, item_id: str, retry_count: int = 0) -> Dict[str, Any]:
        """获取商品信息，自动处理token失效的情况"""
        return await self.item_manager.get_item_info(item_id, retry_count)

    # -------------------- 图片关键词相关方法 --------------------

    async def _handle_image_keyword(self, keyword: str, image_url: str, send_user_name: str, send_user_id: str, send_message: str) -> str:
        """处理图片类型关键词"""
        from src.handlers.image_handler import ImageHandler
        handler = ImageHandler(self.cookie_id, self.cookies_str)
        return await handler.handle_image_keyword(keyword, image_url)

    def _is_cdn_url(self, url: str) -> bool:
        """检查URL是否是闲鱼CDN链接"""
        from src.handlers.image_handler import ImageHandler
        return ImageHandler.is_cdn_url(url)

    async def _update_keyword_image_url(self, keyword: str, new_image_url: str) -> None:
        """更新关键词的图片URL"""
        from src.handlers.image_handler import ImageHandler
        handler = ImageHandler(self.cookie_id, self.cookies_str)
        await handler.update_keyword_image_url(keyword, new_image_url)

    async def _update_card_image_url(self, card_id: int, new_image_url: str) -> None:
        """更新卡券的图片URL"""
        from src.handlers.image_handler import ImageHandler
        handler = ImageHandler(self.cookie_id, self.cookies_str)
        await handler.update_card_image_url(card_id, new_image_url)

    def _parse_price(self, price_str: str) -> float:
        """解析价格字符串为数字"""
        try:
            if not price_str:
                return 0.0
            price_clean = re.sub(r'[^\d.]', '', str(price_str))
            return float(price_clean) if price_clean else 0.0
        except Exception:
            return 0.0

    # -------------------- 发货相关方法 --------------------

    async def _auto_delivery(self, item_id: str, item_title: str = None, order_id: str = None) -> Optional[str]:
        """自动发货功能"""
        return await self.delivery_handler._auto_delivery(item_id, item_title, order_id)

    async def auto_confirm(self, order_id: str, retry_count: int = 0) -> Dict[str, Any]:
        """自动确认发货"""
        return await self.delivery_handler.auto_confirm(order_id, retry_count)

    async def auto_freeshipping(self, order_id: str, item_id: str, buyer_id: str, retry_count: int = 0) -> Dict[str, Any]:
        """自动免拼发货"""
        return await self.delivery_handler.auto_freeshipping(order_id, item_id, buyer_id, retry_count)

    async def fetch_order_detail_info(self, order_id: str) -> Optional[Dict[str, Any]]:
        """获取订单详情信息"""
        return await self.delivery_handler.fetch_order_detail_info(order_id)

    def _process_delivery_content_with_description(self, delivery_content: str, card_description: str) -> str:
        """处理发货内容和备注信息，实现变量替换"""
        try:
            if not card_description or not card_description.strip():
                return delivery_content

            processed_description = card_description.replace('{DELIVERY_CONTENT}', delivery_content)

            if '{DELIVERY_CONTENT}' in card_description:
                return processed_description
            else:
                return f"{processed_description}\n\n{delivery_content}"

        except Exception as e:
            logger.error(f"处理备注信息失败: {e}")
            return delivery_content

    async def _get_api_card_content(self, rule: Dict[str, Any], retry_count: int = 0) -> Optional[str]:
        """调用API获取卡券内容，支持重试机制"""
        max_retries = CONSTANTS.MAX_API_RETRIES

        if retry_count >= max_retries:
            logger.error(f"API调用失败，已达到最大重试次数({max_retries})")
            return None

        try:
            import aiohttp

            api_config = rule.get('api_config')
            if not api_config:
                logger.error(f"API配置为空，规则ID: {rule.get('id')}, 卡券名称: {rule.get('card_name')}")
                logger.debug(f"规则详情: {rule}")
                return None

            if isinstance(api_config, str):
                api_config = json.loads(api_config)

            url = api_config.get('url')
            method = api_config.get('method', 'GET').upper()
            timeout = api_config.get('timeout', CONSTANTS.API_TIMEOUT)
            headers = api_config.get('headers', '{}')
            params = api_config.get('params', '{}')

            if isinstance(headers, str):
                headers = json.loads(headers)
            if isinstance(params, str):
                params = json.loads(params)

            retry_info = f" (重试 {retry_count + 1}/{max_retries})" if retry_count > 0 else ""
            logger.info(f"调用API获取卡券: {method} {url}{retry_info}")

            if not self.session:
                await self.create_session()

            timeout_obj = aiohttp.ClientTimeout(total=timeout)

            if method == 'GET':
                async with self.session.get(url, headers=headers, params=params, timeout=timeout_obj) as response:
                    status_code = response.status
                    response_text = await response.text()
            elif method == 'POST':
                async with self.session.post(url, headers=headers, json=params, timeout=timeout_obj) as response:
                    status_code = response.status
                    response_text = await response.text()
            else:
                logger.error(f"不支持的HTTP方法: {method}")
                return None

            if status_code == 200:
                try:
                    result = json.loads(response_text)
                    if isinstance(result, dict):
                        content = result.get('data') or result.get('content') or result.get('card') or str(result)
                    else:
                        content = str(result)
                except Exception:
                    content = response_text

                logger.info(f"API调用成功，返回内容长度: {len(content)}")
                return content
            else:
                logger.warning(f"API调用失败: {status_code} - {response_text[:200]}...")

                if status_code >= 500 or status_code == 408:
                    if retry_count < max_retries - 1:
                        wait_time = (retry_count + 1) * CONSTANTS.API_RETRY_WAIT_BASE
                        logger.info(f"等待 {wait_time} 秒后重试...")
                        await asyncio.sleep(wait_time)
                        return await self._get_api_card_content(rule, retry_count + 1)

                return None

        except (aiohttp.ClientTimeout, aiohttp.ClientError) as e:
            logger.warning(f"API调用网络异常: {self._safe_str(e)}")

            if retry_count < max_retries - 1:
                wait_time = (retry_count + 1) * CONSTANTS.API_RETRY_WAIT_BASE
                logger.info(f"等待 {wait_time} 秒后重试...")
                await asyncio.sleep(wait_time)
                return await self._get_api_card_content(rule, retry_count + 1)
            else:
                logger.error(f"API调用网络异常，已达到最大重试次数: {self._safe_str(e)}")
                return None

        except Exception as e:
            logger.error(f"API调用异常: {self._safe_str(e)}")
            return None

    # -------------------- 消息处理代理方法 --------------------

    def _is_auto_delivery_trigger(self, message: str) -> bool:
        """检查消息是否为自动发货触发关键字"""
        return self.delivery_handler._is_auto_delivery_trigger(message)

    def _extract_order_id(self, message: dict) -> Optional[str]:
        """从消息中提取订单ID"""
        return self.delivery_handler._extract_order_id(message)

    def can_auto_delivery(self, order_id: str) -> bool:
        """检查是否可以进行自动发货"""
        return self.delivery_handler.can_auto_delivery(order_id)

    def mark_delivery_sent(self, order_id: str) -> None:
        """标记订单已发货"""
        self.delivery_handler.mark_delivery_sent(order_id)

    async def _handle_auto_delivery(self, websocket, message: dict, send_user_name: str, send_user_id: str,
                                   item_id: str, chat_id: str, msg_time: str) -> None:
        """统一处理自动发货逻辑"""
        await self.delivery_handler._handle_auto_delivery(websocket, message, send_user_name, send_user_id, item_id, chat_id, msg_time)

    async def send_notification(self, send_user_name: str, send_user_id: str, send_message: str, item_id: str = None) -> None:
        """发送消息通知"""
        await self.notification_handler.send_notification(send_user_name, send_user_id, send_message, item_id)

    async def send_token_refresh_notification(self, error_message: str, notification_type: str = "token_refresh") -> None:
        """发送Token刷新异常通知"""
        await self.notification_handler.send_token_refresh_notification(error_message, notification_type)

    async def send_delivery_failure_notification(self, send_user_name: str, send_user_id: str, item_id: str, error_message: str) -> None:
        """发送自动发货失败通知"""
        await self.notification_handler.send_delivery_failure_notification(send_user_name, send_user_id, item_id, error_message)

    # -------------------- 消息处理方法 --------------------

    async def handle_message(self, message_data: dict, websocket) -> None:
        """处理所有类型的消息"""
        await self.message_handler.handle_message(message_data, websocket)

    async def handle_heartbeat_response(self, message_data: dict) -> bool:
        """处理心跳响应"""
        return await self.message_handler.handle_heartbeat_response(message_data)

    # -------------------- Token刷新循环 --------------------

    async def token_refresh_loop(self) -> None:
        """Token刷新循环"""
        while True:
            try:
                from src import cookie_manager as cm
                if cm.manager and not cm.manager.get_cookie_status(self.cookie_id):
                    logger.info(f"【{self.cookie_id}】账号已禁用，停止Token刷新循环")
                    break

                current_time = time.time()
                if current_time - self.last_token_refresh_time >= self.token_refresh_interval:
                    logger.info("Token即将过期，准备刷新...")
                    new_token = await self.refresh_token()
                    if new_token:
                        logger.info(f"【{self.cookie_id}】Token刷新成功，准备重新建立连接...")
                        self.connection_restart_flag = True
                        if self.ws:
                            await self.ws.close()
                        break
                    else:
                        logger.error(f"【{self.cookie_id}】Token刷新失败，将在{self.token_retry_interval // 60}分钟后重试")
                        await self.send_token_refresh_notification("Token定时刷新失败，将自动重试", "token_scheduled_refresh_failed")
                        await asyncio.sleep(self.token_retry_interval)
                        continue
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Token刷新循环出错: {self._safe_str(e)}")
                await asyncio.sleep(60)

    # -------------------- WebSocket消息发送 --------------------

    async def create_chat(self, ws, toid: str, item_id: str = '891198795482') -> None:
        """创建聊天会话"""
        msg = {
            "lwp": "/r/SingleChatConversation/create",
            "headers": {"mid": generate_mid()},
            "body": [
                {
                    "pairFirst": f"{toid}@goofish",
                    "pairSecond": f"{self.myid}@goofish",
                    "bizType": "1",
                    "extension": {"itemId": item_id},
                    "ctx": {"appVersion": "1.0", "platform": "web"}
                }
            ]
        }
        await ws.send(json.dumps(msg))

    async def send_msg(self, ws, cid: str, toid: str, text: str) -> None:
        """发送文本消息"""
        text_content = {
            "contentType": 1,
            "text": {"text": text}
        }
        text_base64 = str(base64.b64encode(json.dumps(text_content).encode('utf-8')), 'utf-8')
        msg = {
            "lwp": "/r/MessageSend/sendByReceiverScope",
            "headers": {"mid": generate_mid()},
            "body": [
                {
                    "uuid": generate_uuid(),
                    "cid": f"{cid}@goofish",
                    "conversationType": 1,
                    "content": {
                        "contentType": 101,
                        "custom": {"type": 1, "data": text_base64}
                    },
                    "redPointPolicy": 0,
                    "extension": {"extJson": "{}"},
                    "ctx": {"appVersion": "1.0", "platform": "web"},
                    "mtags": {},
                    "msgReadStatusSetting": 1
                },
                {
                    "actualReceivers": [f"{toid}@goofish", f"{self.myid}@goofish"]
                }
            ]
        }
        await ws.send(json.dumps(msg))

    async def init(self, ws) -> None:
        """初始化 WebSocket 连接，支持降级策略

        使用早返回模式减少嵌套层级。
        """
        # ---------- Token获取阶段 ----------
        if not self.current_token or (time.time() - self.last_token_refresh_time) >= self.token_refresh_interval:
            logger.info(f"【{self.cookie_id}】获取初始 token...")
            await self.refresh_token()

        # ---------- Token降级获取 ----------
        if not self.current_token:
            logger.warning(f"【{self.cookie_id}】Token刷新失败，尝试从Cookie中提取临时token...")
            m_h5_tk = self._extract_token_from_cookie()
            if m_h5_tk:
                self.token_manager.current_token = m_h5_tk
                logger.info(f"【{self.cookie_id}】成功提取临时token: {self.token_manager.current_token[:10]}...")
            else:
                logger.error(f"【{self.cookie_id}】无法获取有效token，初始化失败")
                await self._notify_token_init_failure()
                raise Exception("Token获取失败")

        # ---------- Token验证 ----------
        token_info = self._validate_token()
        if not token_info:
            raise Exception(f"Token格式无效")

        logger.debug(f"【{self.cookie_id}】Token验证通过：{token_info}")

        # ---------- 发送注册消息 ----------
        await self._send_register_message(ws)

        # ---------- 发送同步消息 ----------
        await self._send_sync_message(ws)

        logger.info(f"【{self.cookie_id}】连接注册完成")

    def _extract_token_from_cookie(self) -> Optional[str]:
        """从Cookie中提取token"""
        try:
            from utils.xianyu_utils import trans_cookies
            cookies_dict = trans_cookies(self.cookies_str)
            m_h5_tk = cookies_dict.get('_m_h5_tk', '')
            if m_h5_tk:
                return m_h5_tk.split('_')[0]
        except Exception as e:
            logger.error(f"【{self.cookie_id}】提取临时token失败：{self._safe_str(e)}")
        return None

    def _validate_token(self) -> Optional[str]:
        """验证token格式并返回token信息"""
        if not self.current_token:
            return None
        if len(self.current_token) < CONSTANTS.MIN_TOKEN_LENGTH:
            logger.error(f"【{self.cookie_id}】Token格式异常：长度={len(self.current_token)}")
            return None
        return f"{self.current_token[:5]}...{self.current_token[-5:]}"

    async def _notify_token_init_failure(self) -> None:
        """发送初始化token失败通知"""
        await self.send_token_refresh_notification("初始化时无法获取有效Token", "token_init_failed")

    async def _send_register_message(self, ws) -> None:
        """发送注册消息并处理响应"""
        msg = {
            "lwp": "/reg",
            "headers": {
                "cache-header": "app-key token ua wv",
                "app-key": APP_CONFIG.get('app_key'),
                "token": self.current_token,
                "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 DingTalk(2.1.5) OS(Windows/10) Browser(Chrome/133.0.0.0) DingWeb/2.1.5 IMPaaS DingWeb/2.1.5",
                "dt": "j",
                "wv": "im:3,au:3,sy:6",
                "sync": "0,0;0;0;",
                "did": self.device_id,
                "mid": generate_mid()
            }
        }
        logger.debug(f"【{self.cookie_id}】发送注册消息：{json.dumps(msg, ensure_ascii=False)[:200]}...")
        await ws.send(json.dumps(msg))
        logger.info(f"【{self.cookie_id}】注册消息发送完成，等待响应...")

        # 等待并处理注册响应（不阻塞主流程）
        try:
            response = await asyncio.wait_for(ws.recv(), timeout=CONSTANTS.REGISTER_TIMEOUT)
            response_data = json.loads(response)
            logger.info(f"【{self.cookie_id}】注册响应：{response_data.get('lwp', 'unknown')}")

            if response_data.get('lwp') == '/reg/error':
                error_info = response_data.get('error', {})
                error_code = error_info.get('code', 'unknown')
                error_msg = error_info.get('message', '未知错误')
                logger.error(f"【{self.cookie_id}】注册失败：{error_code} - {error_msg}")
        except asyncio.TimeoutError:
            logger.warning(f"【{self.cookie_id}】注册响应超时，继续执行...")

    async def _send_sync_message(self, ws) -> None:
        """发送同步消息并处理响应"""
        await asyncio.sleep(0.5)

        current_time = int(time.time() * 1000)
        msg = {
            "lwp": "/r/SyncStatus/ackDiff",
            "headers": {"mid": generate_mid()},
            "body": [
                {
                    "pipeline": "sync",
                    "tooLong2Tag": "PNM,1",
                    "channel": "sync",
                    "topic": "sync",
                    "highPts": 0,
                    "pts": current_time * 1000,
                    "seq": 0,
                    "timestamp": current_time
                }
            ]
        }
        logger.debug(f"【{self.cookie_id}】发送同步消息")
        await ws.send(json.dumps(msg))

        try:
            response = await asyncio.wait_for(ws.recv(), timeout=CONSTANTS.SYNC_TIMEOUT)
            response_data = json.loads(response)
            logger.info(f"【{self.cookie_id}】同步响应：{response_data.get('lwp', 'unknown')}")
        except asyncio.TimeoutError:
            logger.warning(f"【{self.cookie_id}】同步响应超时")

    async def send_heartbeat(self, ws) -> None:
        """发送心跳包"""
        msg = {
            "lwp": "/!",
            "headers": {"mid": generate_mid()}
        }
        await ws.send(json.dumps(msg))
        self.last_heartbeat_time = time.time()

    async def heartbeat_loop(self, ws) -> None:
        """心跳循环"""
        while True:
            try:
                from src import cookie_manager as cm
                if cm.manager and not cm.manager.get_cookie_status(self.cookie_id):
                    logger.info(f"【{self.cookie_id}】账号已禁用，停止心跳循环")
                    break

                await self.send_heartbeat(ws)
                await asyncio.sleep(self.heartbeat_interval)
            except Exception as e:
                logger.error(f"心跳发送失败: {self._safe_str(e)}")
                break

    async def send_msg_once(self, toid: str, item_id: str, text: str) -> None:
        """单次发送消息"""
        headers = {
            "Cookie": self.cookies_str,
            "Host": "wss-goofish.dingtalk.com",
            "Connection": "Upgrade",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "Origin": "https://www.goofish.com",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }

        async def connection_handler(websocket) -> None:
            """WebSocket连接建立后的处理"""
            await self._handle_websocket_connection(websocket, toid, item_id, text)

        await self._use_websocket_with_fallback(headers, connection_handler)

    async def _create_websocket_connection(self, headers: Dict[str, str]):
        """创建WebSocket连接，兼容不同版本的websockets库"""
        import websockets

        websockets_version = getattr(websockets, '__version__', '未知')
        logger.debug(f"websockets库版本: {websockets_version}")

        try:
            return websockets.connect(self.base_url, extra_headers=headers)
        except Exception as e:
            error_msg = self._safe_str(e)
            logger.debug(f"extra_headers参数失败: {error_msg}")

            if "extra_headers" in error_msg or "unexpected keyword argument" in error_msg:
                logger.warning("websockets库不支持extra_headers参数，尝试additional_headers")
                try:
                    return websockets.connect(self.base_url, additional_headers=headers)
                except Exception as e2:
                    error_msg2 = self._safe_str(e2)
                    logger.debug(f"additional_headers参数失败: {error_msg2}")

                    if "additional_headers" in error_msg2 or "unexpected keyword argument" in error_msg2:
                        logger.warning("websockets库不支持headers参数，使用基础连接模式")
                        return websockets.connect(self.base_url)
                    else:
                        raise e2
            else:
                raise e

    async def _handle_websocket_connection(self, websocket, toid: str, item_id: str, text: str) -> None:
        """处理WebSocket连接的具体逻辑"""
        await self.init(websocket)
        await self.create_chat(websocket, toid, item_id)
        async for message in websocket:
            try:
                logger.info(f"【{self.cookie_id}】message: {message}")
                message = json.loads(message)
                cid = message["body"]["singleChatConversation"]["cid"]
                cid = cid.split('@')[0]
                await self.send_msg(websocket, cid, toid, text)
                logger.info(f'【{self.cookie_id}】send message')
                return
            except Exception as e:
                pass

    async def create_session(self) -> None:
        """创建aiohttp session"""
        if not self.session:
            headers = DEFAULT_HEADERS.copy()
            headers['cookie'] = self.cookies_str
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=CONSTANTS.SESSION_TIMEOUT)
            )

    async def close_session(self) -> None:
        """关闭aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None

    # -------------------- 主程序 --------------------

    async def main(self) -> None:
        """主程序入口"""
        try:
            logger.info(f"【{self.cookie_id}】开始启动XianyuLive主程序...")
            await self.create_session()
            logger.info(f"【{self.cookie_id}】Session创建完成，开始WebSocket连接循环...")

            while True:
                # 检查账号状态
                if self._is_account_disabled():
                    break

                # 建立WebSocket连接
                websocket = await self._establish_websocket_connection()
                if not websocket:
                    await asyncio.sleep(5)
                    continue

                # 处理WebSocket连接
                await self._run_websocket_session(websocket)

        finally:
            await self.close_session()

    def _is_account_disabled(self) -> bool:
        """检查账号是否已禁用"""
        from src import cookie_manager as cm
        if cm.manager and not cm.manager.get_cookie_status(self.cookie_id):
            logger.info(f"【{self.cookie_id}】账号已禁用，停止主循环")
            return True
        return False

    async def _establish_websocket_connection(self):
        """建立WebSocket连接，使用降级策略"""
        headers = WEBSOCKET_HEADERS.copy()
        headers['Cookie'] = self.cookies_str

        logger.info(f"【{self.cookie_id}】准备建立 WebSocket 连接到：{self.base_url}")
        logger.debug(f"【{self.cookie_id}】WebSocket headers: {headers}")

        websocket = None

        # 策略1: 基础连接模式（最稳定，先尝试）
        try:
            websocket = await websockets.connect(self.base_url)
            logger.info(f"【{self.cookie_id}】WebSocket 连接建立成功（基础模式）!")
            return websocket
        except Exception as base_error:
            logger.debug(f"【{self.cookie_id}】基础模式失败: {self._safe_str(base_error)}")

        # 策略2: additional_headers（较旧版本）
        try:
            websocket = await websockets.connect(self.base_url, additional_headers=headers)
            logger.info(f"【{self.cookie_id}】WebSocket 连接建立成功（additional_headers）!")
            return websocket
        except Exception as additional_error:
            error_msg = self._safe_str(additional_error)
            if "additional_headers" not in error_msg and "unexpected keyword argument" not in error_msg:
                logger.error(f"【{self.cookie_id}】additional_headers 失败（非参数问题）: {error_msg}")
                raise additional_error
            logger.debug(f"【{self.cookie_id}】additional_headers 模式失败: {error_msg}")

        # 策略3: extra_headers（最新版本）
        try:
            websocket = await websockets.connect(self.base_url, extra_headers=headers)
            logger.info(f"【{self.cookie_id}】WebSocket 连接建立成功（extra_headers）!")
            return websocket
        except Exception as extra_error:
            error_msg = self._safe_str(extra_error)
            if "extra_headers" not in error_msg and "unexpected keyword argument" not in error_msg:
                logger.error(f"【{self.cookie_id}】extra_headers 失败（非参数问题）: {error_msg}")
                raise extra_error
            logger.debug(f"【{self.cookie_id}】extra_headers 模式失败: {error_msg}")

        logger.error(f"【{self.cookie_id}】所有 WebSocket 连接策略均失败")
        return None

    def _is_headers_param_error(self, error: Exception) -> bool:
        """判断是否为headers参数不支持的错误"""
        error_msg = self._safe_str(error)
        return any(keyword in error_msg for keyword in CONSTANTS.EXTRA_HEADERS_KEYWORDS + CONSTANTS.ADDITIONAL_HEADERS_KEYWORDS)

    async def _run_websocket_session(self, websocket) -> None:
        """运行WebSocket会话，处理消息和心跳"""
        self.ws = websocket

        logger.info(f"【{self.cookie_id}】开始初始化WebSocket连接...")
        await self.init(websocket)
        logger.info(f"【{self.cookie_id}】WebSocket初始化完成！")

        logger.info(f"【{self.cookie_id}】启动心跳任务...")
        self.heartbeat_task = asyncio.create_task(self.heartbeat_loop(websocket))

        logger.info(f"【{self.cookie_id}】启动token刷新任务...")
        self.token_refresh_task = asyncio.create_task(self.token_refresh_loop())

        logger.info(f"【{self.cookie_id}】开始监听WebSocket消息...")

        try:
            async for message in websocket:
                await self._process_websocket_message(message)
        except Exception as e:
            await self._handle_websocket_error(e)
        finally:
            self._cleanup_tasks()

    async def _process_websocket_message(self, message: str) -> None:
        """处理WebSocket消息"""
        try:
            message_data = json.loads(message)

            if await self.handle_heartbeat_response(message_data):
                return

            await self.handle_message(message_data, self.ws)

        except Exception as e:
            logger.error(f"处理消息出错: {self._safe_str(e)}")

    async def _handle_websocket_error(self, error: Exception) -> None:
        """处理WebSocket错误"""
        error_msg = self._safe_str(error)
        logger.error(f"【{self.cookie_id}】WebSocket 连接异常：{error_msg}")

        # 判断是否为正常关闭
        if all(keyword in error_msg for keyword in CONSTANTS.WS_NORMAL_CLOSE_KEYWORDS):
            logger.warning(f"【{self.cookie_id}】WebSocket 正常关闭，可能是服务器主动断开连接")
            if not self.current_token:
                logger.error(f"【{self.cookie_id}】Token 已失效，需要重新获取")
        else:
            logger.error(f"【{self.cookie_id}】WebSocket 异常断开")

        # 等待后重试
        logger.info(f"【{self.cookie_id}】将在 5 秒后重试连接...")
        await asyncio.sleep(5)

    def _cleanup_tasks(self) -> None:
        """清理任务"""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            self.heartbeat_task = None
        if self.token_refresh_task:
            self.token_refresh_task.cancel()
            self.token_refresh_task = None

    async def get_item_list_info(self, page_number: int = 1, page_size: int = 20, retry_count: int = 0) -> Dict[str, Any]:
        """获取商品信息，自动处理token失效的情况"""
        return await self.item_manager.get_item_list_info(page_number, page_size, retry_count)

    async def get_all_items(self, page_size: int = 20, max_pages: int = None) -> Dict[str, Any]:
        """获取所有商品信息（自动分页）"""
        return await self.item_manager.get_all_items(page_size, max_pages)

    async def send_image_msg(self, ws, cid: str, toid: str, image_url: str, width: int = None, height: int = None, card_id: int = None) -> None:
        """发送图片消息"""
        if width is None:
            width = CONSTANTS.DEFAULT_IMAGE_WIDTH
        if height is None:
            height = CONSTANTS.DEFAULT_IMAGE_HEIGHT
        await self.image_message_manager.send_image_msg(ws, cid, toid, image_url, width, height, card_id)

    async def send_image_from_file(self, ws, cid: str, toid: str, image_path: str) -> bool:
        """从本地文件发送图片"""
        return await self.image_message_manager.send_image_from_file(ws, cid, toid, image_path)


if __name__ == '__main__':
    cookies_str = os.getenv('COOKIES_STR')
    xianyuLive = XianyuLive(cookies_str)
    asyncio.run(xianyuLive.main())
