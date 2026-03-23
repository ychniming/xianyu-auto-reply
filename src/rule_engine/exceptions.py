"""
规则引擎异常模块

定义规则引擎相关的异常类。
"""

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.rule_engine.core import Rule, Condition


class RuleEngineError(Exception):
    """规则引擎异常
    
    当规则评估过程中发生错误时抛出。
    
    Attributes:
        message: 错误消息
        rule: 相关的规则（可选）
        condition: 相关的条件（可选）
    
    Examples:
        >>> error = RuleEngineError("测试错误")
        >>> str(error)
        '测试错误'
        
        >>> from src.rule_engine import Rule, Condition, LogicOperator
        >>> rule = Rule(logic=LogicOperator.AND, conditions=[])
        >>> error = RuleEngineError("规则错误", rule=rule)
        >>> str(error)
        '规则错误 | 规则: and'
    """
    
    def __init__(
        self,
        message: str,
        rule: Optional['Rule'] = None,
        condition: Optional['Condition'] = None
    ):
        """初始化异常
        
        Args:
            message: 错误消息
            rule: 相关的规则
            condition: 相关的条件
        """
        super().__init__(message)
        self.message = message
        self.rule = rule
        self.condition = condition
    
    def __str__(self) -> str:
        """返回异常字符串表示"""
        parts = [self.message]
        if self.rule:
            parts.append(f"规则: {self.rule.logic.value}")
        if self.condition:
            parts.append(f"条件: {self.condition.type}.{self.condition.field}")
        return " | ".join(parts)
