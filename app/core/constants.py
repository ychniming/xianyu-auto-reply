"""
常量定义模块

集中管理项目中使用的魔法数字和常量配置
"""

# ==================== AI回复引擎相关常量 ====================

# 意图检测模型参数
INTENT_DETECTION_MAX_TOKENS: int = 10
INTENT_DETECTION_TEMPERATURE: float = 0.1

# AI回复生成模型参数
AI_REPLY_MAX_TOKENS: int = 100
AI_REPLY_TEMPERATURE: float = 0.7

# 对话历史相关
CONVERSATION_CONTEXT_LIMIT: int = 20  # 获取对话历史的最大条数
CONVERSATION_HISTORY_DISPLAY_COUNT: int = 10  # 显示给AI的最近消息条数

# 意图类型定义
INTENT_PRICE: str = "price"
INTENT_TECH: str = "tech"
INTENT_DEFAULT: str = "default"
INTENT_TYPES: tuple = (INTENT_PRICE, INTENT_TECH, INTENT_DEFAULT)

# 议价设置默认值
DEFAULT_MAX_BARGAIN_ROUNDS: int = 3
DEFAULT_MAX_DISCOUNT_PERCENT: int = 10
DEFAULT_MAX_DISCOUNT_AMOUNT: int = 100

# ==================== Cookie管理器相关常量 ====================

# 关键字缓存过期时间（秒）
KEYWORDS_CACHE_EXPIRY: int = 300  # 5分钟

# 异步任务超时时间（秒）
ASYNC_TASK_TIMEOUT: int = 5

# ==================== 图片处理相关常量 ====================

# CDN域名列表
CDN_DOMAINS: tuple = (
    "gw.alicdn.com",
    "img.alicdn.com",
    "cloud.goofish.com",
    "goofish.com",
    "taobaocdn.com",
    "tbcdn.cn",
    "aliimg.com",
)

# 支持的图片扩展名
IMAGE_EXTENSIONS: tuple = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
)

# ==================== 系统默认常量 ====================

# 默认启用状态
DEFAULT_ENABLED: bool = True

# 默认自动确认发货
DEFAULT_AUTO_CONFIRM: bool = True
