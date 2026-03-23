"""
Xianyu Auto Reply System - Message Decryption Module
Handles message decryption and system message filtering.
"""

import json
import base64
import time
from typing import Optional, Dict, Any, Tuple

from loguru import logger
from utils.xianyu.common import safe_str, SYSTEM_MESSAGE_PATTERNS


class MessageDecryptor:
    """Message decryption and preprocessing."""

    def __init__(self, parent=None):
        """Initialize decryptor.

        Args:
            parent: Parent instance for shared properties
        """
        self.parent = parent

    def decrypt_message(self, sync_data: dict) -> Tuple[Optional[dict], Optional[str]]:
        """Decrypt message data.

        Args:
            sync_data: Sync package data

        Returns:
            Tuple[Optional[dict], Optional[str]]: (decrypted message, error message)
        """
        try:
            if "data" not in sync_data:
                return None, "No data field in sync package"

            data = sync_data["data"]

            try:
                data = base64.b64decode(data).decode("utf-8")
                parsed_data = json.loads(data)

                if isinstance(parsed_data, dict) and 'chatType' in parsed_data:
                    return self._handle_system_message(parsed_data)

                return parsed_data, None

            except Exception:
                data = sync_data["data"]
                try:
                    from utils.xianyu_utils import decrypt as xianyu_decrypt
                    decrypted_data = xianyu_decrypt(data)
                    message = json.loads(decrypted_data)
                    return message, None
                except Exception as e:
                    return None, f"Message decrypt failed: {safe_str(e)}"

        except Exception as e:
            return None, f"Message process failed: {safe_str(e)}"

    def _handle_system_message(self, parsed_data: dict) -> Tuple[Optional[dict], Optional[str]]:
        """Handle system messages.

        Args:
            parsed_data: Parsed data

        Returns:
            Tuple[Optional[dict], Optional[str]]: (None if handled, log info)
        """
        msg_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        cookie_id = self.parent.cookie_id if self.parent else "unknown"

        if 'operation' in parsed_data and 'content' in parsed_data['operation']:
            content = parsed_data['operation']['content']

            if 'sessionArouse' in content:
                logger.info(f"[{msg_time}] [{cookie_id}] [System] Xianyu hints:")
                if 'arouseChatScriptInfo' in content['sessionArouse']:
                    for qa in content['sessionArouse']['arouseChatScriptInfo']:
                        logger.info(f"  - {qa['chatScrip']}")
            elif 'contentType' in content:
                logger.debug(f"[{msg_time}] [{cookie_id}] [System] Other message type: {content}")

        return None, None

    def is_system_message(self, send_message: str) -> bool:
        """Check if message is a system message.

        Args:
            send_message: Message content

        Returns:
            bool: True if system message
        """
        return send_message in SYSTEM_MESSAGE_PATTERNS

    def get_system_message_log(self, send_message: str, msg_time: str, cookie_id: str) -> Optional[str]:
        """Get system message log info.

        Args:
            send_message: Message content
            msg_time: Message time
            cookie_id: Cookie ID

        Returns:
            Optional[str]: Log info or None
        """
        if send_message == '[我已拍下，待付款]':
            return f'[{msg_time}] [{cookie_id}] System message - skipped'
        elif send_message == '[你关闭了订单，钱款已原路退返]':
            return f'[{msg_time}] [{cookie_id}] System message - skipped'
        elif send_message == '发来一条消息':
            return f'[{msg_time}] [{cookie_id}] System notification - skipped'
        elif send_message == '发来一条新消息':
            return f'[{msg_time}] [{cookie_id}] System notification - skipped'
        elif send_message == '[买家确认收货，交易成功]':
            return f'[{msg_time}] [{cookie_id}] Trade completed - skipped'
        elif send_message in ('快给ta一个评价吧~', '快给ta一个评价吧～'):
            return f'[{msg_time}] [{cookie_id}] Review reminder - skipped'
        elif send_message == '卖家人不错？送Ta闲鱼小红花':
            return f'[{msg_time}] [{cookie_id}] Flower reminder - skipped'
        elif send_message == '[你已确认收货，交易成功]':
            return f'[{msg_time}] [{cookie_id}] Buyer confirmed - skipped'
        elif send_message == '[你已发货]':
            return f'[{msg_time}] [{cookie_id}] Shipping confirmed - skipped'

        return None

    def extract_card_info(self, message: dict) -> Optional[Dict[str, Any]]:
        """Extract info from card message.

        Args:
            message: Message dict

        Returns:
            Optional[Dict[str, Any]]: Card info with title
        """
        try:
            if not (isinstance(message, dict) and "1" in message and isinstance(message["1"], dict)):
                return None

            message_1 = message["1"]
            if not ("6" in message_1 and isinstance(message_1["6"], dict)):
                return None

            message_6 = message_1["6"]
            if not ("3" in message_6 and isinstance(message_6["3"], dict)):
                return None

            message_6_3 = message_6["3"]
            if "5" not in message_6_3:
                return None

            try:
                card_content = json.loads(message_6_3["5"])
                if "dxCard" in card_content and "item" in card_content["dxCard"]:
                    card_item = card_content["dxCard"]["item"]
                    if "main" in card_item and "exContent" in card_item["main"]:
                        ex_content = card_item["main"]["exContent"]
                        return {
                            'title': ex_content.get("title", "")
                        }
            except (json.JSONDecodeError, KeyError) as e:
                logger.debug(f"Card info extraction failed: {safe_str(e)}")

            return None

        except Exception as e:
            logger.debug(f"Card info extraction error: {safe_str(e)}")
            return None

    def handle_order_status(self, message: dict, user_id: str) -> Optional[str]:
        """Handle order status message.

        Args:
            message: Message dict
            user_id: User ID

        Returns:
            Optional[str]: Order status or None
        """
        try:
            msg_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            cookie_id = self.parent.cookie_id if self.parent else "unknown"

            red_reminder = None
            if isinstance(message, dict) and "3" in message and isinstance(message["3"], dict):
                red_reminder = message["3"].get("redReminder")

            user_url = f'https://www.goofish.com/personal?userId={user_id}'

            if red_reminder == '等待买家付款':
                logger.info(f'[{msg_time}] [System] Buyer {user_url} waiting for payment')
                return 'waiting_payment'
            elif red_reminder == '交易关闭':
                logger.info(f'[{msg_time}] [System] Buyer {user_url} trade closed')
                return 'closed'
            elif red_reminder == '等待卖家发货':
                logger.info(f'[{msg_time}] [System] Trade success {user_url} waiting for shipping')
                return 'waiting_delivery'

            return None

        except Exception:
            return None

    def build_ack_message(self, message: dict, generate_mid_func) -> dict:
        """Build acknowledgment message.

        Args:
            message: Original message
            generate_mid_func: Function to generate mid

        Returns:
            dict: ACK message
        """
        ack = {
            "code": 200,
            "headers": {
                "mid": message["headers"]["mid"] if "mid" in message["headers"] else generate_mid_func(),
                "sid": message["headers"]["sid"] if "sid" in message["headers"] else '',
            }
        }

        if 'app-key' in message["headers"]:
            ack["headers"]["app-key"] = message["headers"]["app-key"]
        if 'ua' in message["headers"]:
            ack["headers"]["ua"] = message["headers"]["ua"]
        if 'dt' in message["headers"]:
            ack["headers"]["dt"] = message["headers"]["dt"]

        return ack
