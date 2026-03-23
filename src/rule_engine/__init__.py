"""
规则引擎模块

提供轻量级规则引擎框架，支持条件组合、嵌套条件和可扩展条件处理器。

主要组件：
- RuleEngine: 规则引擎核心类
- Rule: 规则定义
- Condition: 条件定义
- LogicOperator: 逻辑操作符
- ConditionOperator: 条件操作符
- ConditionHandler: 条件处理器基类
- RuleEngineError: 规则引擎异常

使用示例：
    >>> from src.rule_engine import RuleEngine, Rule, Condition, LogicOperator
    >>> 
    >>> engine = RuleEngine()
    >>> 
    >>> rule = Rule(
    ...     logic=LogicOperator.AND,
    ...     conditions=[
    ...         Condition(type="time", field="hour", operator="between", value=[9, 18])
    ...     ]
    ... )
    >>> 
    >>> context = {"hour": 14}
    >>> result = engine.evaluate(rule, context)
    >>> print(result)  # True
"""

from src.rule_engine.core import (
    RuleEngine,
    Rule,
    Condition,
    rule_engine,
)
from src.rule_engine.operators import (
    LogicOperator,
    ConditionOperator,
)
from src.rule_engine.exceptions import RuleEngineError
from src.rule_engine.handlers.base import ConditionHandler
from src.rule_engine.handlers import (
    TimeConditionHandler,
    UserConditionHandler,
    ItemConditionHandler,
    KeywordConditionHandler,
    TriggerConditionHandler,
)

__all__ = [
    'RuleEngine',
    'Rule',
    'Condition',
    'LogicOperator',
    'ConditionOperator',
    'ConditionHandler',
    'RuleEngineError',
    'rule_engine',
    'TimeConditionHandler',
    'UserConditionHandler',
    'ItemConditionHandler',
    'KeywordConditionHandler',
    'TriggerConditionHandler',
]
