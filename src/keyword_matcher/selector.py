"""
选择器模块

负责从匹配结果中选择最佳匹配，支持多种选择策略和回复模式。
"""

import json
import random
from typing import Dict, List, Optional, Any, Tuple

from loguru import logger

from src.keyword_matcher.constants import MATCH_TYPE_CONTAINS, MAX_JSON_STRING_LENGTH
from src.keyword_matcher.variables import VariablesHandler

# 导入规则引擎
from src.rule_engine import rule_engine, Rule, RuleEngineError


class Selector:
    """匹配结果选择器

    负责从多个匹配结果中选择最佳匹配，支持优先级、商品ID和条件评估。
    """

    def __init__(
        self,
        sequence_index_updater: Optional[Any] = None,
        trigger_count_updater: Optional[Any] = None,
        variables_handler: Optional[VariablesHandler] = None
    ):
        """初始化选择器

        Args:
            sequence_index_updater: 顺序回复索引更新回调
            trigger_count_updater: 触发次数更新回调
            variables_handler: 变量处理器
        """
        self._sequence_index_updater = sequence_index_updater
        self._trigger_count_updater = trigger_count_updater
        self._variables_handler = variables_handler or VariablesHandler()

    def set_sequence_index_updater(self, updater: Any) -> None:
        """设置顺序回复索引更新回调"""
        self._sequence_index_updater = updater

    def set_trigger_count_updater(self, updater: Any) -> None:
        """设置触发次数更新回调"""
        self._trigger_count_updater = updater

    def select_best(
        self,
        matches: List[Tuple[int, int, Dict[str, Any]]],
        item_id: Optional[str] = None,
        cookie_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """从匹配结果中选择最佳匹配

        选择策略：
        1. 按优先级（priority）降序排序
        2. 商品ID关键词优先于通用关键词
        3. 同优先级时按匹配位置排序（位置靠前的优先）
        4. 同优先级同位置时选择最长的关键词
        5. 如果关键词有 conditions，使用规则引擎评估条件

        Args:
            matches: 匹配结果列表 [(start, end, kw_data), ...]
            item_id: 商品ID
            cookie_id: 账号ID
            context: 规则引擎上下文

        Returns:
            Optional[Dict]: 最佳匹配结果
        """
        if not matches:
            return None

        item_matches = []
        general_matches = []

        for start, end, kw_data in matches:
            kw_item_id = kw_data.get('item_id')

            if item_id and kw_item_id == item_id:
                item_matches.append((start, end, kw_data))
            elif not kw_item_id:
                general_matches.append((start, end, kw_data))

        selected_matches = item_matches if item_matches else general_matches

        if not selected_matches:
            return None

        def sort_key(match: Tuple[int, int, Dict[str, Any]]) -> Tuple[int, int, int]:
            start, end, kw_data = match
            priority = kw_data.get('priority', 0) or 0
            keyword_len = end - start + 1
            return (priority, -start, keyword_len)

        selected_matches.sort(key=sort_key, reverse=True)

        for best_match in selected_matches:
            start, end, kw_data = best_match

            conditions_str = kw_data.get('conditions')
            if conditions_str:
                if not context:
                    logger.debug(
                        f"关键词 '{kw_data.get('keyword')}' 有条件但未提供上下文，跳过"
                    )
                    continue

                try:
                    if isinstance(conditions_str, str):
                        if len(conditions_str) > MAX_JSON_STRING_LENGTH:
                            logger.warning(
                                f"关键词 '{kw_data.get('keyword')}' 条件JSON过长"
                                f"（{len(conditions_str)}字符），跳过"
                            )
                            continue
                        conditions_data = json.loads(conditions_str)
                    else:
                        conditions_data = conditions_str

                    rule = Rule.from_dict(conditions_data)
                    rule_context = self._build_rule_context(context, kw_data)

                    if not rule_engine.evaluate(rule, rule_context):
                        logger.debug(
                            f"关键词 '{kw_data.get('keyword')}' 条件不满足，跳过"
                        )
                        continue

                    logger.info(f"关键词 '{kw_data.get('keyword')}' 条件评估通过")

                except json.JSONDecodeError as e:
                    logger.warning(
                        f"关键词 '{kw_data.get('keyword')}' 条件JSON解析失败: {e}，跳过"
                    )
                    continue
                except (KeyError, ValueError) as e:
                    logger.warning(
                        f"关键词 '{kw_data.get('keyword')}' 条件格式错误: {e}，跳过"
                    )
                    continue
                except RuleEngineError as e:
                    logger.warning(
                        f"关键词 '{kw_data.get('keyword')}' 条件评估失败: {e}，跳过"
                    )
                    continue
                except Exception as e:
                    logger.error(
                        f"关键词 '{kw_data.get('keyword')}' 条件处理异常: {e}，跳过"
                    )
                    continue

            reply = self._get_reply_by_mode(kw_data, cookie_id)

            return {
                'keyword': kw_data.get('keyword', ''),
                'reply': reply,
                'item_id': kw_data.get('item_id'),
                'type': kw_data.get('type', 'text'),
                'image_url': kw_data.get('image_url'),
                'position': (start, end),
                'match_type': kw_data.get('match_type', MATCH_TYPE_CONTAINS),
                'priority': kw_data.get('priority', 0),
                'reply_mode': kw_data.get('reply_mode', 'single'),
            }

        return None

    def _build_rule_context(
        self,
        context: Dict[str, Any],
        kw_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """构建规则引擎上下文

        将传入的上下文转换为规则引擎可用的扁平化结构。

        Args:
            context: 原始上下文
            kw_data: 关键词数据

        Returns:
            Dict[str, Any]: 扁平化的规则引擎上下文
        """
        rule_context = {}

        time_ctx = context.get('time', {})
        if time_ctx:
            rule_context['hour'] = time_ctx.get('hour')
            rule_context['minute'] = time_ctx.get('minute')
            rule_context['weekday'] = time_ctx.get('weekday')
            rule_context['timestamp'] = time_ctx.get('timestamp')

        user_ctx = context.get('user', {})
        if user_ctx:
            rule_context['user_id'] = user_ctx.get('id')
            rule_context['user_is_new'] = user_ctx.get('is_new', False)
            rule_context['user_purchase_count'] = user_ctx.get('purchase_count', 0)
            rule_context['user_message_count'] = user_ctx.get('message_count', 0)

        item_ctx = context.get('item', {})
        if item_ctx:
            rule_context['item_id'] = item_ctx.get('id')
            rule_context['item_price'] = item_ctx.get('price')
            rule_context['item_category'] = item_ctx.get('category')

        keyword_ctx = context.get('keyword', {})
        if keyword_ctx:
            rule_context['trigger_count'] = keyword_ctx.get('trigger_count', 0)
            rule_context['message'] = keyword_ctx.get('message')

        return rule_context

    def _get_reply_by_mode(
        self,
        kw_data: Dict[str, Any],
        cookie_id: Optional[str] = None
    ) -> str:
        """根据回复模式获取回复内容

        支持三种回复模式：
        - single: 返回单条回复（默认）
        - random: 从 replies 列表中随机选择一条回复
        - sequence: 按顺序循环使用 replies 列表

        Args:
            kw_data: 关键词数据
            cookie_id: 账号ID

        Returns:
            str: 回复内容
        """
        reply_mode = kw_data.get('reply_mode', 'single')
        default_reply = kw_data.get('reply', '')

        if reply_mode == 'single':
            return default_reply

        replies_str = kw_data.get('replies', '')
        if not replies_str:
            return default_reply

        try:
            replies = json.loads(replies_str) if isinstance(replies_str, str) else replies_str
            if not isinstance(replies, list) or len(replies) == 0:
                return default_reply
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"解析 replies 失败: {replies_str}")
            return default_reply

        if reply_mode == 'random':
            return random.choice(replies)

        elif reply_mode == 'sequence':
            current_index = kw_data.get('sequence_index', 0) or 0
            current_index = current_index % len(replies)
            reply = replies[current_index]

            next_index = (current_index + 1) % len(replies)

            if cookie_id and self._sequence_index_updater:
                try:
                    self._sequence_index_updater(
                        cookie_id,
                        kw_data.get('keyword', ''),
                        kw_data.get('item_id'),
                        next_index
                    )
                except Exception as e:
                    logger.error(f"更新顺序回复索引失败: {e}")

            return reply

        return default_reply
