"""
闲鱼自动回复系统 - 核心模块
"""

__version__ = "1.0.0"

# 导出核心模块
from app.core.cookie_manager import CookieManager
from app.core.xianyu_live import XianyuLive
from app.core.ai_reply_engine import AIReplyEngine, ai_reply_engine

# 导出关键词匹配器
from app.core.keyword_matcher import keyword_matcher, KeywordMatcher

# 导出规则引擎
from app.core.rule_engine import (
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

# 导出异常类
from app.core.exceptions import (
    ErrorCode,
    XianyuBaseException,
    AuthenticationError,
    PermissionDeniedError,
    ResourceNotFoundError,
    ValidationError,
    ConflictError,
    RateLimitError,
    DatabaseError,
    ExternalServiceError,
)

__all__ = [
    'CookieManager',
    'XianyuLive',
    'AIReplyEngine',
    'ai_reply_engine',
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
    # 异常类
    'ErrorCode',
    'XianyuBaseException',
    'AuthenticationError',
    'PermissionDeniedError',
    'ResourceNotFoundError',
    'ValidationError',
    'ConflictError',
    'RateLimitError',
    'DatabaseError',
    'ExternalServiceError',
]
