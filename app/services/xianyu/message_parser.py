"""
闲鱼自动回复系统 - 消息解析模块
负责消息解析、提取商品ID等逻辑
"""

import re
import json
from typing import Optional, Dict, Any
from loguru import logger
from app.services.xianyu.common import safe_str


class MessageParser:
    """消息解析器 - 负责消息解析和信息提取"""

    def __init__(self, parent=None):
        """初始化消息解析器

        Args:
            parent: 父类实例，用于访问共享属性
        """
        self.parent = parent

    def is_chat_message(self, message: dict) -> bool:
        """判断是否为用户聊天消息

        Args:
            message: 消息字典

        Returns:
            bool: 是否为聊天消息
        """
        try:
            return (
                isinstance(message, dict)
                and "1" in message
                and isinstance(message["1"], dict)
                and "10" in message["1"]
                and isinstance(message["1"]["10"], dict)
                and "reminderContent" in message["1"]["10"]
            )
        except Exception:
            return False

    def is_sync_package(self, message_data: dict) -> bool:
        """判断是否为同步包消息

        Args:
            message_data: 消息数据字典

        Returns:
            bool: 是否为同步包消息
        """
        try:
            return (
                isinstance(message_data, dict)
                and "body" in message_data
                and "syncPushPackage" in message_data["body"]
                and "data" in message_data["body"]["syncPushPackage"]
                and len(message_data["body"]["syncPushPackage"]["data"]) > 0
            )
        except Exception:
            return False

    def extract_item_id_from_message(self, message: dict) -> Optional[str]:
        """从消息中提取商品ID

        Args:
            message: 消息字典

        Returns:
            Optional[str]: 商品ID，提取失败返回None
        """
        try:
            message_1 = message.get('1')
            if isinstance(message_1, str):
                id_match = re.search(r'(\d{10,})', message_1)
                if id_match:
                    logger.info(f"从message[1]字符串中提取商品ID: {id_match.group(1)}")
                    return id_match.group(1)

            message_3 = message.get('3', {})
            if isinstance(message_3, dict):
                if 'extension' in message_3:
                    extension = message_3['extension']
                    if isinstance(extension, dict):
                        item_id = extension.get('itemId') or extension.get('item_id')
                        if item_id:
                            logger.info(f"从extension中提取商品ID: {item_id}")
                            return item_id

                if 'bizData' in message_3:
                    biz_data = message_3['bizData']
                    if isinstance(biz_data, dict):
                        item_id = biz_data.get('itemId') or biz_data.get('item_id')
                        if item_id:
                            logger.info(f"从bizData中提取商品ID: {item_id}")
                            return item_id

                for key, value in message_3.items():
                    if isinstance(value, dict):
                        item_id = value.get('itemId') or value.get('item_id')
                        if item_id:
                            logger.info(f"从{key}字段中提取商品ID: {item_id}")
                            return item_id

                content = message_3.get('content', '')
                if isinstance(content, str) and content:
                    id_match = re.search(r'(\d{10,})', content)
                    if id_match:
                        cookie_id = self.parent.cookie_id if self.parent else "unknown"
                        logger.info(f"【{cookie_id}】从消息内容中提取商品ID: {id_match.group(1)}")
                        return id_match.group(1)

            def find_item_id_recursive(obj, path="", max_depth=10):
                if max_depth <= 0:
                    logger.warning(f"递归深度超限，停止搜索: {path}")
                    return None
                if isinstance(obj, dict):
                    for key in ['itemId', 'item_id', 'id']:
                        if key in obj and isinstance(obj[key], (str, int)):
                            value = str(obj[key])
                            if len(value) >= 10 and value.isdigit():
                                logger.info(f"从{path}.{key}中提取商品ID: {value}")
                                return value

                    for key, value in obj.items():
                        result = find_item_id_recursive(value, f"{path}.{key}" if path else key, max_depth - 1)
                        if result:
                            return result

                elif isinstance(obj, str):
                    id_match = re.search(r'(\d{10,})', obj)
                    if id_match:
                        logger.info(f"从{path}字符串中提取商品ID: {id_match.group(1)}")
                        return id_match.group(1)

                return None

            result = find_item_id_recursive(message)
            if result:
                return result

            logger.debug("所有方法都未能提取到商品ID")
            return None

        except Exception as e:
            logger.error(f"提取商品ID失败: {safe_str(e)}")
            return None

    def extract_user_id(self, message: dict) -> str:
        """从消息中提取用户ID

        Args:
            message: 消息字典

        Returns:
            str: 用户ID
        """
        try:
            message_1 = message.get("1")
            if isinstance(message_1, str) and '@' in message_1:
                return message_1.split('@')[0]
            elif isinstance(message_1, dict):
                return "unknown_user"
            else:
                return "unknown_user"
        except Exception as e:
            logger.debug(f"提取用户ID失败: {self._safe_str(e)}")
            return "unknown_user"

    def extract_chat_info(self, message: dict) -> Dict[str, Any]:
        """从消息中提取聊天信息

        Args:
            message: 消息字典

        Returns:
            Dict[str, Any]: 聊天信息字典
        """
        try:
            if not (isinstance(message, dict) and "1" in message and isinstance(message["1"], dict)):
                return {}

            message_1 = message["1"]
            if not isinstance(message_1.get("10"), dict):
                return {}

            message_10 = message_1["10"]
            create_time = int(message_1.get("5", 0))
            send_user_name = message_10.get("senderNick", message_10.get("reminderTitle", "未知用户"))
            send_user_id = message_10.get("senderUserId", "unknown")
            send_message = message_10.get("reminderContent", "")

            chat_id_raw = message_1.get("2", "")
            chat_id = chat_id_raw.split('@')[0] if '@' in str(chat_id_raw) else str(chat_id_raw)

            return {
                'create_time': create_time,
                'send_user_name': send_user_name,
                'send_user_id': send_user_id,
                'send_message': send_message,
                'chat_id': chat_id
            }

        except Exception as e:
            logger.error(f"提取聊天信息失败: {self._safe_str(e)}")
            return {}

    def is_system_message(self, send_message: str) -> bool:
        """判断是否为系统消息

        Args:
            send_message: 消息内容

        Returns:
            bool: 是否为系统消息
        """
        system_messages = [
            '[我已拍下，待付款]',
            '[你关闭了订单，钱款已原路退返]',
            '发来一条消息',
            '发来一条新消息',
            '[买家确认收货，交易成功]',
            '快给ta一个评价吧~',
            '快给ta一个评价吧～',
            '卖家人不错？送Ta闲鱼小红花',
            '[你已确认收货，交易成功]',
            '[你已发货]'
        ]
        return send_message in system_messages

    def debug_message_structure(self, message: dict, context: str = "") -> None:
        """调试消息结构的辅助方法

        Args:
            message: 消息字典
            context: 上下文描述
        """
        try:
            logger.debug(f"[{context}] 消息结构调试:")
            logger.debug(f"  消息类型: {type(message)}")

            if isinstance(message, dict):
                for key, value in message.items():
                    logger.debug(f"  键 '{key}': {type(value)} - {str(value)[:100]}...")

                    if key in ["1", "3"] and isinstance(value, dict):
                        logger.debug(f"    详细结构 '{key}':")
                        for sub_key, sub_value in value.items():
                            logger.debug(f"      '{sub_key}': {type(sub_value)} - {str(sub_value)[:50]}...")
            else:
                logger.debug(f"  消息内容: {str(message)[:200]}...")

        except Exception as e:
            logger.error(f"调试消息结构时发生错误: {safe_str(e)}")
