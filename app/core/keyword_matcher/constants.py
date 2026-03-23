"""
常量模块

包含关键词匹配模块使用的所有常量。
"""

# 匹配类型常量
MATCH_TYPE_EXACT = 'exact'       # 精确匹配
MATCH_TYPE_CONTAINS = 'contains' # 包含匹配（默认）
MATCH_TYPE_PREFIX = 'prefix'     # 前缀匹配
MATCH_TYPE_SUFFIX = 'suffix'     # 后缀匹配
MATCH_TYPE_REGEX = 'regex'       # 正则匹配
MATCH_TYPE_FUZZY = 'fuzzy'       # 模糊匹配

# 默认模糊匹配阈值
DEFAULT_FUZZY_THRESHOLD = 80

# 正则匹配超时时间（秒）
REGEX_TIMEOUT = 1.0

# 正则表达式安全限制
MAX_REGEX_LENGTH = 500  # 正则表达式最大长度
MAX_REGEX_NESTING_DEPTH = 5  # 最大嵌套深度
MAX_REGEX_QUANTIFIER_REPEAT = 100  # 最大重复次数

# JSON解析安全限制
MAX_JSON_STRING_LENGTH = 10000  # JSON字符串最大长度

# 消息最大长度限制
MAX_MESSAGE_LENGTH = 10000
