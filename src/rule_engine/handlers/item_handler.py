"""
商品条件处理器模块

处理与商品相关的条件判断。
"""

from typing import Any, Dict

from src.rule_engine.handlers.base import ConditionHandler
from src.rule_engine.operators import ConditionOperator
from src.rule_engine.exceptions import RuleEngineError


class ItemConditionHandler(ConditionHandler):
    """商品条件处理器
    
    处理与商品相关的条件判断，支持商品ID、价格、库存、分类等字段。
    
    支持的字段：
    - item_id: 商品ID
    - title: 商品标题
    - price: 商品价格
    - stock: 库存数量
    - category: 商品分类
    - status: 商品状态
    
    支持的操作符：
    - eq, ne, gt, lt, gte, lte: 基本比较
    - between: 范围比较
    - in, not_in: 列表包含
    - contains, not_contains: 字符串包含
    - starts_with, ends_with: 前缀/后缀匹配
    
    Examples:
        >>> handler = ItemConditionHandler()
        >>> from src.rule_engine import Condition
        >>> condition = Condition(type="item", field="price", operator="between", value=[10, 100])
        >>> context = {"price": 50}
        >>> result = handler.evaluate(condition, context)
        >>> print(result)  # True
    """
    
    def evaluate(self, condition, context: Dict[str, Any]) -> bool:
        """评估商品条件
        
        Args:
            condition: 商品条件
            context: 上下文数据，包含商品字段
            
        Returns:
            bool: 条件是否满足
            
        Raises:
            RuleEngineError: 字段不存在
        """
        field_value = context.get(condition.field)
        
        if field_value is None:
            raise RuleEngineError(f"商品字段不存在: {condition.field}")
        
        return self._compare(field_value, condition.operator, condition.value)
    
    def _compare(self, field_value: Any, operator: str, value: Any) -> bool:
        """执行比较操作
        
        扩展基础比较操作，支持between、contains和前缀/后缀匹配操作符。
        
        Args:
            field_value: 字段值
            operator: 操作符
            value: 比较值
            
        Returns:
            bool: 比较结果
        """
        if operator == ConditionOperator.BETWEEN.value:
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                raise RuleEngineError("between 操作符需要包含两个值的列表")
            return value[0] <= field_value <= value[1]
        elif operator == ConditionOperator.CONTAINS.value:
            return value in str(field_value)
        elif operator == ConditionOperator.NOT_CONTAINS.value:
            return value not in str(field_value)
        elif operator == ConditionOperator.STARTS_WITH.value:
            return str(field_value).startswith(value)
        elif operator == ConditionOperator.ENDS_WITH.value:
            return str(field_value).endswith(value)
        
        return super()._compare(field_value, operator, value)
