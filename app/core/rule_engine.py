"""
规则引擎模块（向后兼容层）

此文件保留用于向后兼容，所有实现已迁移到 src/rule_engine/ 子模块。

新代码应该使用：
    from app.core.rule_engine import RuleEngine, Rule, Condition, LogicOperator

旧代码可以继续使用：
    from app.core.rule_engine import RuleEngine, Rule, Condition, LogicOperator
    # 或
    from app.core.rule_engine.rule_engine import RuleEngine, Rule, Condition, LogicOperator
"""

from app.core.rule_engine import (
    RuleEngine,
    Rule,
    Condition,
    LogicOperator,
    ConditionOperator,
    ConditionHandler,
    RuleEngineError,
    rule_engine,
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
]
