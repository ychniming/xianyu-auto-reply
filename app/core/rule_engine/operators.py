"""
操作符枚举模块

定义规则引擎使用的逻辑操作符和条件操作符。
"""

from enum import Enum


class LogicOperator(Enum):
    """逻辑操作符枚举
    
    用于组合多个条件或规则的逻辑关系。
    
    Attributes:
        AND: 逻辑与，所有条件都为真时返回真
        OR: 逻辑或，任一条件为真时返回真
        NOT: 逻辑非，条件为假时返回真
    
    Examples:
        >>> LogicOperator.AND.value
        'and'
        >>> LogicOperator.OR.value
        'or'
        >>> LogicOperator.NOT.value
        'not'
    """
    AND = "and"
    OR = "or"
    NOT = "not"


class ConditionOperator(Enum):
    """条件操作符枚举
    
    定义条件判断支持的操作符类型。
    
    Attributes:
        EQ: 等于 (==)
        NE: 不等于 (!=)
        GT: 大于 (>)
        LT: 小于 (<)
        GTE: 大于等于 (>=)
        LTE: 小于等于 (<=)
        CONTAINS: 包含 (in)
        NOT_CONTAINS: 不包含 (not in)
        IN: 在列表中 (value in list)
        NOT_IN: 不在列表中 (value not in list)
        BETWEEN: 在范围内 (min <= value <= max)
        STARTS_WITH: 以...开头
        ENDS_WITH: 以...结尾
        MATCHES: 正则匹配
        IS_EMPTY: 为空
        IS_NOT_EMPTY: 不为空
    
    Examples:
        >>> ConditionOperator.EQ.value
        'eq'
        >>> ConditionOperator.BETWEEN.value
        'between'
    """
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    LT = "lt"
    GTE = "gte"
    LTE = "lte"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    BETWEEN = "between"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    MATCHES = "matches"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"
