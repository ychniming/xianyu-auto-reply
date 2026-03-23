"""
闲鱼自动回复系统 - 回复处理器模块
负责关键词回复、AI回复、默认回复等逻辑
"""

import asyncio
import json
import time
from typing import Optional, Dict, Any
from datetime import datetime

from loguru import logger
from src.keyword_matcher import keyword_matcher
from configs.config import USE_NEW_KEYWORD_MATCHER, AUTO_REPLY
from utils.xianyu.common import safe_str


class ReplyProcessor:
    """回复处理器 - 负责各种回复逻辑"""

    def __init__(self, parent):
        """初始化回复处理器

        Args:
            parent: 父类 XianyuLive 实例，用于访问父类方法
        """
        self.parent = parent

    async def get_default_reply(
        self,
        send_user_name: str,
        send_user_id: str,
        send_message: str
    ) -> Optional[str]:
        """获取默认回复内容，支持变量替换

        Args:
            send_user_name: 发送者用户名
            send_user_id: 发送者用户ID
            send_message: 发送的消息内容

        Returns:
            Optional[str]: 默认回复内容
        """
        try:
            from db_manager import db_manager

            default_reply_settings = db_manager.get_default_reply(self.parent.cookie_id)

            if not default_reply_settings or not default_reply_settings.get('enabled', False):
                logger.debug(f"账号 {self.parent.cookie_id} 未启用默认回复")
                return None

            reply_content = default_reply_settings.get('reply_content', '')
            if not reply_content:
                logger.warning(f"账号 {self.parent.cookie_id} 默认回复内容为空")
                return None

            try:
                formatted_reply = reply_content.format(
                    send_user_name=send_user_name,
                    send_user_id=send_user_id,
                    send_message=send_message
                )
                logger.info(f"【{self.parent.cookie_id}】使用默认回复: {formatted_reply}")
                return formatted_reply
            except Exception as format_error:
                logger.error(f"默认回复变量替换失败: {self._safe_str(format_error)}")
                return reply_content

        except Exception as e:
            logger.error(f"获取默认回复失败: {self._safe_str(e)}")
            return None

    async def get_keyword_reply(
        self,
        send_user_name: str,
        send_user_id: str,
        send_message: str,
        item_id: str = None
    ) -> Optional[str]:
        """获取关键词匹配回复（支持商品ID优先匹配和图片类型）

        Args:
            send_user_name: 发送者用户名
            send_user_id: 发送者用户ID
            send_message: 发送的消息内容
            item_id: 商品ID（可选）

        Returns:
            Optional[str]: 匹配到的回复内容，或 None
        """
        try:
            if not send_message or not send_message.strip():
                logger.debug(f"账号 {self.parent.cookie_id} 收到空消息，跳过关键词匹配")
                return None

            MAX_MESSAGE_LENGTH = 10000
            original_length = len(send_message)
            if original_length > MAX_MESSAGE_LENGTH:
                send_message = send_message[:MAX_MESSAGE_LENGTH]
                logger.warning(
                    f"账号 {self.parent.cookie_id} 消息过长({original_length}字符)，"
                    f"已截断至{MAX_MESSAGE_LENGTH}字符"
                )

            if USE_NEW_KEYWORD_MATCHER:
                return await self._get_keyword_reply_new(
                    send_user_name, send_user_id, send_message, item_id
                )
            else:
                return await self._get_keyword_reply_old(
                    send_user_name, send_user_id, send_message, item_id
                )

        except Exception as e:
            logger.error(f"获取关键词回复失败: {self._safe_str(e)}")
            return None

    async def _get_keyword_reply_new(
        self,
        send_user_name: str,
        send_user_id: str,
        send_message: str,
        item_id: str = None
    ) -> Optional[str]:
        """使用新的关键词匹配器获取回复

        Args:
            send_user_name: 发送者用户名
            send_user_id: 发送者用户ID
            send_message: 发送的消息内容
            item_id: 商品ID（可选）

        Returns:
            Optional[str]: 匹配到的回复内容，或 None
        """
        try:
            variables = {
                'send_user_name': send_user_name,
                'send_user_id': send_user_id,
                'send_message': send_message,
                'item_id': item_id or '',
                '用户名': send_user_name,
                '用户ID': send_user_id,
                '消息内容': send_message,
                '商品ID': item_id or '',
            }

            context = self._build_keyword_match_context(
                send_user_name, send_user_id, send_message, item_id
            )

            match_result = keyword_matcher.match(
                cookie_id=self.parent.cookie_id,
                message=send_message,
                item_id=item_id,
                variables=variables,
                context=context
            )

            if not match_result:
                logger.debug(f"账号 {self.parent.cookie_id} 未找到匹配的关键词")
                return None

            keyword = match_result.get('keyword', '')
            reply = match_result.get('reply', '')
            keyword_type = match_result.get('type', 'text')
            image_url = match_result.get('image_url')
            matched_item_id = match_result.get('item_id')
            position = match_result.get('position', (0, 0))

            logger.info(
                f"账号 {self.parent.cookie_id} 关键词匹配成功: "
                f"关键词='{keyword}', 类型={keyword_type}, "
                f"商品ID={matched_item_id or '通用'}, 位置={position}"
            )

            if keyword_type == 'image' and image_url:
                logger.info(f"账号 {self.parent.cookie_id} 图片关键词回复: {image_url}")
                return await self.parent._handle_image_keyword(
                    keyword, image_url, send_user_name, send_user_id, send_message
                )
            else:
                logger.info(f"账号 {self.parent.cookie_id} 文本关键词回复: {reply}")
                return reply

        except Exception as e:
            logger.error(f"使用新匹配器获取关键词回复失败: {self._safe_str(e)}")
            return None

    def _build_keyword_match_context(
        self,
        send_user_name: str,
        send_user_id: str,
        send_message: str,
        item_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """构建关键词匹配的规则引擎上下文

        Args:
            send_user_name: 发送者用户名
            send_user_id: 发送者用户ID
            send_message: 发送的消息内容
            item_id: 商品ID（可选）

        Returns:
            Dict[str, Any]: 规则引擎上下文
        """
        now = datetime.now()
        current_time = time.time()

        user_stats = self._get_user_stats(send_user_id)
        item_info = self._get_item_info_for_context(item_id)
        trigger_count = self._get_keyword_trigger_count(send_message, item_id)

        context = {
            'time': {
                'hour': now.hour,
                'minute': now.minute,
                'weekday': now.weekday(),
                'timestamp': int(current_time)
            },
            'user': {
                'id': send_user_id,
                'name': send_user_name,
                'is_new': user_stats.get('is_new', True),
                'purchase_count': user_stats.get('purchase_count', 0),
                'message_count': user_stats.get('message_count', 0)
            },
            'item': {
                'id': item_id,
                'price': item_info.get('price'),
                'category': item_info.get('category')
            },
            'keyword': {
                'trigger_count': trigger_count,
                'message': send_message
            }
        }

        logger.debug(f"构建关键词匹配上下文: {context}")
        return context

    def _get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户统计信息

        Args:
            user_id: 用户ID

        Returns:
            Dict[str, Any]: 用户统计信息
        """
        try:
            from db_manager import db_manager

            if hasattr(db_manager, 'get_user_stats'):
                stats = db_manager.get_user_stats(self.parent.cookie_id, user_id)

                if stats:
                    return {
                        'is_new': stats.get('message_count', 0) <= 1,
                        'purchase_count': stats.get('purchase_count', 0),
                        'message_count': stats.get('message_count', 0)
                    }

            return {
                'is_new': True,
                'purchase_count': 0,
                'message_count': 0
            }

        except Exception as e:
            logger.debug(f"获取用户统计信息失败: {safe_str(e)}")
            return {
                'is_new': True,
                'purchase_count': 0,
                'message_count': 0
            }

    def _get_item_info_for_context(self, item_id: Optional[str]) -> Dict[str, Any]:
        """获取商品信息用于上下文

        Args:
            item_id: 商品ID

        Returns:
            Dict[str, Any]: 商品信息
        """
        if not item_id:
            return {}

        try:
            from db_manager import db_manager

            item_info = db_manager.get_item_info(self.parent.cookie_id, item_id)

            if item_info:
                return {
                    'price': self.parent._parse_price(item_info.get('item_price', '0')),
                    'category': item_info.get('item_category')
                }

            return {}

        except Exception as e:
            logger.debug(f"获取商品信息失败: {self._safe_str(e)}")
            return {}

    def _get_keyword_trigger_count(self, message: str, item_id: Optional[str]) -> int:
        """获取关键词触发次数

        Args:
            message: 消息内容
            item_id: 商品ID

        Returns:
            int: 触发次数
        """
        try:
            from db_manager import db_manager

            keywords = db_manager.get_keywords_with_type(self.parent.cookie_id)

            if keywords:
                for kw_data in keywords:
                    keyword = kw_data.get('keyword', '')
                    if keyword and keyword.lower() in message.lower():
                        kw_item_id = kw_data.get('item_id')
                        if kw_item_id == item_id or not kw_item_id:
                            return kw_data.get('trigger_count', 0) or 0

            return 0

        except Exception as e:
            logger.debug(f"获取关键词触发次数失败: {self._safe_str(e)}")
            return 0

    async def _get_keyword_reply_old(
        self,
        send_user_name: str,
        send_user_id: str,
        send_message: str,
        item_id: str = None
    ) -> Optional[str]:
        """使用旧的关键词匹配逻辑获取回复（向后兼容）

        Args:
            send_user_name: 发送者用户名
            send_user_id: 发送者用户ID
            send_message: 发送的消息内容
            item_id: 商品ID（可选）

        Returns:
            Optional[str]: 匹配到的回复内容，或 None
        """
        try:
            from db_manager import db_manager

            keywords = db_manager.get_keywords_with_type(self.parent.cookie_id)

            if not keywords:
                logger.debug(f"账号 {self.parent.cookie_id} 没有配置关键词")
                return None

            if item_id:
                for keyword_data in keywords:
                    keyword = keyword_data['keyword']
                    reply = keyword_data['reply']
                    keyword_item_id = keyword_data['item_id']
                    keyword_type = keyword_data.get('type', 'text')
                    image_url = keyword_data.get('image_url')

                    if keyword_item_id == item_id and keyword.lower() in send_message.lower():
                        logger.info(f"商品ID关键词匹配成功: 商品{item_id} '{keyword}' (类型: {keyword_type})")

                        if keyword_type == 'image' and image_url:
                            return await self.parent._handle_image_keyword(
                                keyword, image_url, send_user_name, send_user_id, send_message
                            )
                        else:
                            try:
                                formatted_reply = reply.format(
                                    send_user_name=send_user_name,
                                    send_user_id=send_user_id,
                                    send_message=send_message
                                )
                                logger.info(f"商品ID文本关键词回复: {formatted_reply}")
                                return formatted_reply
                            except Exception as format_error:
                                logger.error(f"关键词回复变量替换失败: {self._safe_str(format_error)}")
                                return reply

            for keyword_data in keywords:
                keyword = keyword_data['keyword']
                reply = keyword_data['reply']
                keyword_item_id = keyword_data['item_id']
                keyword_type = keyword_data.get('type', 'text')
                image_url = keyword_data.get('image_url')

                if not keyword_item_id and keyword.lower() in send_message.lower():
                    logger.info(f"通用关键词匹配成功: '{keyword}' (类型: {keyword_type})")

                    if keyword_type == 'image' and image_url:
                        return await self.parent._handle_image_keyword(
                            keyword, image_url, send_user_name, send_user_id, send_message
                        )
                    else:
                        try:
                            formatted_reply = reply.format(
                                send_user_name=send_user_name,
                                send_user_id=send_user_id,
                                send_message=send_message
                            )
                            logger.info(f"通用文本关键词回复: {formatted_reply}")
                            return formatted_reply
                        except Exception as format_error:
                            logger.error(f"关键词回复变量替换失败: {self._safe_str(format_error)}")
                            return reply

            logger.debug(f"未找到匹配的关键词: {send_message}")
            return None

        except Exception as e:
            logger.error(f"使用旧匹配器获取关键词回复失败: {safe_str(e)}")
            return None

    async def get_ai_reply(
        self,
        send_user_name: str,
        send_user_id: str,
        send_message: str,
        item_id: str,
        chat_id: str
    ) -> Optional[str]:
        """获取AI回复

        Args:
            send_user_name: 发送者用户名
            send_user_id: 发送者用户ID
            send_message: 发送的消息内容
            item_id: 商品ID
            chat_id: 聊天ID

        Returns:
            Optional[str]: AI回复内容
        """
        try:
            from src.ai_reply_engine import ai_reply_engine

            if not ai_reply_engine.is_ai_enabled(self.parent.cookie_id):
                logger.debug(f"账号 {self.parent.cookie_id} 未启用AI回复")
                return None

            from db_manager import db_manager
            item_info_raw = db_manager.get_item_info(self.parent.cookie_id, item_id)

            if not item_info_raw:
                logger.debug(f"数据库中无商品信息: {item_id}")
                item_info = {
                    'title': '商品信息获取失败',
                    'price': 0,
                    'desc': '暂无商品描述'
                }
            else:
                item_info = {
                    'title': item_info_raw.get('item_title', '未知商品'),
                    'price': self.parent._parse_price(item_info_raw.get('item_price', '0')),
                    'desc': item_info_raw.get('item_description', '暂无商品描述')
                }

            reply = ai_reply_engine.generate_reply(
                message=send_message,
                item_info=item_info,
                chat_id=chat_id,
                cookie_id=self.parent.cookie_id,
                user_id=send_user_id,
                item_id=item_id
            )

            if reply:
                logger.info(f"【{self.parent.cookie_id}】AI回复生成成功: {reply}")
                return reply
            else:
                logger.debug(f"AI回复生成失败")
                return None

        except Exception as e:
            logger.error(f"获取AI回复失败: {self._safe_str(e)}")
            return None

    async def get_api_reply(
        self,
        msg_time: str,
        user_url: str,
        send_user_id: str,
        send_user_name: str,
        item_id: str,
        send_message: str,
        chat_id: str
    ) -> Optional[str]:
        """调用API获取回复消息

        Args:
            msg_time: 消息时间
            user_url: 用户URL
            send_user_id: 发送者用户ID
            send_user_name: 发送者用户名
            item_id: 商品ID
            send_message: 发送的消息内容
            chat_id: 聊天ID

        Returns:
            Optional[str]: API回复内容
        """
        try:
            if not self.parent.session:
                await self.parent.create_session()

            import aiohttp

            api_config = AUTO_REPLY.get('api', {})
            timeout = aiohttp.ClientTimeout(total=api_config.get('timeout', 10))

            payload = {
                "cookie_id": self.parent.cookie_id,
                "msg_time": msg_time,
                "user_url": user_url,
                "send_user_id": send_user_id,
                "send_user_name": send_user_name,
                "item_id": item_id,
                "send_message": send_message,
                "chat_id": chat_id
            }

            async with self.parent.session.post(
                api_config.get('url', 'http://localhost:8080/xianyu/reply'),
                json=payload,
                timeout=timeout
            ) as response:
                result = await response.json()

                if str(result.get('code')) == '200' or result.get('code') == 200:
                    send_msg = result.get('data', {}).get('send_msg')
                    if send_msg:
                        return send_msg.format(
                            send_user_id=payload['send_user_id'],
                            send_user_name=payload['send_user_name'],
                            send_message=payload['send_message']
                        )
                    else:
                        logger.warning("API返回成功但无回复消息")
                        return None
                else:
                    logger.warning(f"API返回错误: {result.get('msg', '未知错误')}")
                    return None

        except asyncio.TimeoutError:
            logger.error("API调用超时")
            return None
        except Exception as e:
            logger.error(f"调用API出错: {safe_str(e)}")
            return None
