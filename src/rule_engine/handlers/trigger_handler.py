"""
触发次数条件处理器模块

处理与触发次数相关的条件判断。
"""

from typing import Any, Dict

from src.rule_engine.handlers.base import ConditionHandler
from src.rule_engine.exceptions import RuleEngineError


class TriggerConditionHandler(ConditionHandler):
    """触发次数条件处理器
    
    处理与触发次数相关的条件判断，支持触发次数限制。
    
    支持的字段：
    - count: 触发次数
    
    支持的操作符：
    - eq, ne, gt, lt, gte, lte: 基本比较
    
    注意：
    - 触发次数从上下文的 trigger_count 字段获取
    - 条件的 field 必须为 "count"
    
    Examples:
        >>> handler = TriggerConditionHandler()
        >>> from src.rule_engine import Condition
        >>> condition = Condition(type="trigger", field="count", operator="lte", value=5)
        >>> context = {"trigger_count": 3}
        >>> result = handler.evaluate(condition, context)
        >>> print(result)  # True (3 <= 5)
    """
    
    def evaluate(self, condition, context: Dict[str, Any]) -> bool:
        """评估触发次数条件
        
        Args:
            condition: 触发次数条件
            context: 上下文数据，包含 trigger_count 字段
            
        Returns:
            bool: 条件是否满足
            
        Raises:
            RuleEngineError: 字段不支持
        """
        trigger_count = context.get("trigger_count", 0)
        
        if condition.field != "count":
            raise RuleEngineError(f"触发次数条件不支持字段: {condition.field}")
        
        return self._compare(trigger_count, condition.operator, condition.value)
