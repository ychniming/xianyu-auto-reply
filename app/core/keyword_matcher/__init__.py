"""
关键词匹配模块

使用 Aho-Corasick 算法实现高效的关键词匹配，支持多账号独立缓存、
热更新、图片关键词和变量替换功能。

支持的匹配类型：
- exact: 精确匹配，消息完全等于关键词
- contains: 包含匹配，消息包含关键词（Aho-Corasick 直接匹配）
- prefix: 前缀匹配，消息以关键词开头
- suffix: 后缀匹配，消息以关键词结尾
- regex: 正则匹配，消息匹配正则表达式（带超时保护）
- fuzzy: 模糊匹配，消息与关键词相似度超过阈值
"""

from app.core.keyword_matcher.matcher import KeywordMatcher

# 全局单例实例
keyword_matcher = KeywordMatcher()

__all__ = [
    'KeywordMatcher',
    'keyword_matcher',
    'MATCH_TYPE_EXACT',
    'MATCH_TYPE_CONTAINS',
    'MATCH_TYPE_PREFIX',
    'MATCH_TYPE_SUFFIX',
    'MATCH_TYPE_REGEX',
    'MATCH_TYPE_FUZZY',
    'DEFAULT_FUZZY_THRESHOLD',
    'REGEX_TIMEOUT',
    'MAX_REGEX_LENGTH',
    'MAX_REGEX_NESTING_DEPTH',
    'MAX_REGEX_QUANTIFIER_REPEAT',
    'MAX_JSON_STRING_LENGTH',
]

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
