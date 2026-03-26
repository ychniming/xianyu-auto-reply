---
title: 工程规范
description: 闲鱼自动回复系统的编码规范和工程实践
lastUpdated: 2026-03-25
maintainer: Doc Keeper Agent
---

# 工程规范

[返回索引](../INDEX.md)

## Python 编码规范

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

# 私有方法：单下划线前缀
def _load_config(self):
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

### 导入顺序

```python
# 1. 标准库
import os
import sys
import asyncio
from typing import Dict, List, Optional

# 2. 第三方库
from fastapi import FastAPI, HTTPException
from loguru import logger
from pydantic import BaseModel

# 3. 本地模块
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

# 禁止裸露的 except
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

## JavaScript 编码规范

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
```

## 文件大小限制

| 文件类型 | 建议行数 | 最大行数 |
|---------|---------|---------|
| Python模块 | 200-400行 | 800行 |
| JavaScript模块 | 200-400行 | 600行 |
| 单个函数 | ≤50行 | 100行 |
| 单个类 | ≤300行 | 500行 |

## Git 提交规范

### 提交信息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型说明

| 类型 | 说明 |
|------|------|
| feat | 新功能 |
| fix | 修复 Bug |
| docs | 文档更新 |
| style | 代码格式 |
| refactor | 重构 |
| test | 测试 |
| chore | 构建/工具 |

### 示例

```
feat(message): 添加消息撤回功能

- 支持撤回 2 分钟内的消息
- 添加撤回确认弹窗
- 记录撤回日志

Closes #123
```

## 代码审查清单

### 功能正确性

- [ ] 功能符合需求
- [ ] 边界条件处理
- [ ] 错误处理完整
- [ ] 日志记录适当

### 代码质量

- [ ] 命名清晰
- [ ] 结构合理
- [ ] 无重复代码
- [ ] 注释适当

### 安全性

- [ ] 无敏感信息泄露
- [ ] 输入验证
- [ ] 权限检查
- [ ] SQL 注入防护

### 性能

- [ ] 无明显性能问题
- [ ] 数据库查询优化
- [ ] 缓存使用合理

## 相关文档

- [产品原则](./principles.md)
- [团队文化](./culture.md)
- [分层设计](../architecture/layers.md)

---

**维护者：** Doc Keeper Agent  
**最后更新：** 2026-03-25
