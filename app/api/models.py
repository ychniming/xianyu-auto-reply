"""数据模型模块

提供FastAPI应用使用的数据模型
"""
from pydantic import BaseModel


class RequestModel(BaseModel):
    """自动回复请求模型"""
    cookie_id: str
    msg_time: str
    user_url: str
    send_user_id: str
    send_user_name: str
    item_id: str
    send_message: str
    chat_id: str


class ResponseData(BaseModel):
    """回复数据模型"""
    send_msg: str


class ResponseModel(BaseModel):
    """统一响应模型"""
    code: int
    data: ResponseData


__all__ = [
    'RequestModel',
    'ResponseData',
    'ResponseModel',
]
