"""
时间条件处理器模块

处理与时间相关的条件判断。
"""

from datetime import datetime
from typing import Any, Dict

from app.core.rule_engine.handlers.base import ConditionHandler
from app.core.rule_engine.operators import ConditionOperator
from app.core.rule_engine.exceptions import RuleEngineError


class TimeConditionHandler(ConditionHandler):
    """时间条件处理器
    
    处理与时间相关的条件判断，支持小时、分钟、星期等时间字段。
    
    支持的字段：
    - hour: 小时（0-23）
    - minute: 分钟（0-59）
    - weekday: 星期（0=周一, 6=周日）
    - timestamp: Unix 时间戳
    
    支持的操作符：
    - eq, ne, gt, lt, gte, lte: 基本比较
    - between: 范围比较
    - in, not_in: 列表包含
    
    Examples:
        >>> handler = TimeConditionHandler()
        >>> from app.core.rule_engine import Condition
        >>> condition = Condition(type="time", field="hour", operator="between", value=[9, 18])
        >>> context = {"hour": 14}
        >>> result = handler.evaluate(condition, context)
        >>> print(result)  # True
    """
    
    def evaluate(self, condition, context: Dict[str, Any]) -> bool:
        """评估时间条件
        
        如果上下文中没有提供时间字段，会自动从当前时间获取。
        
        Args:
            condition: 时间条件
            context: 上下文数据，包含时间字段
            
        Returns:
            bool: 条件是否满足
            
        Raises:
            RuleEngineError: 字段不存在或值无效
        """
        field_value = context.get(condition.field)
        
        if field_value is None:
            now = datetime.now()
            if condition.field == "hour":
                field_value = now.hour
            elif condition.field == "minute":
                field_value = now.minute
            elif condition.field == "weekday":
                field_value = now.weekday()
            elif condition.field == "timestamp":
                field_value = now.timestamp()
            else:
                raise RuleEngineError(f"时间字段不存在: {condition.field}")
        
        return self._compare(field_value, condition.operator, condition.value)
    
    def _compare(self, field_value: Any, operator: str, value: Any) -> bool:
        """执行比较操作
        
        扩展基础比较操作，支持between操作符。
        
        Args:
            field_value: 字段值
            operator: 操作符
            value: 比较值
            
        Returns:
            bool: 比较结果
        """
        if operator == ConditionOperator.BETWEEN.value:
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                raise RuleEngineError("between 操作符需要包含两个值的列表")
            return value[0] <= field_value <= value[1]
        
        return super()._compare(field_value, operator, value)
