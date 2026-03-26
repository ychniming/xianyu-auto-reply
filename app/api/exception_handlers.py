"""
闲鱼自动回复系统 - 全局异常处理器

提供统一的异常处理机制，确保所有API返回一致的错误响应格式。
"""

import traceback
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import ErrorCode, XianyuBaseException
from app.api.response import error


def xianyu_exception_handler(request: Request, exc: XianyuBaseException) -> JSONResponse:
    """处理闲鱼系统业务异常
    
    捕获所有继承自 XianyuBaseException 的异常，返回统一格式的错误响应。
    
    Args:
        request: FastAPI 请求对象
        exc: 闲鱼系统异常实例
        
    Returns:
        JSONResponse: 包含错误信息的 JSON 响应
        
    Examples:
        当业务代码抛出异常时：
        >>> raise ResourceNotFoundError("用户不存在", ErrorCode.USER_NOT_FOUND)
        
        返回响应：
        {
            "code": 404,
            "message": "用户不存在",
            "data": {
                "error_code": "RES_002",
                "error_description": "用户不存在",
                "details": null
            }
        }
    """
    # 记录业务异常日志
    logger.warning(
        "业务异常: {} | 路径: {} | 方法: {} | 状态码: {}",
        str(exc),
        request.url.path,
        request.method,
        exc.status_code
    )
    
    # 构建错误响应数据
    error_data: Dict[str, Any] = {}
    
    if exc.error_code:
        error_data["error_code"] = exc.error_code.code
        error_data["error_description"] = exc.error_code.description
    
    if exc.details is not None:
        error_data["details"] = exc.details
    
    # 如果 error_data 为空，设置为 None
    if not error_data:
        error_data = None
    
    # 返回统一格式的错误响应
    response = error(
        code=exc.status_code,
        message=exc.message,
        data=error_data
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response
    )


def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """处理 Pydantic 验证错误
    
    捕获请求参数验证失败异常，返回详细的验证错误信息。
    
    Args:
        request: FastAPI 请求对象
        exc: 请求验证错误实例
        
    Returns:
        JSONResponse: 包含验证错误详情的 JSON 响应
        
    Examples:
        当请求参数验证失败时：
        POST /api/users {"username": ""}  # username 不能为空
        
        返回响应：
        {
            "code": 400,
            "message": "请求参数验证失败",
            "data": {
                "error_code": "VAL_001",
                "error_description": "数据验证失败",
                "details": [
                    {
                        "field": "username",
                        "message": "用户名不能为空",
                        "type": "value_error"
                    }
                ]
            }
        }
    """
    # 记录验证错误日志
    logger.warning(
        "参数验证失败: {} | 路径: {} | 方法: {}",
        str(exc),
        request.url.path,
        request.method
    )
    
    # 解析验证错误详情
    errors: List[Dict[str, Any]] = []
    
    for error_item in exc.errors():
        # 获取字段路径
        field_path = ".".join(str(loc) for loc in error_item.get("loc", []))
        
        # 构建错误详情
        error_detail = {
            "field": field_path,
            "message": error_item.get("msg", "验证失败"),
            "type": error_item.get("type", "validation_error")
        }
        
        # 如果有输入值，添加到详情中（敏感信息已过滤）
        if "input" in error_item and field_path not in ["password", "token", "cookie"]:
            error_detail["input"] = error_item["input"]
        
        errors.append(error_detail)
    
    # 构建错误响应数据
    error_data = {
        "error_code": ErrorCode.VALIDATION_FAILED.code,
        "error_description": ErrorCode.VALIDATION_FAILED.description,
        "details": errors
    }
    
    # 返回统一格式的错误响应
    response = error(
        code=status.HTTP_400_BAD_REQUEST,
        message="请求参数验证失败",
        data=error_data
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=response
    )


def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理所有未捕获的异常
    
    作为最后的异常处理器，捕获所有未被其他处理器处理的异常。
    记录详细的错误日志，返回通用错误信息，不暴露敏感信息。
    
    Args:
        request: FastAPI 请求对象
        exc: 异常实例
        
    Returns:
        JSONResponse: 包含通用错误信息的 JSON 响应
        
    Examples:
        当系统发生未预期的异常时：
        >>> raise RuntimeError("数据库连接池耗尽")
        
        返回响应：
        {
            "code": 500,
            "message": "服务器内部错误，请稍后重试",
            "data": null
        }
        
        日志中记录：
        ERROR - 未捕获异常: RuntimeError: 数据库连接池耗尽
        Traceback (most recent call last):
          ...
    """
    # 获取异常堆栈信息
    tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    
    # 记录详细的错误日志（包含堆栈信息）
    logger.error(
        "未捕获异常: {} | 路径: {} | 方法: {} | 异常类型: {}\n{}",
        str(exc),
        request.url.path,
        request.method,
        type(exc).__name__,
        tb_str
    )
    
    # 构建错误响应数据（生产环境不暴露敏感信息）
    error_data = {
        "error_code": ErrorCode.DATABASE_ERROR.code if "database" in str(exc).lower() 
                      else ErrorCode.EXTERNAL_SERVICE_ERROR.code,
        "error_description": "系统内部错误"
    }
    
    # 返回统一格式的错误响应
    response = error(
        code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="服务器内部错误，请稍后重试",
        data=error_data
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response
    )


def register_exception_handlers(app: FastAPI) -> None:
    """注册所有异常处理器到 FastAPI 应用
    
    将所有异常处理器注册到 FastAPI 应用实例，确保全局异常处理。
    应在应用启动时调用此函数。
    
    Args:
        app: FastAPI 应用实例
        
    Examples:
        在应用启动时注册：
        >>> from fastapi import FastAPI
        >>> from app.api.exception_handlers import register_exception_handlers
        >>> 
        >>> app = FastAPI()
        >>> register_exception_handlers(app)
        
    注意:
        异常处理器的注册顺序很重要：
        1. 具体异常（XianyuBaseException）应先注册
        2. 通用异常（Exception）应最后注册
        FastAPI 会按照从具体到通用的顺序匹配异常处理器
    """
    # 注册闲鱼系统业务异常处理器
    app.add_exception_handler(XianyuBaseException, xianyu_exception_handler)
    
    # 注册请求验证异常处理器
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # 注册通用异常处理器（必须最后注册，作为兜底）
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("全局异常处理器注册完成")


__all__ = [
    'xianyu_exception_handler',
    'validation_exception_handler',
    'generic_exception_handler',
    'register_exception_handlers',
]
