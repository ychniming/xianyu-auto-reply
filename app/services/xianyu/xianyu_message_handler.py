"""
闲鱼自动回复系统 - 消息处理模块
处理消息解析、关键词匹配、AI回复等逻辑
"""

import asyncio
import json
import time
from typing import Optional

from loguru import logger

from app.services.xianyu.common import safe_str
from app.services.xianyu.message_parser import MessageParser
from app.services.xianyu.message_decryptor import MessageDecryptor
from app.services.xianyu.reply_processor import ReplyProcessor


class MessageHandler:
    """消息处理器 - 处理消息解析和回复逻辑"""

    def __init__(self, parent):
        """初始化消息处理器

        Args:
            parent: 父类 XianyuLive 实例，用于访问父类方法
        """
        self.parent = parent
        self.message_parser = MessageParser(parent)
        self.message_decryptor = MessageDecryptor(parent)
        self.reply_processor = ReplyProcessor(parent)

    async def get_default_reply(self, send_user_name: str, send_user_id: str, send_message: str) -> Optional[str]:
        """获取默认回复内容，支持变量替换"""
        return await self.reply_processor.get_default_reply(send_user_name, send_user_id, send_message)

    async def get_ai_reply(self, send_user_name: str, send_user_id: str, send_message: str, item_id: str, chat_id: str) -> Optional[str]:
        """获取AI回复"""
        return await self.reply_processor.get_ai_reply(send_user_name, send_user_id, send_message, item_id, chat_id)

    async def get_api_reply(self, msg_time: str, user_url: str, send_user_id: str, send_user_name: str, item_id: str, send_message: str, chat_id: str) -> Optional[str]:
        """调用API获取回复消息"""
        return await self.reply_processor.get_api_reply(msg_time, user_url, send_user_id, send_user_name, item_id, send_message, chat_id)

    async def handle_message(self, message_data: dict, websocket) -> None:
        """处理所有类型的消息"""
        try:
            from src import cookie_manager
            if cookie_manager and not cookie_manager.get_cookie_status(self.parent.cookie_id):
                logger.debug(f"【{self.parent.cookie_id}】账号已禁用，跳过消息处理")
                return

            try:
                message = message_data
                ack = self.message_decryptor.build_ack_message(message, self.parent.generate_mid)
                await websocket.send(json.dumps(ack))
            except Exception:
                pass

            if not self.message_parser.is_sync_package(message_data):
                return

            sync_data = message_data["body"]["syncPushPackage"]["data"][0]

            message, error = self.message_decryptor.decrypt_message(sync_data)
            if error:
                logger.error(error)
                return

            if message is None:
                return

            if not isinstance(message, dict):
                logger.error(f"消息格式错误，期望字典但得到: {type(message)}")
                return

            user_id = self.message_parser.extract_user_id(message)

            item_id = self._extract_item_id(message, user_id)

            order_status = self.message_decryptor.handle_order_status(message, user_id)
            if order_status:
                return

            if not self.message_parser.is_chat_message(message):
                logger.debug("非聊天消息")
                return

            chat_info = self.message_parser.extract_chat_info(message)
            if not chat_info:
                logger.error("提取聊天消息信息失败")
                return

            create_time = chat_info['create_time']
            send_user_name = chat_info['send_user_name']
            send_user_id = chat_info['send_user_id']
            send_message = chat_info['send_message']
            chat_id = chat_info['chat_id']

            msg_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(create_time/1000))

            if send_user_id == self.parent.myid:
                logger.info(f"[{msg_time}] 【手动发出】 商品({item_id}): {send_message}")
                return
            else:
                logger.info(f"[{msg_time}] 【收到】用户: {send_user_name} (ID: {send_user_id}), 商品({item_id}): {send_message}")

            from configs.config import AUTO_REPLY
            if not AUTO_REPLY.get('enabled', True):
                logger.info(f"[{msg_time}] 【{self.parent.cookie_id}】【系统】自动回复已禁用")
                return

            user_url = f'https://www.goofish.com/personal?userId={send_user_id}'

            reply = None
            if AUTO_REPLY.get('api', {}).get('enabled', False):
                reply = await self.get_api_reply(
                    msg_time, user_url, send_user_id, send_user_name,
                    item_id, send_message, chat_id
                )
                if not reply:
                    logger.error(f"[{msg_time}] 【API调用失败】用户: {send_user_name} (ID: {send_user_id}), 商品({item_id}): {send_message}")

            system_log = self.message_decryptor.get_system_message_log(send_message, msg_time, self.parent.cookie_id)
            if system_log:
                logger.info(system_log)
                return

            if self.parent._is_auto_delivery_trigger(send_message):
                await self.parent._handle_auto_delivery(websocket, message, send_user_name, send_user_id,
                                               item_id, chat_id, msg_time)
                return

            if send_message == '[卡片消息]':
                handled = await self._handle_card_message(
                    message, msg_time, websocket, send_user_name, send_user_id, item_id, chat_id
                )
                if handled:
                    return

            reply_source = 'API'

            if not reply:
                reply = await self.reply_processor.get_keyword_reply(send_user_name, send_user_id, send_message, item_id)
                if reply:
                    reply_source = '关键词'
                else:
                    reply = await self.get_ai_reply(send_user_name, send_user_id, send_message, item_id, chat_id)
                    if reply:
                        reply_source = 'AI'
                    else:
                        reply = await self.get_default_reply(send_user_name, send_user_id, send_message)
                        reply_source = '默认'

            await self.parent.send_notification(send_user_name, send_user_id, send_message, item_id)

            if reply:
                await self._send_reply(websocket, chat_id, send_user_id, reply, reply_source, send_user_name, item_id, msg_time)
            else:
                msg_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                logger.info(f"[{msg_time}] 【{self.parent.cookie_id}】【系统】未找到匹配的回复规则，不回复")

        except Exception as e:
            logger.error(f"处理消息时发生错误: {safe_str(e)}")
            logger.debug(f"原始消息: {message_data}")

    def _extract_item_id(self, message: dict, user_id: str) -> str:
        """提取商品ID

        Args:
            message: 消息字典
            user_id: 用户ID

        Returns:
            str: 商品ID
        """
        item_id = None
        try:
            if "1" in message and isinstance(message["1"], dict) and "10" in message["1"] and isinstance(message["1"]["10"], dict):
                url_info = message["1"]["10"].get("reminderUrl", "")
                if isinstance(url_info, str) and "itemId=" in url_info:
                    item_id = url_info.split("itemId=")[1].split("&")[0]

            if not item_id:
                item_id = self.message_parser.extract_item_id_from_message(message)

            if not item_id:
                item_id = f"auto_{user_id}_{int(time.time())}"
                logger.debug(f"无法提取商品ID，使用默认值: {item_id}")

        except Exception as e:
            logger.error(f"提取商品ID时发生错误: {safe_str(e)}")
            item_id = f"auto_{user_id}_{int(time.time())}"

        return item_id

    async def _handle_card_message(
        self,
        message: dict,
        msg_time: str,
        websocket,
        send_user_name: str,
        send_user_id: str,
        item_id: str,
        chat_id: str
    ) -> bool:
        """处理卡片消息

        Args:
            message: 消息字典
            msg_time: 消息时间
            websocket: WebSocket连接
            send_user_name: 发送者用户名
            send_user_id: 发送者用户ID
            item_id: 商品ID
            chat_id: 聊天ID

        Returns:
            bool: 是否已处理
        """
        try:
            card_info = self.message_decryptor.extract_card_info(message)
            card_title = card_info.get('title', '') if card_info else ''

            if card_title == "我已小刀，待刀成":
                logger.info(f'[{msg_time}] 【{self.parent.cookie_id}】【系统】检测到"我已小刀，待刀成"，准备自动免拼发货')
                order_id = self.parent._extract_order_id(message)
                if order_id:
                    logger.info(f'[{msg_time}] 【{self.parent.cookie_id}】延迟2秒后执行免拼发货...')
                    await asyncio.sleep(2)
                    result = await self.parent.auto_freeshipping(order_id, item_id, send_user_id)
                    if result.get('success'):
                        logger.info(f'[{msg_time}] 【{self.parent.cookie_id}】✅ 自动免拼发货成功')
                    else:
                        logger.warning(f'[{msg_time}] 【{self.parent.cookie_id}】❌ 自动免拼发货失败: {result.get("error", "未知错误")}')
                    await self.parent._handle_auto_delivery(websocket, message, send_user_name, send_user_id,
                                           item_id, chat_id, msg_time)
                    return True
                else:
                    logger.warning(f'[{msg_time}] 【{self.parent.cookie_id}】❌ 未能提取到订单ID，无法执行免拼发货')
                return True
            else:
                logger.info(f'[{msg_time}] 【{self.parent.cookie_id}】收到卡片消息，标题: {card_title or "未知"}')

        except Exception as e:
            logger.error(f"处理卡片消息异常: {safe_str(e)}")

        return False

    async def _send_reply(
        self,
        websocket,
        chat_id: str,
        send_user_id: str,
        reply: str,
        reply_source: str,
        send_user_name: str,
        item_id: str,
        msg_time: str
    ) -> None:
        """发送回复消息

        Args:
            websocket: WebSocket连接
            chat_id: 聊天ID
            send_user_id: 发送者用户ID
            reply: 回复内容
            reply_source: 回复来源
            send_user_name: 发送者用户名
            item_id: 商品ID
            msg_time: 消息时间
        """
        if reply.startswith("__IMAGE_SEND__"):
            image_url = reply.replace("__IMAGE_SEND__", "")
            try:
                await self.parent.send_image_msg(websocket, chat_id, send_user_id, image_url)
                msg_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                logger.info(f"[{msg_time}] 【{reply_source}图片发出】用户: {send_user_name} (ID: {send_user_id}), 商品({item_id}): 图片 {image_url}")
            except Exception as e:
                logger.error(f"图片发送失败: {safe_str(e)}")
                await self.parent.send_msg(websocket, chat_id, send_user_id, "抱歉，图片发送失败，请稍后重试。")
                msg_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                logger.error(f"[{msg_time}] 【{reply_source}图片发送失败】用户: {send_user_name} (ID: {send_user_id}), 商品({item_id})")
        else:
            await self.parent.send_msg(websocket, chat_id, send_user_id, reply)
            msg_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            logger.info(f"[{msg_time}] 【{reply_source}发出】用户: {send_user_name} (ID: {send_user_id}), 商品({item_id}): {reply}")

    async def handle_heartbeat_response(self, message_data: dict) -> bool:
        """处理心跳响应"""
        try:
            if message_data.get("code") == 200:
                self.parent.last_heartbeat_response = time.time()
                logger.debug("心跳响应正常")
                return True
        except Exception as e:
            logger.error(f"处理心跳响应出错: {safe_str(e)}")
        return False
