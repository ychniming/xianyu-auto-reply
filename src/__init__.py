"""
闲鱼自动回复系统 - 核心模块
"""

__version__ = "1.0.0"

# 导出关键词匹配器
from src.keyword_matcher import keyword_matcher, KeywordMatcher

# 导出规则引擎
from src.rule_engine import (
    rule_engine,
    RuleEngine,
    Rule,
    Condition,
    LogicOperator,
    ConditionOperator,
    ConditionHandler,
    RuleEngineError,
    TimeConditionHandler,
    UserConditionHandler,
    ItemConditionHandler,
    KeywordConditionHandler,
)

__all__ = [
    'keyword_matcher', 
    'KeywordMatcher',
    'rule_engine',
    'RuleEngine',
    'Rule',
    'Condition',
    'LogicOperator',
    'ConditionOperator',
    'ConditionHandler',
    'RuleEngineError',
    'TimeConditionHandler',
    'UserConditionHandler',
    'ItemConditionHandler',
    'KeywordConditionHandler',
]
