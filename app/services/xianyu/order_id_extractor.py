"""
闲鱼自动回复系统 - 订单ID提取模块
负责从消息中提取订单ID
"""

import json
import time
import re
from typing import Optional, Dict, Any
from loguru import logger

from app.services.xianyu.common import safe_str


class OrderIdExtractor:
    """订单ID提取器"""

    def __init__(self, parent):
        self.parent = parent

    def _safe_str(self, obj) -> str:
        """安全转换为字符串"""
        return safe_str(obj)

    def _extract_order_id(self, message: dict) -> Optional[str]:
        """从消息中提取订单ID

        Args:
            message: 消息字典

        Returns:
            Optional[str]: 订单ID
        """
        order_id = None
        extraction_methods = []

        try:
            if not message:
                logger.warning(f"【{self.parent.cookie_id}】⚠️ 消息为空，无法提取订单ID")
                self._record_extraction_failure("empty_message")
                return None

            if not isinstance(message, dict):
                logger.warning(f"【{self.parent.cookie_id}】⚠️ 消息类型错误: {type(message)}, 无法提取订单ID")
                self._record_extraction_failure("invalid_message_type")
                return None

            logger.debug(f"【{self.parent.cookie_id}】🔍 完整消息结构: {message}")

            message_1 = message.get('1', {})
            logger.debug(f"【{self.parent.cookie_id}】🔍 message['1'] keys: {list(message_1.keys()) if message_1 else 'None'}")

            message_1_6 = message_1.get('6', {}) if message_1 else {}
            logger.debug(f"【{self.parent.cookie_id}】🔍 message['1']['6'] keys: {list(message_1_6.keys()) if message_1_6 else 'None'}")

            content_json_str = None
            try:
                content_json_str = message.get('1', {}).get('6', {}).get('3', {}).get('5', '')
            except (AttributeError, TypeError) as e:
                logger.debug(f"【{self.parent.cookie_id}】获取content_json_str失败: {e}")

            if content_json_str and not order_id:
                try:
                    content_data = json.loads(content_json_str)

                    target_url = content_data.get('dxCard', {}).get('item', {}).get('main', {}).get('exContent', {}).get('button', {}).get('targetUrl', '')
                    if target_url:
                        order_match = re.search(r'orderId=(\d+)', target_url)
                        if order_match:
                            order_id = order_match.group(1)
                            extraction_methods.append("button_targetUrl_orderId")
                            logger.info(f'【{self.parent.cookie_id}】✅ 从button提取到订单ID: {order_id}')

                    if not order_id:
                        main_target_url = content_data.get('dxCard', {}).get('item', {}).get('main', {}).get('targetUrl', '')
                        if main_target_url:
                            order_match = re.search(r'order_detail\?id=(\d+)', main_target_url)
                            if order_match:
                                order_id = order_match.group(1)
                                extraction_methods.append("main_targetUrl_order_detail")
                                logger.info(f'【{self.parent.cookie_id}】✅ 从main targetUrl提取到订单ID: {order_id}')

                except json.JSONDecodeError as parse_e:
                    logger.debug(f"【{self.parent.cookie_id}】解析内容JSON失败: {parse_e}")
                    extraction_methods.append(f"json_parse_error: {str(parse_e)[:50]}")
                except Exception as parse_e:
                    logger.debug(f"【{self.parent.cookie_id}】方法1提取订单ID失败: {parse_e}")
                    extraction_methods.append(f"method1_error: {str(parse_e)[:50]}")

            if not order_id and content_json_str:
                try:
                    content_data = json.loads(content_json_str)
                    dynamic_target_url = content_data.get('dynamicOperation', {}).get('changeContent', {}).get('dxCard', {}).get('item', {}).get('main', {}).get('exContent', {}).get('button', {}).get('targetUrl', '')
                    if dynamic_target_url:
                        order_match = re.search(r'order_detail\?id=(\d+)', dynamic_target_url)
                        if order_match:
                            order_id = order_match.group(1)
                            extraction_methods.append("dynamicOperation_order_detail")
                            logger.info(f'【{self.parent.cookie_id}】✅ 从order_detail提取到订单ID: {order_id}')
                except json.JSONDecodeError as parse_e:
                    logger.debug(f"【{self.parent.cookie_id}】解析dynamicOperation JSON失败: {parse_e}")
                except Exception as parse_e:
                    logger.debug(f"【{self.parent.cookie_id}】方法2提取订单ID失败: {parse_e}")

            if not order_id:
                order_id = self._extract_order_id_from_text(message)
                if order_id:
                    extraction_methods.append("text_pattern_fallback")
                    logger.info(f'【{self.parent.cookie_id}】✅ 从消息文本中提取到订单ID: {order_id}')

            if not order_id:
                order_id = self._extract_order_id_from_message_fields(message)
                if order_id:
                    extraction_methods.append("message_fields_fallback")
                    logger.info(f'【{self.parent.cookie_id}】✅ 从消息字段中提取到订单ID: {order_id}')

            if order_id:
                logger.info(f"【{self.parent.cookie_id}】✅ 订单ID提取成功: {order_id}, 使用方法: {', '.join(extraction_methods)}")
                self._record_extraction_success()
            else:
                logger.warning(f"【{self.parent.cookie_id}】❌ 未能提取到订单ID，尝试的方法: {', '.join(extraction_methods) if extraction_methods else '无'}")
                self._record_extraction_failure(f"all_methods_failed: {extraction_methods}")

            return order_id

        except Exception as e:
            logger.error(f"【{self.parent.cookie_id}】提取订单ID时发生未预期错误: {self._safe_str(e)}")
            self._record_extraction_failure(f"unexpected_error: {self._safe_str(e)[:100]}")
            return None

    def _extract_order_id_from_text(self, message: dict) -> Optional[str]:
        """从消息文本中搜索订单ID模式

        Args:
            message: 消息字典

        Returns:
            Optional[str]: 订单ID
        """
        try:
            text_content = ""

            if '1' in message and isinstance(message['1'], dict):
                msg_data = message['1']

                if '3' in msg_data:
                    text_content += str(msg_data['3']) + " "

                if '5' in msg_data:
                    text_content += str(msg_data['5']) + " "

                if '6' in msg_data and isinstance(msg_data['6'], dict):
                    ext_content = msg_data['6']
                    if '3' in ext_content and isinstance(ext_content['3'], dict):
                        inner_content = ext_content['3']
                        for key in ['1', '2', '3', '4', '5']:
                            if key in inner_content:
                                text_content += str(inner_content[key]) + " "

            if 'text' in message:
                text_content += str(message['text']) + " "

            if 'content' in message:
                text_content += str(message['content']) + " "

            if 'body' in message:
                text_content += str(message['body']) + " "

            if not text_content:
                text_content = json.dumps(message, ensure_ascii=False)

            if not text_content:
                return None

            patterns = [
                (r'订单[号ID]*[：:]\s*(\d{15,20})', "order_prefix"),
                (r'order[\s_-]*id[：:]\s*(\d{15,20})', "order_id_english"),
                (r'orderId=(\d{15,20})', "url_orderId"),
                (r'order_detail\?id=(\d{15,20})', "url_order_detail"),
                (r'(?:订单|付款|发货).*?(\d{15,20})', "context_order"),
                (r'\b(\d{15,20})\b', "generic_number"),
            ]

            for pattern, pattern_name in patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                if matches:
                    for match in matches:
                        if match and len(match) >= 15:
                            logger.debug(f"【{self.parent.cookie_id}】从文本中提取到订单ID: {match}, 模式: {pattern_name}")
                            return match

            logger.debug(f"【{self.parent.cookie_id}】未从文本中找到订单ID，文本长度: {len(text_content)}")
            return None

        except Exception as e:
            logger.debug(f"【{self.parent.cookie_id}】从文本提取订单ID失败: {e}")
            return None

    def _extract_order_id_from_message_fields(self, message: dict) -> Optional[str]:
        """从消息的其他字段搜索订单ID

        Args:
            message: 消息字典

        Returns:
            Optional[str]: 订单ID
        """
        try:
            message_str = json.dumps(message, ensure_ascii=False)

            patterns = [
                r'"orderId"[\s]*:[\s]*"(\d{15,20})"',
                r'"orderId"[\s]*:[\s]*(\d{15,20})',
                r'"order_id"[\s]*:[\s]*"(\d{15,20})"',
                r'"order_id"[\s]*:[\s]*(\d{15,20})',
                r'"id"[\s]*:[\s]*"(\d{15,20})"',
                r'"tradeId"[\s]*:[\s]*"(\d{15,20})"',
                r'"tradeId"[\s]*:[\s]*(\d{15,20})',
            ]

            for pattern in patterns:
                match = re.search(pattern, message_str, re.IGNORECASE)
                if match:
                    order_id = match.group(1)
                    logger.debug(f"【{self.parent.cookie_id}】从消息字段中提取到订单ID: {order_id}")
                    return order_id

            return None

        except Exception as e:
            logger.debug(f"【{self.parent.cookie_id}】从消息字段提取订单ID失败: {e}")
            return None

    def _record_extraction_success(self) -> None:
        """记录订单ID提取成功"""
        try:
            if not hasattr(self, '_order_id_extraction_failures'):
                self._order_id_extraction_failures = 0
            self._order_id_extraction_failures = 0
        except Exception:
            pass

    def _record_extraction_failure(self, reason: str) -> None:
        """记录订单ID提取失败

        Args:
            reason: 失败原因
        """
        try:
            if not hasattr(self, '_order_id_extraction_failures'):
                self._order_id_extraction_failures = 0
            if not hasattr(self, '_last_extraction_failure_time'):
                self._last_extraction_failure_time = 0

            self._order_id_extraction_failures += 1
            self._last_extraction_failure_time = time.time()

            logger.warning(
                f"【{self.parent.cookie_id}】订单ID提取失败 (#{self._order_id_extraction_failures}): {reason}"
            )

            if self._order_id_extraction_failures >= 5:
                self._send_extraction_failure_alert()

        except Exception:
            pass

    def _send_extraction_failure_alert(self) -> None:
        """发送订单ID提取失败告警"""
        try:
            import asyncio
            logger.error(
                f"【{self.parent.cookie_id}】🚨 告警：连续 {self._order_id_extraction_failures} 次订单ID提取失败，"
                f"请检查闲鱼消息格式是否已更新"
            )

            if hasattr(self.parent, 'send_notification'):
                asyncio.create_task(
                    self.parent.send_notification(
                        title="订单ID提取失败告警",
                        message=f"账号 {self.parent.cookie_id} 连续 {self._order_id_extraction_failures} 次无法提取订单ID，"
                                f"可能是闲鱼消息格式已更新，请检查系统日志。"
                    )
                )

            self._order_id_extraction_failures = 0

        except Exception as e:
            logger.error(f"发送订单ID提取失败告警时出错: {e}")
