"""
条件处理器基类模块

提供条件处理器的抽象基类和通用比较逻辑混入类。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from app.core.rule_engine.operators import ConditionOperator
from app.core.rule_engine.exceptions import RuleEngineError


class BaseCompareMixin:
    """比较操作混入类
    
    提供通用的比较逻辑，减少Handler子类的重复代码。
    
    所有Handler子类可以继承此混入类来获得基础比较功能，
    并通过覆盖_compare方法来扩展特定类型的比较逻辑。
    
    Examples:
        >>> class MyHandler(ConditionHandler, BaseCompareMixin):
        ...     def evaluate(self, condition, context):
        ...         value = context.get(condition.field)
        ...         return self._compare(value, condition.operator, condition.value)
    """
    
    def _compare_basic(self, field_value: Any, operator: str, value: Any) -> Any:
        """执行基础比较操作
        
        处理所有Handler通用的比较操作符。
        
        Args:
            field_value: 字段值
            operator: 操作符
            value: 比较值
            
        Returns:
            Any: 比较结果（bool或NotImplemented）
            
        Raises:
            RuleEngineError: 类型比较错误
        """
        try:
            if operator == ConditionOperator.EQ.value:
                return field_value == value
            elif operator == ConditionOperator.NE.value:
                return field_value != value
            elif operator == ConditionOperator.GT.value:
                return field_value > value
            elif operator == ConditionOperator.LT.value:
                return field_value < value
            elif operator == ConditionOperator.GTE.value:
                return field_value >= value
            elif operator == ConditionOperator.LTE.value:
                return field_value <= value
            elif operator == ConditionOperator.IN.value:
                return field_value in value
            elif operator == ConditionOperator.NOT_IN.value:
                return field_value not in value
            else:
                return NotImplemented
        except TypeError as e:
            raise RuleEngineError(f"类型比较错误: {e}")
    
    def _compare(self, field_value: Any, operator: str, value: Any) -> bool:
        """执行比较操作
        
        子类可以覆盖此方法来扩展特定类型的比较逻辑。
        默认实现调用_compare_basic处理基础操作符，
        如果操作符不支持则抛出异常。
        
        Args:
            field_value: 字段值
            operator: 操作符
            value: 比较值
            
        Returns:
            bool: 比较结果
            
        Raises:
            RuleEngineError: 操作符不支持
        """
        result = self._compare_basic(field_value, operator, value)
        if result is NotImplemented:
            raise RuleEngineError(f"不支持的操作符: {operator}")
        return result


class ConditionHandler(ABC, BaseCompareMixin):
    """条件处理器抽象基类
    
    所有自定义条件处理器必须继承此类并实现 evaluate 方法。
    继承此类的处理器自动获得BaseCompareMixin的比较能力。
    
    Examples:
        >>> class CustomHandler(ConditionHandler):
        ...     def evaluate(self, condition: Condition, context: Dict[str, Any]) -> bool:
        ...         field_value = context.get(condition.field)
        ...         return self._compare(field_value, condition.operator, condition.value)
    """
    
    @abstractmethod
    def evaluate(self, condition, context: Dict[str, Any]) -> bool:
        """评估条件
        
        Args:
            condition: 条件对象
            context: 上下文数据
            
        Returns:
            bool: 条件是否满足
            
        Raises:
            RuleEngineError: 评估过程中发生错误
        """
        pass
