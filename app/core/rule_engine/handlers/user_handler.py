"""
用户条件处理器模块

处理与用户相关的条件判断。
"""

from typing import Any, Dict

from app.core.rule_engine.handlers.base import ConditionHandler
from app.core.rule_engine.operators import ConditionOperator
from app.core.rule_engine.exceptions import RuleEngineError


class UserConditionHandler(ConditionHandler):
    """用户条件处理器
    
    处理与用户相关的条件判断，支持用户ID、等级、VIP状态等字段。
    
    支持的字段：
    - user_id: 用户ID
    - username: 用户名
    - level: 用户等级
    - is_vip: 是否VIP
    - is_banned: 是否被封禁
    - register_days: 注册天数
    
    支持的操作符：
    - eq, ne, gt, lt, gte, lte: 基本比较
    - in, not_in: 列表包含
    - contains, not_contains: 字符串包含
    - is_empty, is_not_empty: 空值检查
    
    Examples:
        >>> handler = UserConditionHandler()
        >>> from app.core.rule_engine import Condition
        >>> condition = Condition(type="user", field="level", operator="gte", value=5)
        >>> context = {"level": 7}
        >>> result = handler.evaluate(condition, context)
        >>> print(result)  # True
    """
    
    def evaluate(self, condition, context: Dict[str, Any]) -> bool:
        """评估用户条件
        
        Args:
            condition: 用户条件
            context: 上下文数据，包含用户字段
            
        Returns:
            bool: 条件是否满足
            
        Raises:
            RuleEngineError: 字段不存在（非空值检查时）
        """
        field_value = context.get(condition.field)
        
        if condition.operator in (ConditionOperator.IS_EMPTY.value, ConditionOperator.IS_NOT_EMPTY.value):
            return self._compare(field_value, condition.operator, condition.value)
        
        if field_value is None:
            raise RuleEngineError(f"用户字段不存在: {condition.field}")
        
        return self._compare(field_value, condition.operator, condition.value)
    
    def _compare(self, field_value: Any, operator: str, value: Any) -> bool:
        """执行比较操作
        
        扩展基础比较操作，支持contains和空值检查操作符。
        
        Args:
            field_value: 字段值
            operator: 操作符
            value: 比较值
            
        Returns:
            bool: 比较结果
        """
        if operator == ConditionOperator.CONTAINS.value:
            return value in field_value
        elif operator == ConditionOperator.NOT_CONTAINS.value:
            return value not in field_value
        elif operator == ConditionOperator.IS_EMPTY.value:
            return not field_value
        elif operator == ConditionOperator.IS_NOT_EMPTY.value:
            return bool(field_value)
        
        return super()._compare(field_value, operator, value)
