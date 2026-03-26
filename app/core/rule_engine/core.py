"""
规则引擎核心模块

提供规则引擎的核心类：Condition、Rule 和 RuleEngine。
"""

import json
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from loguru import logger

from app.core.rule_engine.operators import LogicOperator
from app.core.rule_engine.exceptions import RuleEngineError
from app.core.rule_engine.handlers import (
    TimeConditionHandler,
    UserConditionHandler,
    ItemConditionHandler,
    KeywordConditionHandler,
    TriggerConditionHandler,
)
from app.core.rule_engine.handlers.base import ConditionHandler


@dataclass
class Condition:
    """单个条件
    
    表示一个具体的条件判断，如 "时间在9点到18点之间"。
    
    Attributes:
        type: 条件类型，如 "time"、"user"、"item"、"keyword"
        field: 字段名，如 "hour"、"user_id"、"item_price"
        operator: 操作符，如 "eq"、"gt"、"between"
        value: 比较值，可以是单个值或列表（如 between 操作符需要两个值）
    
    Examples:
        >>> condition1 = Condition(
        ...     type="time",
        ...     field="hour",
        ...     operator="between",
        ...     value=[9, 18]
        ... )
        >>> condition2 = Condition(
        ...     type="user",
        ...     field="user_id",
        ...     operator="eq",
        ...     value="12345"
        ... )
    """
    type: str
    field: str
    operator: str
    value: Any
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 条件的字典表示
        """
        return {
            "type": self.type,
            "field": self.field,
            "operator": self.operator,
            "value": self.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Condition':
        """从字典创建条件
        
        Args:
            data: 条件字典数据
            
        Returns:
            Condition: 条件实例
            
        Raises:
            KeyError: 缺少必需字段
            ValueError: 字段值无效
        """
        required_fields = ['type', 'field', 'operator', 'value']
        for field_name in required_fields:
            if field_name not in data:
                raise KeyError(f"缺少必需字段: {field_name}")
        
        if not isinstance(data['type'], str) or not data['type'].strip():
            raise ValueError("type 必须是非空字符串")
        if not isinstance(data['field'], str) or not data['field'].strip():
            raise ValueError("field 必须是非空字符串")
        if not isinstance(data['operator'], str) or not data['operator'].strip():
            raise ValueError("operator 必须是非空字符串")
        
        return cls(
            type=data['type'].strip(),
            field=data['field'].strip(),
            operator=data['operator'].strip(),
            value=data['value']
        )


@dataclass
class Rule:
    """规则：包含条件组合
    
    表示一个规则，可以包含多个条件或嵌套的子规则。
    
    Attributes:
        logic: 逻辑操作符（AND/OR/NOT）
        conditions: 条件列表（AND/OR 时使用）
        sub_rules: 子规则列表（嵌套时使用）
        condition: 单个条件（NOT 时使用）
    
    Examples:
        >>> rule1 = Rule(
        ...     logic=LogicOperator.AND,
        ...     conditions=[
        ...         Condition(type="time", field="hour", operator="between", value=[9, 18]),
        ...         Condition(type="user", field="is_vip", operator="eq", value=True)
        ...     ]
        ... )
        >>> rule2 = Rule(
        ...     logic=LogicOperator.NOT,
        ...     condition=Condition(type="user", field="is_banned", operator="eq", value=True)
        ... )
    """
    logic: LogicOperator
    conditions: List[Condition] = field(default_factory=list)
    sub_rules: List['Rule'] = field(default_factory=list)
    condition: Optional[Condition] = None
    
    def __post_init__(self):
        """初始化后验证"""
        self._validate()
    
    def _validate(self):
        """验证规则结构
        
        Raises:
            ValueError: 规则结构无效
        """
        if self.logic == LogicOperator.NOT:
            if self.condition is None:
                raise ValueError("NOT 逻辑必须指定 condition")
            if self.conditions:
                raise ValueError("NOT 逻辑不能有 conditions 列表")
            if self.sub_rules:
                raise ValueError("NOT 逻辑不能有 sub_rules 列表")
        else:
            if not self.conditions and not self.sub_rules:
                raise ValueError(f"{self.logic.value} 逻辑必须有 conditions 或 sub_rules")
            if self.condition is not None:
                raise ValueError(f"{self.logic.value} 逻辑不能有单个 condition")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 规则的字典表示
        """
        data = {
            "logic": self.logic.value
        }
        
        if self.logic == LogicOperator.NOT:
            data["condition"] = self.condition.to_dict() if self.condition else None
        else:
            if self.conditions:
                data["conditions"] = [c.to_dict() for c in self.conditions]
            if self.sub_rules:
                data["sub_rules"] = [r.to_dict() for r in self.sub_rules]
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Rule':
        """从字典创建规则
        
        Args:
            data: 规则字典数据
            
        Returns:
            Rule: 规则实例
            
        Raises:
            KeyError: 缺少必需字段
            ValueError: 字段值无效
        """
        if 'logic' not in data:
            raise KeyError("缺少必需字段: logic")
        
        try:
            logic = LogicOperator(data['logic'])
        except ValueError:
            raise ValueError(f"无效的逻辑操作符: {data['logic']}")
        
        if logic == LogicOperator.NOT:
            if 'condition' not in data:
                raise KeyError("NOT 逻辑缺少 condition 字段")
            
            condition = Condition.from_dict(data['condition'])
            return cls(logic=logic, condition=condition)
        else:
            conditions = []
            if 'conditions' in data:
                conditions = [Condition.from_dict(c) for c in data['conditions']]
            
            sub_rules = []
            if 'sub_rules' in data:
                sub_rules = [Rule.from_dict(r) for r in data['sub_rules']]
            
            return cls(logic=logic, conditions=conditions, sub_rules=sub_rules)


class RuleEngine:
    """规则引擎
    
    核心规则评估引擎，支持条件组合、嵌套条件和可扩展条件处理器。
    
    特性：
    - 支持 AND、OR、NOT 逻辑组合
    - 支持嵌套条件结构
    - 可扩展的条件处理器
    - JSON 序列化/反序列化
    - 高性能评估
    - 完善的错误处理
    
    Examples:
        >>> engine = RuleEngine()
        >>> rule = Rule(
        ...     logic=LogicOperator.AND,
        ...     conditions=[
        ...         Condition(type="time", field="hour", operator="between", value=[9, 18]),
        ...         Condition(type="user", field="is_vip", operator="eq", value=True)
        ...     ]
        ... )
        >>> context = {"hour": 14, "is_vip": True}
        >>> result = engine.evaluate(rule, context)
        >>> print(result)  # True
    """
    
    def __init__(self, cache_size: int = 1000):
        """初始化规则引擎
        
        Args:
            cache_size: 规则评估缓存大小，0表示禁用缓存
        """
        self._condition_handlers: Dict[str, ConditionHandler] = {}
        self._cache_size = cache_size
        self._rule_cache: Dict[str, bool] = {}
        self._register_builtin_handlers()
        logger.info("规则引擎初始化完成")
    
    def _register_builtin_handlers(self) -> None:
        """注册内置条件处理器"""
        self.register_handler("time", TimeConditionHandler())
        self.register_handler("user", UserConditionHandler())
        self.register_handler("item", ItemConditionHandler())
        self.register_handler("keyword", KeywordConditionHandler())
        self.register_handler("trigger", TriggerConditionHandler())
        logger.debug("已注册内置条件处理器: time, user, item, keyword, trigger")
    
    def register_handler(self, condition_type: str, handler: ConditionHandler) -> None:
        """注册条件处理器
        
        Args:
            condition_type: 条件类型
            handler: 条件处理器实例
            
        Examples:
            >>> engine = RuleEngine()
            >>> class CustomHandler(ConditionHandler):
            ...     def evaluate(self, condition, context):
            ...         return context.get(condition.field) == condition.value
            >>> engine.register_handler("custom", CustomHandler())
        """
        self._condition_handlers[condition_type] = handler
        logger.debug(f"已注册条件处理器: {condition_type}")
    
    def get_handler(self, condition_type: str) -> Optional[ConditionHandler]:
        """获取条件处理器
        
        Args:
            condition_type: 条件类型
            
        Returns:
            Optional[ConditionHandler]: 条件处理器，如果不存在则返回 None
        """
        return self._condition_handlers.get(condition_type)
    
    def evaluate(self, rule: Rule, context: Dict[str, Any]) -> bool:
        """评估规则
        
        根据规则的逻辑操作符和条件，在给定的上下文中评估规则是否满足。
        
        Args:
            rule: 规则对象
            context: 上下文数据，包含条件评估所需的字段
            
        Returns:
            bool: 规则是否满足
            
        Raises:
            RuleEngineError: 评估过程中发生错误
        """
        try:
            if rule.logic == LogicOperator.AND:
                return self._evaluate_and(rule, context)
            elif rule.logic == LogicOperator.OR:
                return self._evaluate_or(rule, context)
            elif rule.logic == LogicOperator.NOT:
                return self._evaluate_not(rule, context)
            else:
                raise RuleEngineError(f"未知的逻辑操作符: {rule.logic}", rule=rule)
        except RuleEngineError:
            raise
        except Exception as e:
            raise RuleEngineError(f"规则评估失败: {e}", rule=rule)
    
    def _evaluate_and(self, rule: Rule, context: Dict[str, Any]) -> bool:
        """评估 AND 逻辑
        
        所有条件和子规则都必须满足。
        
        Args:
            rule: 规则对象
            context: 上下文数据
            
        Returns:
            bool: 是否满足 AND 逻辑
        """
        for condition in rule.conditions:
            if not self._evaluate_condition(condition, context):
                logger.debug(f"AND 条件不满足: {condition.type}.{condition.field}")
                return False
        
        for sub_rule in rule.sub_rules:
            if not self.evaluate(sub_rule, context):
                logger.debug(f"AND 子规则不满足: {sub_rule.logic.value}")
                return False
        
        return True
    
    def _evaluate_or(self, rule: Rule, context: Dict[str, Any]) -> bool:
        """评估 OR 逻辑
        
        任一条件或子规则满足即可。
        
        Args:
            rule: 规则对象
            context: 上下文数据
            
        Returns:
            bool: 是否满足 OR 逻辑
        """
        for condition in rule.conditions:
            if self._evaluate_condition(condition, context):
                logger.debug(f"OR 条件满足: {condition.type}.{condition.field}")
                return True
        
        for sub_rule in rule.sub_rules:
            if self.evaluate(sub_rule, context):
                logger.debug(f"OR 子规则满足: {sub_rule.logic.value}")
                return True
        
        return False
    
    def _evaluate_not(self, rule: Rule, context: Dict[str, Any]) -> bool:
        """评估 NOT 逻辑
        
        条件不满足时返回 True。
        
        Args:
            rule: 规则对象
            context: 上下文数据
            
        Returns:
            bool: 是否满足 NOT 逻辑
        """
        if rule.condition is None:
            raise RuleEngineError("NOT 规则缺少条件", rule=rule)
        
        result = not self._evaluate_condition(rule.condition, context)
        logger.debug(f"NOT 条件结果: {result}")
        return result
    
    def _evaluate_condition(self, condition: Condition, context: Dict[str, Any]) -> bool:
        """评估单个条件
        
        Args:
            condition: 条件对象
            context: 上下文数据
            
        Returns:
            bool: 条件是否满足
            
        Raises:
            RuleEngineError: 条件类型不存在或评估失败
        """
        handler = self._condition_handlers.get(condition.type)
        
        if handler is None:
            raise RuleEngineError(
                f"未知的条件类型: {condition.type}",
                condition=condition
            )
        
        try:
            result = handler.evaluate(condition, context)
            logger.debug(
                f"条件评估: {condition.type}.{condition.field} "
                f"{condition.operator} {condition.value} = {result}"
            )
            return result
        except RuleEngineError:
            raise
        except Exception as e:
            raise RuleEngineError(
                f"条件评估失败: {e}",
                condition=condition
            )
    
    def parse_from_json(self, json_str: str) -> Rule:
        """从 JSON 字符串解析规则
        
        Args:
            json_str: JSON 字符串
            
        Returns:
            Rule: 规则对象
            
        Raises:
            json.JSONDecodeError: JSON 格式错误
            KeyError: 缺少必需字段
            ValueError: 字段值无效
        """
        try:
            data = json.loads(json_str)
            return Rule.from_dict(data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            raise
        except (KeyError, ValueError) as e:
            logger.error(f"规则解析失败: {e}")
            raise
    
    def to_json(self, rule: Rule, indent: Optional[int] = 2) -> str:
        """将规则转换为 JSON 字符串
        
        Args:
            rule: 规则对象
            indent: 缩进空格数，None 表示不格式化
            
        Returns:
            str: JSON 字符串
        """
        try:
            data = rule.to_dict()
            return json.dumps(data, indent=indent, ensure_ascii=False)
        except Exception as e:
            logger.error(f"规则序列化失败: {e}")
            raise RuleEngineError(f"规则序列化失败: {e}", rule=rule)
    
    def parse_from_dict(self, data: Dict[str, Any]) -> Rule:
        """从字典解析规则
        
        Args:
            data: 规则字典数据
            
        Returns:
            Rule: 规则对象
            
        Raises:
            KeyError: 缺少必需字段
            ValueError: 字段值无效
        """
        return Rule.from_dict(data)
    
    def to_dict(self, rule: Rule) -> Dict[str, Any]:
        """将规则转换为字典
        
        Args:
            rule: 规则对象
            
        Returns:
            Dict[str, Any]: 规则字典
        """
        return rule.to_dict()
    
    def validate_rule(self, rule: Rule) -> List[str]:
        """验证规则结构
        
        检查规则的结构是否正确，所有条件类型是否有对应的处理器。
        
        Args:
            rule: 规则对象
            
        Returns:
            List[str]: 错误消息列表，空列表表示验证通过
        """
        errors = []
        self._validate_rule_recursive(rule, errors)
        return errors
    
    def _validate_rule_recursive(self, rule: Rule, errors: List[str]) -> None:
        """递归验证规则
        
        Args:
            rule: 规则对象
            errors: 错误消息列表
        """
        for condition in rule.conditions:
            if condition.type not in self._condition_handlers:
                errors.append(f"未知的条件类型: {condition.type}")
        
        if rule.condition:
            if rule.condition.type not in self._condition_handlers:
                errors.append(f"未知的条件类型: {rule.condition.type}")
        
        for sub_rule in rule.sub_rules:
            self._validate_rule_recursive(sub_rule, errors)
    
    def clear_cache(self) -> None:
        """清除规则评估缓存"""
        self._rule_cache.clear()
        logger.debug("规则缓存已清除")


rule_engine = RuleEngine()
