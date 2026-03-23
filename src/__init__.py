"""
向后兼容层 - 重定向到新位置

从 'src' 导入已弃用，请使用 'app.core' 代替
"""
import sys
import warnings
import os

warnings.warn(
    "从 'src' 导入已弃用，请使用 'app.core' 代替",
    DeprecationWarning,
    stacklevel=2
)

# 添加 app 目录到路径
app_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app')
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from app.core import *
