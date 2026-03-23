"""Unified API Response Module

Provides standardized response models and utility functions for all API endpoints.
"""
from typing import Optional, Any, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response format
    
    All API endpoints should use this format for consistency.
    
    Attributes:
        code: HTTP-like status code (200 for success, 4xx/5xx for errors)
        message: Human-readable message describing the result
        data: Optional payload containing the response data
    """
    code: int
    message: str
    data: Optional[T] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "Success",
                "data": None
            }
        }


def success(data: Any = None, message: str = "Success") -> dict:
    """Create a success response
    
    Args:
        data: Response payload
        message: Success message
        
    Returns:
        dict: Standardized success response
    """
    return {
        "code": 200,
        "message": message,
        "data": data
    }


def error(code: int = 500, message: str = "Error", data: Any = None) -> dict:
    """Create an error response
    
    Args:
        code: Error code (4xx for client errors, 5xx for server errors)
        message: Error message
        data: Optional error details
        
    Returns:
        dict: Standardized error response
    """
    return {
        "code": code,
        "message": message,
        "data": data
    }


def created(data: Any = None, message: str = "Created successfully") -> dict:
    """Create a 201 Created response
    
    Args:
        data: Response payload (typically contains the created resource ID)
        message: Success message
        
    Returns:
        dict: Standardized created response
    """
    return {
        "code": 201,
        "message": message,
        "data": data
    }


def updated(data: Any = None, message: str = "Updated successfully") -> dict:
    """Create an update success response
    
    Args:
        data: Response payload
        message: Success message
        
    Returns:
        dict: Standardized update response
    """
    return {
        "code": 200,
        "message": message,
        "data": data
    }


def deleted(message: str = "Deleted successfully") -> dict:
    """Create a delete success response
    
    Args:
        message: Success message
        
    Returns:
        dict: Standardized delete response
    """
    return {
        "code": 200,
        "message": message,
        "data": None
    }


def not_found(message: str = "Resource not found") -> dict:
    """Create a 404 Not Found response
    
    Args:
        message: Error message
        
    Returns:
        dict: Standardized not found response
    """
    return {
        "code": 404,
        "message": message,
        "data": None
    }


def bad_request(message: str = "Bad request", data: Any = None) -> dict:
    """Create a 400 Bad Request response
    
    Args:
        message: Error message
        data: Optional error details
        
    Returns:
        dict: Standardized bad request response
    """
    return {
        "code": 400,
        "message": message,
        "data": data
    }


def unauthorized(message: str = "Unauthorized") -> dict:
    """Create a 401 Unauthorized response
    
    Args:
        message: Error message
        
    Returns:
        dict: Standardized unauthorized response
    """
    return {
        "code": 401,
        "message": message,
        "data": None
    }


def forbidden(message: str = "Forbidden") -> dict:
    """Create a 403 Forbidden response
    
    Args:
        message: Error message
        
    Returns:
        dict: Standardized forbidden response
    """
    return {
        "code": 403,
        "message": message,
        "data": None
    }


def server_error(message: str = "Internal server error", data: Any = None) -> dict:
    """Create a 500 Internal Server Error response
    
    Args:
        message: Error message
        data: Optional error details
        
    Returns:
        dict: Standardized server error response
    """
    return {
        "code": 500,
        "message": message,
        "data": data
    }


# Convenience aliases for backward compatibility
def success_response(data: Any = None, message: str = "Success") -> dict:
    """Alias for success() for backward compatibility"""
    return success(data, message)


def error_response(code: int = 500, message: str = "Error", data: Any = None) -> dict:
    """Alias for error() for backward compatibility"""
    return error(code, message, data)


__all__ = [
    'ApiResponse',
    'success',
    'error',
    'created',
    'updated',
    'deleted',
    'not_found',
    'bad_request',
    'unauthorized',
    'forbidden',
    'server_error',
    'success_response',
    'error_response',
]
