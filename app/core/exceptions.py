"""
闲鱼自动回复系统 - 异常模块

定义系统所有业务异常类和错误码枚举。
"""

from enum import Enum
from typing import Optional, Any


class ErrorCode(Enum):
    """错误码枚举
    
    定义系统中所有业务错误码，便于错误追踪和前端处理。
    
    Examples:
        >>> ErrorCode.AUTH_FAILED.value
        'AUTH_001'
        >>> ErrorCode.RESOURCE_NOT_FOUND.description
        '请求的资源不存在'
    """
    
    # 认证相关错误 (AUTH_xxx)
    AUTH_FAILED = ("AUTH_001", "认证失败")
    TOKEN_EXPIRED = ("AUTH_002", "令牌已过期")
    TOKEN_INVALID = ("AUTH_003", "无效的令牌")
    LOGIN_REQUIRED = ("AUTH_004", "请先登录")
    
    # 权限相关错误 (PERM_xxx)
    PERMISSION_DENIED = ("PERM_001", "权限不足")
    ADMIN_REQUIRED = ("PERM_002", "需要管理员权限")
    RESOURCE_FORBIDDEN = ("PERM_003", "无权访问此资源")
    
    # 资源相关错误 (RES_xxx)
    RESOURCE_NOT_FOUND = ("RES_001", "请求的资源不存在")
    USER_NOT_FOUND = ("RES_002", "用户不存在")
    COOKIE_NOT_FOUND = ("RES_003", "Cookie不存在")
    ITEM_NOT_FOUND = ("RES_004", "商品不存在")
    KEYWORD_NOT_FOUND = ("RES_005", "关键词不存在")
    
    # 验证相关错误 (VAL_xxx)
    VALIDATION_FAILED = ("VAL_001", "数据验证失败")
    INVALID_INPUT = ("VAL_002", "输入参数无效")
    MISSING_REQUIRED_FIELD = ("VAL_003", "缺少必填字段")
    INVALID_FORMAT = ("VAL_004", "格式不正确")
    
    # 冲突相关错误 (CONF_xxx)
    RESOURCE_CONFLICT = ("CONF_001", "资源已存在")
    DUPLICATE_COOKIE = ("CONF_002", "Cookie已存在")
    DUPLICATE_USERNAME = ("CONF_003", "用户名已存在")
    
    # 限流相关错误 (RATE_xxx)
    RATE_LIMIT_EXCEEDED = ("RATE_001", "请求过于频繁")
    TOO_MANY_REQUESTS = ("RATE_002", "请求次数超限")
    
    # 数据库相关错误 (DB_xxx)
    DATABASE_ERROR = ("DB_001", "数据库操作失败")
    DATABASE_CONNECTION = ("DB_002", "数据库连接失败")
    DATABASE_QUERY = ("DB_003", "数据库查询错误")
    
    # 外部服务相关错误 (EXT_xxx)
    EXTERNAL_SERVICE_ERROR = ("EXT_001", "外部服务错误")
    AI_SERVICE_ERROR = ("EXT_002", "AI服务错误")
    WEBSOCKET_ERROR = ("EXT_003", "WebSocket连接错误")
    
    @property
    def code(self) -> str:
        """获取错误码"""
        return self.value[0]
    
    @property
    def description(self) -> str:
        """获取错误描述"""
        return self.value[1]


class XianyuBaseException(Exception):
    """闲鱼系统异常基类
    
    所有业务异常的基类，提供统一的异常处理接口。
    
    Attributes:
        message: 错误消息
        error_code: 错误码
        status_code: HTTP状态码
        details: 额外的错误详情
    
    Examples:
        >>> error = XianyuBaseException("系统错误", ErrorCode.DATABASE_ERROR, 500)
        >>> str(error)
        '系统错误 [DB_001]'
        >>> error.status_code
        500
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[ErrorCode] = None,
        status_code: int = 500,
        details: Optional[Any] = None
    ):
        """初始化异常
        
        Args:
            message: 错误消息
            error_code: 错误码枚举
            status_code: HTTP状态码
            details: 额外的错误详情
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details
    
    def __str__(self) -> str:
        """返回异常字符串表示"""
        if self.error_code:
            return f"{self.message} [{self.error_code.code}]"
        return self.message
    
    def to_dict(self) -> dict:
        """转换为字典格式
        
        Returns:
            包含异常信息的字典
        """
        result = {
            "message": self.message,
            "status_code": self.status_code,
        }
        if self.error_code:
            result["error_code"] = self.error_code.code
            result["error_description"] = self.error_code.description
        if self.details:
            result["details"] = self.details
        return result


class AuthenticationError(XianyuBaseException):
    """认证失败异常
    
    当用户认证失败时抛出，如登录失败、令牌无效等。
    
    Examples:
        >>> raise AuthenticationError("用户名或密码错误")
        >>> raise AuthenticationError("令牌已过期", ErrorCode.TOKEN_EXPIRED)
    """
    
    def __init__(
        self,
        message: str = "认证失败",
        error_code: ErrorCode = ErrorCode.AUTH_FAILED,
        details: Optional[Any] = None
    ):
        """初始化认证异常
        
        Args:
            message: 错误消息
            error_code: 错误码
            details: 额外的错误详情
        """
        super().__init__(message, error_code, status_code=401, details=details)


class PermissionDeniedError(XianyuBaseException):
    """权限不足异常
    
    当用户没有足够权限执行操作时抛出。
    
    Examples:
        >>> raise PermissionDeniedError("需要管理员权限")
        >>> raise PermissionDeniedError("无权访问此资源", ErrorCode.RESOURCE_FORBIDDEN)
    """
    
    def __init__(
        self,
        message: str = "权限不足",
        error_code: ErrorCode = ErrorCode.PERMISSION_DENIED,
        details: Optional[Any] = None
    ):
        """初始化权限异常
        
        Args:
            message: 错误消息
            error_code: 错误码
            details: 额外的错误详情
        """
        super().__init__(message, error_code, status_code=403, details=details)


class ResourceNotFoundError(XianyuBaseException):
    """资源不存在异常
    
    当请求的资源不存在时抛出。
    
    Examples:
        >>> raise ResourceNotFoundError("用户不存在", ErrorCode.USER_NOT_FOUND)
        >>> raise ResourceNotFoundError("Cookie不存在", ErrorCode.COOKIE_NOT_FOUND)
    """
    
    def __init__(
        self,
        message: str = "请求的资源不存在",
        error_code: ErrorCode = ErrorCode.RESOURCE_NOT_FOUND,
        details: Optional[Any] = None
    ):
        """初始化资源不存在异常
        
        Args:
            message: 错误消息
            error_code: 错误码
            details: 额外的错误详情
        """
        super().__init__(message, error_code, status_code=404, details=details)


class ValidationError(XianyuBaseException):
    """验证失败异常
    
    当数据验证失败时抛出，如参数格式错误、必填字段缺失等。
    
    Examples:
        >>> raise ValidationError("用户名格式不正确", ErrorCode.INVALID_FORMAT)
        >>> raise ValidationError("缺少必填字段", ErrorCode.MISSING_REQUIRED_FIELD)
    """
    
    def __init__(
        self,
        message: str = "数据验证失败",
        error_code: ErrorCode = ErrorCode.VALIDATION_FAILED,
        details: Optional[Any] = None
    ):
        """初始化验证异常
        
        Args:
            message: 错误消息
            error_code: 错误码
            details: 额外的错误详情
        """
        super().__init__(message, error_code, status_code=400, details=details)


class ConflictError(XianyuBaseException):
    """资源冲突异常
    
    当资源已存在或存在冲突时抛出。
    
    Examples:
        >>> raise ConflictError("用户名已存在", ErrorCode.DUPLICATE_USERNAME)
        >>> raise ConflictError("Cookie已存在", ErrorCode.DUPLICATE_COOKIE)
    """
    
    def __init__(
        self,
        message: str = "资源已存在",
        error_code: ErrorCode = ErrorCode.RESOURCE_CONFLICT,
        details: Optional[Any] = None
    ):
        """初始化冲突异常
        
        Args:
            message: 错误消息
            error_code: 错误码
            details: 额外的错误详情
        """
        super().__init__(message, error_code, status_code=409, details=details)


class RateLimitError(XianyuBaseException):
    """请求过于频繁异常
    
    当请求频率超过限制时抛出。
    
    Examples:
        >>> raise RateLimitError("请求过于频繁，请稍后再试")
        >>> raise RateLimitError("请求次数超限", ErrorCode.TOO_MANY_REQUESTS)
    """
    
    def __init__(
        self,
        message: str = "请求过于频繁",
        error_code: ErrorCode = ErrorCode.RATE_LIMIT_EXCEEDED,
        details: Optional[Any] = None
    ):
        """初始化限流异常
        
        Args:
            message: 错误消息
            error_code: 错误码
            details: 额外的错误详情
        """
        super().__init__(message, error_code, status_code=429, details=details)


class DatabaseError(XianyuBaseException):
    """数据库错误异常
    
    当数据库操作失败时抛出。
    
    Examples:
        >>> raise DatabaseError("数据库连接失败", ErrorCode.DATABASE_CONNECTION)
        >>> raise DatabaseError("查询执行失败", ErrorCode.DATABASE_QUERY)
    """
    
    def __init__(
        self,
        message: str = "数据库操作失败",
        error_code: ErrorCode = ErrorCode.DATABASE_ERROR,
        details: Optional[Any] = None
    ):
        """初始化数据库异常
        
        Args:
            message: 错误消息
            error_code: 错误码
            details: 额外的错误详情
        """
        super().__init__(message, error_code, status_code=500, details=details)


class ExternalServiceError(XianyuBaseException):
    """外部服务错误异常
    
    当调用外部服务失败时抛出，如AI服务、WebSocket等。
    
    Examples:
        >>> raise ExternalServiceError("AI服务响应超时", ErrorCode.AI_SERVICE_ERROR)
        >>> raise ExternalServiceError("WebSocket连接断开", ErrorCode.WEBSOCKET_ERROR)
    """
    
    def __init__(
        self,
        message: str = "外部服务错误",
        error_code: ErrorCode = ErrorCode.EXTERNAL_SERVICE_ERROR,
        details: Optional[Any] = None
    ):
        """初始化外部服务异常
        
        Args:
            message: 错误消息
            error_code: 错误码
            details: 额外的错误详情
        """
        super().__init__(message, error_code, status_code=502, details=details)


__all__ = [
    # 枚举
    'ErrorCode',
    # 基类
    'XianyuBaseException',
    # 业务异常
    'AuthenticationError',
    'PermissionDeniedError',
    'ResourceNotFoundError',
    'ValidationError',
    'ConflictError',
    'RateLimitError',
    'DatabaseError',
    'ExternalServiceError',
]
