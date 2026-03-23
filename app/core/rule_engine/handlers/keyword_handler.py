"""
关键词条件处理器模块

处理与关键词相关的条件判断。
"""

import re
from typing import Any, Dict

from app.core.rule_engine.handlers.base import ConditionHandler
from app.core.rule_engine.operators import ConditionOperator
from app.core.rule_engine.exceptions import RuleEngineError


class KeywordConditionHandler(ConditionHandler):
    """关键词条件处理器
    
    处理与关键词相关的条件判断，支持关键词匹配、消息内容检查等。
    
    支持的字段：
    - message: 消息内容
    - keyword: 关键词
    - match_type: 匹配类型（exact/contains/prefix/suffix/regex）
    - exclude: 排除关键词列表
    
    支持的操作符：
    - eq, ne: 精确比较
    - contains, not_contains: 包含检查
    - starts_with, ends_with: 前缀/后缀匹配
    - matches: 正则匹配
    - in, not_in: 列表包含
    - is_empty, is_not_empty: 空值检查
    
    Examples:
        >>> handler = KeywordConditionHandler()
        >>> from app.core.rule_engine import Condition
        >>> condition = Condition(type="keyword", field="message", operator="contains", value="价格")
        >>> context = {"message": "请问价格是多少？"}
        >>> result = handler.evaluate(condition, context)
        >>> print(result)  # True
    """
    
    def evaluate(self, condition, context: Dict[str, Any]) -> bool:
        """评估关键词条件
        
        Args:
            condition: 关键词条件
            context: 上下文数据，包含消息或关键词字段
            
        Returns:
            bool: 条件是否满足
            
        Raises:
            RuleEngineError: 字段不存在
        """
        field_value = context.get(condition.field)
        
        if condition.field == "exclude" and condition.operator == ConditionOperator.CONTAINS.value:
            message = context.get("message", "")
            if not message:
                return True
            
            exclude_keywords = condition.value
            if isinstance(exclude_keywords, list):
                for exclude_kw in exclude_keywords:
                    if exclude_kw in message:
                        return False
                return True
            return True
        
        if field_value is None:
            raise RuleEngineError(f"关键词字段不存在: {condition.field}")
        
        return self._compare(field_value, condition.operator, condition.value)
    
    def _compare(self, field_value: Any, operator: str, value: Any) -> bool:
        """执行比较操作
        
        扩展基础比较操作，支持正则匹配和字符串操作符。
        
        Args:
            field_value: 字段值
            operator: 操作符
            value: 比较值
            
        Returns:
            bool: 比较结果
        """
        field_str = str(field_value)
        value_str = str(value)
        
        if operator == ConditionOperator.EQ.value:
            return field_str == value_str
        elif operator == ConditionOperator.NE.value:
            return field_str != value_str
        elif operator == ConditionOperator.CONTAINS.value:
            return value_str in field_str
        elif operator == ConditionOperator.NOT_CONTAINS.value:
            return value_str not in field_str
        elif operator == ConditionOperator.STARTS_WITH.value:
            return field_str.startswith(value_str)
        elif operator == ConditionOperator.ENDS_WITH.value:
            return field_str.endswith(value_str)
        elif operator == ConditionOperator.MATCHES.value:
            return bool(re.search(value_str, field_str))
        elif operator == ConditionOperator.IN.value:
            return field_str in value
        elif operator == ConditionOperator.NOT_IN.value:
            return field_str not in value
        elif operator == ConditionOperator.IS_EMPTY.value:
            return not field_str.strip()
        elif operator == ConditionOperator.IS_NOT_EMPTY.value:
            return bool(field_str.strip())
        
        return super()._compare(field_value, operator, value)
