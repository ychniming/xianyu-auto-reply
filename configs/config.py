"""Configuration management module with Pydantic Settings support.

Provides type-safe configuration management with environment variable override.
"""
import os
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from dotenv import load_dotenv

# Load .env file if exists
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    model_config = ConfigDict(
        env_prefix="XIANYU_",
        extra="ignore"
    )
    
    db_path: str = Field(
        default="data/xianyu_data.db",
        description="Database file path"
    )


class JWTSettings(BaseSettings):
    """JWT authentication settings."""
    
    model_config = ConfigDict(
        env_prefix="XIANYU_",
        extra="ignore"
    )
    
    jwt_secret_key: str = Field(
        default="your-secret-key-here",
        description="JWT secret key for token signing"
    )
    jwt_expire_hours: int = Field(
        default=24,
        description="JWT token expiration time in hours"
    )
    session_timeout: int = Field(
        default=3600,
        description="Session timeout in seconds"
    )


class RateLimitSettings(BaseSettings):
    """Rate limiting settings."""
    
    model_config = ConfigDict(
        env_prefix="XIANYU_",
        extra="ignore"
    )
    
    rate_limit_global: str = Field(
        default="100/minute",
        description="Global rate limit"
    )
    rate_limit_login: str = Field(
        default="5/minute",
        description="Login endpoint rate limit"
    )
    rate_limit_register: str = Field(
        default="3/minute",
        description="Registration endpoint rate limit"
    )


class CacheSettings(BaseSettings):
    """Cache configuration settings."""
    
    model_config = ConfigDict(
        env_prefix="XIANYU_",
        extra="ignore"
    )
    
    keywords_cache_expiry: int = Field(
        default=300,
        description="Keywords cache expiry in seconds"
    )
    item_cache_expiry: int = Field(
        default=300,
        description="Item cache expiry in seconds"
    )
    item_cache_max_size: int = Field(
        default=100,
        description="Maximum item cache size"
    )
    keyword_matcher_cache_size: int = Field(
        default=1000,
        description="Keyword matcher cache size"
    )


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""
    
    model_config = ConfigDict(
        env_prefix="XIANYU_",
        extra="ignore"
    )
    
    log_level: str = Field(
        default="INFO",
        description="Log level (DEBUG, INFO, WARNING, ERROR)"
    )
    log_format: str = Field(
        default="text",
        description="Log format (json or text)"
    )
    log_rotation: str = Field(
        default="1 day",
        description="Log rotation interval"
    )
    log_retention: str = Field(
        default="7 days",
        description="Log retention period"
    )
    log_compression: str = Field(
        default="zip",
        description="Log compression format"
    )


class WebSocketSettings(BaseSettings):
    """WebSocket configuration settings."""
    
    model_config = ConfigDict(
        env_prefix="XIANYU_",
        extra="ignore"
    )
    
    websocket_url: str = Field(
        default="wss://wss-goofish.dingtalk.com/",
        description="WebSocket connection URL"
    )
    heartbeat_interval: int = Field(
        default=15,
        description="Heartbeat interval in seconds"
    )
    heartbeat_timeout: int = Field(
        default=5,
        description="Heartbeat timeout in seconds"
    )
    token_refresh_interval: int = Field(
        default=3600,
        description="Token refresh interval in seconds"
    )
    token_retry_interval: int = Field(
        default=300,
        description="Token retry interval in seconds"
    )
    message_expire_time: int = Field(
        default=300000,
        description="Message expiration time in milliseconds"
    )


class AIReplySettings(BaseSettings):
    """AI reply configuration settings."""
    
    model_config = ConfigDict(
        env_prefix="XIANYU_",
        extra="ignore"
    )
    
    ai_reply_enabled: bool = Field(
        default=False,
        description="Enable AI reply functionality"
    )
    default_ai_model: str = Field(
        default="qwen-plus",
        description="Default AI model"
    )
    default_ai_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        description="Default AI API base URL"
    )
    ai_request_timeout: int = Field(
        default=30,
        description="AI request timeout in seconds"
    )
    ai_max_tokens: int = Field(
        default=100,
        description="Maximum AI generation tokens"
    )


class AutoReplySettings(BaseSettings):
    """Auto reply configuration settings."""
    
    model_config = ConfigDict(
        env_prefix="XIANYU_",
        extra="ignore"
    )
    
    auto_reply_enabled: bool = Field(
        default=True,
        description="Enable auto reply functionality"
    )
    auto_reply_default_message: str = Field(
        default='亲爱的"{send_user_name}" 老板你好！所有宝贝都可以拍，秒发货的哈~不满意的话可以直接申请退款哈~',
        description="Default auto reply message"
    )
    auto_reply_max_retry: int = Field(
        default=3,
        description="Maximum retry count"
    )
    auto_reply_retry_interval: int = Field(
        default=5,
        description="Retry interval in seconds"
    )


class AppConfigSettings(BaseSettings):
    """Application-specific configuration loaded from YAML for backward compatibility."""

    model_config = ConfigDict(
        env_prefix="XIANYU_",
        extra="ignore"
    )

    cookies_value: str = Field(default="", description="Cookies value")
    cookies_last_update: str = Field(default="", description="Cookies last update time")
    api_endpoints: Dict[str, str] = Field(default_factory=dict, description="API endpoints")
    default_headers: Dict[str, str] = Field(default_factory=dict, description="Default HTTP headers")
    websocket_headers: Dict[str, str] = Field(default_factory=dict, description="WebSocket headers")
    app_config: Dict[str, Any] = Field(default_factory=dict, description="App configuration")
    manual_mode: Dict[str, Any] = Field(default_factory=dict, description="Manual mode settings")
    item_detail: Dict[str, Any] = Field(default_factory=dict, description="Item detail fetch settings")
    use_new_keyword_matcher: bool = Field(default=True, description="Use new keyword matcher")
    log_config_format: str = Field(default="", description="Log format string")

    @property
    def config(self) -> Dict[str, Any]:
        """Return all config values as a dictionary for backward compatibility."""
        return {
            'COOKIES': {
                'value': self.cookies_value,
                'last_update_time': self.cookies_last_update
            },
            'API_ENDPOINTS': self.api_endpoints,
            'DEFAULT_HEADERS': self.default_headers,
            'WEBSOCKET_HEADERS': self.websocket_headers,
            'APP_CONFIG': self.app_config,
            'MANUAL_MODE': self.manual_mode,
            'ITEM_DETAIL': self.item_detail,
            'USE_NEW_KEYWORD_MATCHER': self.use_new_keyword_matcher,
            'LOG_CONFIG': {
                'format': self.log_config_format
            }
        }


class AppSettings(BaseSettings):
    """Main application settings combining all configuration sections."""
    
    model_config = ConfigDict(
        env_prefix="XIANYU_",
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore"
    )
    
    # Application info
    app_name: str = Field(
        default="Xianyu Auto Reply",
        description="Application name"
    )
    app_version: str = Field(
        default="1.0.0",
        description="Application version"
    )
    debug: bool = Field(
        default=False,
        description="Debug mode"
    )
    
    # API settings
    api_host: str = Field(
        default="0.0.0.0",
        description="API server host"
    )
    api_port: int = Field(
        default=8080,
        description="API server port"
    )
    enable_docs: bool = Field(
        default=True,
        description="Enable API documentation"
    )
    
    # Nested settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    websocket: WebSocketSettings = Field(default_factory=WebSocketSettings)
    ai_reply: AIReplySettings = Field(default_factory=AIReplySettings)
    auto_reply: AutoReplySettings = Field(default_factory=AutoReplySettings)
    app_config: AppConfigSettings = Field(default_factory=AppConfigSettings)


class YAMLConfig:
    """YAML configuration bridge for backward compatibility.

    This class now delegates to settings.app_config to ensure
    single source of truth while maintaining backward compatibility.
    """

    _instance = None

    _KEY_MAPPING = {
        'WEBSOCKET_URL': ('websocket', 'websocket_url'),
        'HEARTBEAT_INTERVAL': ('websocket', 'heartbeat_interval'),
        'HEARTBEAT_TIMEOUT': ('websocket', 'heartbeat_timeout'),
        'TOKEN_REFRESH_INTERVAL': ('websocket', 'token_refresh_interval'),
        'TOKEN_RETRY_INTERVAL': ('websocket', 'token_retry_interval'),
        'MESSAGE_EXPIRE_TIME': ('websocket', 'message_expire_time'),
        'AUTO_REPLY.enabled': ('auto_reply', 'auto_reply_enabled'),
        'AUTO_REPLY.default_message': ('auto_reply', 'auto_reply_default_message'),
        'AUTO_REPLY.max_retry': ('auto_reply', 'auto_reply_max_retry'),
        'AUTO_REPLY.retry_interval': ('auto_reply', 'auto_reply_retry_interval'),
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(YAMLConfig, cls).__new__(cls)
        return cls._instance

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated key."""
        if key in self._KEY_MAPPING:
            section, attr = self._KEY_MAPPING[key]
            return getattr(getattr(settings, section), attr)

        keys = key.split('.')
        current = settings.app_config.config
        for k in keys:
            if isinstance(current, dict):
                current = current.get(k)
            else:
                return default
            if current is None:
                return default
        return current

    @property
    def config(self) -> Dict[str, Any]:
        """Get full configuration dictionary from settings."""
        return settings.app_config.config

    def save(self) -> None:
        """Save configuration back to YAML file (not recommended, use settings)."""
        import warnings
        warnings.warn(
            "YAMLConfig.save() is deprecated. Configuration should be done via "
            "environment variables or settings. This method will be removed in future versions.",
            DeprecationWarning,
            stacklevel=2
        )


# Create global instances
yaml_config = YAMLConfig()
settings = AppSettings()


# Export commonly used configuration items (backward compatibility)
def _get_env_or_yaml(env_key: str, yaml_key: str, default: Any = None) -> Any:
    """Get value from environment variable, YAML config, or default."""
    env_value = os.getenv(env_key)
    if env_value is not None:
        return env_value
    return yaml_config.get(yaml_key, default)


def _load_yaml_into_settings() -> None:
    """Load YAML configuration values into settings.app_config.

    This function bridges YAML-based legacy config with Pydantic Settings
    to maintain backward compatibility while providing type safety.
    """
    yaml_path = Path(__file__).parent / 'global_config.yml'
    if not yaml_path.exists():
        return

    with open(yaml_path, 'r', encoding='utf-8') as f:
        yaml_data = yaml.safe_load(f)

    if not yaml_data:
        return

    app_cfg = settings.app_config
    app_cfg.cookies_value = yaml_data.get('COOKIES', {}).get('value', '')
    app_cfg.cookies_last_update = yaml_data.get('COOKIES', {}).get('last_update_time', '')
    app_cfg.api_endpoints = yaml_data.get('API_ENDPOINTS', {})
    app_cfg.default_headers = yaml_data.get('DEFAULT_HEADERS', {})
    app_cfg.websocket_headers = yaml_data.get('WEBSOCKET_HEADERS', {})
    app_cfg.app_config = yaml_data.get('APP_CONFIG', {})
    app_cfg.manual_mode = yaml_data.get('MANUAL_MODE', {})
    app_cfg.item_detail = yaml_data.get('ITEM_DETAIL', {})
    app_cfg.use_new_keyword_matcher = yaml_data.get('USE_NEW_KEYWORD_MATCHER', True)
    app_cfg.log_config_format = yaml_data.get('LOG_CONFIG', {}).get('format', '')


_load_yaml_into_settings()


# Unified exports - all from Pydantic Settings (single source of truth)
# Backward compatibility aliases
COOKIES_STR = settings.app_config.cookies_value
COOKIES_LAST_UPDATE = settings.app_config.cookies_last_update
WEBSOCKET_URL = settings.websocket.websocket_url
HEARTBEAT_INTERVAL = settings.websocket.heartbeat_interval
HEARTBEAT_TIMEOUT = settings.websocket.heartbeat_timeout
TOKEN_REFRESH_INTERVAL = settings.websocket.token_refresh_interval
TOKEN_RETRY_INTERVAL = settings.websocket.token_retry_interval
MESSAGE_EXPIRE_TIME = settings.websocket.message_expire_time
API_ENDPOINTS = settings.app_config.api_endpoints
DEFAULT_HEADERS = settings.app_config.default_headers
WEBSOCKET_HEADERS = settings.app_config.websocket_headers
APP_CONFIG = settings.app_config.app_config
AUTO_REPLY = {
    'enabled': settings.auto_reply.auto_reply_enabled,
    'default_message': settings.auto_reply.auto_reply_default_message,
    'max_retry': settings.auto_reply.auto_reply_max_retry,
    'retry_interval': settings.auto_reply.auto_reply_retry_interval,
    'api': {
        'enabled': False,
        'url': f'http://localhost:{settings.api_port}/xianyu/reply',
        'timeout': 10
    }
}
MANUAL_MODE = settings.app_config.manual_mode
LOG_CONFIG = {
    'level': settings.logging.log_level,
    'format': settings.app_config.log_config_format or '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>',
    'rotation': settings.logging.log_rotation,
    'retention': settings.logging.log_retention,
    'compression': settings.logging.log_compression
}

ITEM_DETAIL = settings.app_config.item_detail

_cookies_raw = settings.app_config.cookies_value
COOKIES_LIST = [{'id': 'default', 'value': _cookies_raw}] if _cookies_raw else []

USE_NEW_KEYWORD_MATCHER = settings.app_config.use_new_keyword_matcher
KEYWORD_MATCHER_CACHE_SIZE = settings.cache.keyword_matcher_cache_size


# Legacy Config class for backward compatibility
class Config:
    """Legacy configuration class for backward compatibility.
    
    Delegates to YAMLConfig for actual configuration loading.
    """
    
    _instance = None
    _config = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = yaml_config
        return cls._instance

    @property
    def config(self) -> Dict[str, Any]:
        return yaml_config.config


# Create legacy config instance
config = Config()


__all__ = [
    'settings',
    'yaml_config',
    'config',
    'AppSettings',
    'AppConfigSettings',
    'DatabaseSettings',
    'JWTSettings',
    'RateLimitSettings',
    'CacheSettings',
    'LoggingSettings',
    'WebSocketSettings',
    'AIReplySettings',
    'AutoReplySettings',
    # Legacy exports
    'COOKIES_STR',
    'COOKIES_LAST_UPDATE',
    'WEBSOCKET_URL',
    'HEARTBEAT_INTERVAL',
    'HEARTBEAT_TIMEOUT',
    'TOKEN_REFRESH_INTERVAL',
    'TOKEN_RETRY_INTERVAL',
    'MESSAGE_EXPIRE_TIME',
    'API_ENDPOINTS',
    'DEFAULT_HEADERS',
    'WEBSOCKET_HEADERS',
    'APP_CONFIG',
    'AUTO_REPLY',
    'MANUAL_MODE',
    'LOG_CONFIG',
    'COOKIES_LIST',
    'USE_NEW_KEYWORD_MATCHER',
    'KEYWORD_MATCHER_CACHE_SIZE',
    'ITEM_DETAIL',
]
