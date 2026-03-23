"""公共辅助函数模块

提供reply_server中各模块共用的辅助函数
"""
from pathlib import Path
from typing import Optional
from fastapi.responses import HTMLResponse


def read_html_file(static_dir: Path, filename: str) -> HTMLResponse:
    """读取HTML文件并返回HTMLResponse

    Args:
        static_dir: 静态文件目录路径
        filename: HTML文件名

    Returns:
        HTMLResponse: HTML响应，如果文件不存在返回错误响应
    """
    file_path = static_dir / filename
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(f.read())
    return HTMLResponse(f'<h3>{filename} not found</h3>')


def safe_int(value: str, default: int = 0) -> int:
    """安全转换为整数

    Args:
        value: 待转换的值
        default: 转换失败时的默认值

    Returns:
        int: 转换后的整数
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def mask_sensitive_value(value: str, visible_chars: int = 4) -> str:
    """遮蔽敏感值，只显示前visible_chars个字符

    Args:
        value: 敏感值
        visible_chars: 显示的字符数

    Returns:
        str: 遮蔽后的值
    """
    if not value:
        return ''
    if len(value) <= visible_chars:
        return '*' * len(value)
    return value[:visible_chars] + '*' * (len(value) - visible_chars)


__all__ = [
    'read_html_file',
    'safe_int',
    'mask_sensitive_value',
]