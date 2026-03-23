# 代码规范

[返回主目录](./project_rules.md)

---

## 3.1 Python 代码规范

### 命名规范

```python
# 模块名：小写字母+下划线
# 文件名示例：xianyu_utils.py, cookie_manager.py

# 类名：大驼峰命名法
class CookieManager:
    class AIReplyEngine:
        pass

# 函数名：小写字母+下划线
def get_cookie_details(cookie_id: str) -> dict:
    pass

def update_keywords(cookie_id: str, kw_list: list) -> None:
    pass

# 变量名：小写字母+下划线
cookie_value = "..."
user_id = 123

# 常量名：大写字母+下划线
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30

# 私有属性/方法：单下划线前缀
def _load_config(self):
    pass

# 强私有属性/方法：双下划线前缀
def __encrypt_data(self, data):
    pass
```

### 类型注解

```python
from typing import Dict, List, Optional, Any, Tuple

def get_all_cookies(self) -> Dict[str, str]:
    """获取所有Cookie"""
    pass

def save_keywords(self, cookie_id: str, kw_list: List[Tuple[str, str]]) -> None:
    """保存关键词"""
    pass

def get_cookie_details(self, cookie_id: str) -> Optional[Dict[str, Any]]:
    """获取Cookie详情，可能返回None"""
    pass
```

### 文档字符串

```python
def process_message(self, message: str, cookie_id: str) -> str:
    """处理收到的消息并返回回复内容
    
    Args:
        message: 用户发送的消息内容
        cookie_id: 账号ID
        
    Returns:
        str: 自动回复的内容
        
    Raises:
        ValueError: 当cookie_id不存在时抛出
    """
    pass
```

### 代码组织

```python
# 导入顺序：标准库 -> 第三方库 -> 本地模块
import os
import sys
import asyncio
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from loguru import logger
from pydantic import BaseModel

from db_manager import db_manager
from config import config
```

### 异常处理

```python
# 使用具体的异常类型
try:
    result = await self._send_message(content)
except asyncio.TimeoutError:
    logger.error(f"发送消息超时: {cookie_id}")
    raise
except ConnectionError as e:
    logger.error(f"连接错误: {e}")
    await self._reconnect()
except Exception as e:
    logger.error(f"未知错误: {e}")
    raise

# 不要使用裸露的 except
# 错误示例：
# except:
#     pass
```

### 日志规范

```python
from loguru import logger

# 使用不同级别
logger.debug("调试信息：变量值 = {}", value)
logger.info("正常信息：账号 {} 启动成功", cookie_id)
logger.warning("警告信息：Cookie即将过期")
logger.error("错误信息：发送失败 - {}", error_msg)
logger.critical("严重错误：数据库损坏")

# 结构化日志
logger.info("消息处理完成", extra={
    "cookie_id": cookie_id,
    "message_type": "text",
    "response_time": 0.5
})
```

---

## 3.2 JavaScript 代码规范

### 命名规范

```javascript
// 变量名：小驼峰命名法
let userName = '';
let cookieId = '';

// 常量名：大写字母+下划线
const API_BASE = location.origin;
const MAX_RETRY = 3;

// 函数名：小驼峰命名法
function fetchAccountList() {}
function updateCookieStatus() {}

// 类名：大驼峰命名法
class APIModule {}
class AuthModule {}

// 私有方法：下划线前缀
function _handleError(error) {}
```

### 模块化规范

```javascript
// 模块定义
const UtilsModule = (function() {
    // 私有变量
    let _cache = {};
    
    // 私有方法
    function _validateInput(input) {
        return input && input.trim();
    }
    
    // 公共方法
    return {
        showToast: function(message, type) {
            // 实现
        },
        showLoading: function() {
            // 实现
        }
    };
})();

// 模块导出（全局）
window.UtilsModule = UtilsModule;
```

### 异步处理

```javascript
// 使用 async/await
async function fetchAccountList() {
    try {
        const response = await fetchJSON('/api/accounts');
        return response.data;
    } catch (error) {
        handleApiError(error);
        return [];
    }
}

// 错误处理
async function updateCookie(cookieId, value) {
    if (!cookieId || !value) {
        showToast('参数错误', 'error');
        return false;
    }
    
    try {
        await fetchJSON('/api/cookie/update', {
            method: 'POST',
            body: JSON.stringify({ cookieId, value })
        });
        showToast('更新成功', 'success');
        return true;
    } catch (error) {
        handleApiError(error);
        return false;
    }
}
```

---

## 3.3 文件大小限制

| 文件类型 | 建议行数 | 最大行数 |
|---------|---------|---------|
| Python模块 | 200-400行 | 800行 |
| JavaScript模块 | 200-400行 | 600行 |
| 单个函数 | ≤50行 | 100行 |
| 单个类 | ≤300行 | 500行 |
