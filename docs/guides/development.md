---
title: 开发指南
description: 闲鱼自动回复系统的开发环境搭建和开发规范
lastUpdated: 2026-03-25
maintainer: Doc Keeper Agent
---

# 开发指南

[返回索引](../INDEX.md)

## 环境搭建

### 1. 克隆项目

```bash
git clone https://github.com/zhinianboke/xianyu-auto-reply.git
cd xianyu-auto-reply
```

### 2. 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
# 安装 Python 依赖
pip install --upgrade pip
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt  # 如果存在
```

### 4. 安装 Playwright

```bash
# 安装浏览器
playwright install chromium

# 安装系统依赖（Linux）
playwright install-deps
```

### 5. 配置环境变量

```bash
# 复制配置模板
cp configs/.env.example configs/.env

# 编辑配置
nano configs/.env
```

### 6. 启动开发服务器

```bash
python scripts/Start.py
```

## 项目结构

```
xianyu-auto-reply-main/
├── configs/              # 配置文件
│   ├── .env              # 环境变量
│   ├── .env.example      # 配置模板
│   └── config.py         # 配置类
├── deploy/               # 部署文件
├── docs/                 # 文档
├── logs/                 # 日志
├── scripts/              # 脚本
│   └── Start.py          # 启动入口
├── static/               # 前端资源
│   ├── css/              # 样式
│   ├── js/               # JavaScript
│   └── *.html            # 页面
├── utils/                # 工具函数
│   ├── xianyu_utils.py   # 闲鱼 API
│   ├── message_utils.py  # 消息处理
│   └── ...
├── XianyuAutoAsync.py    # WebSocket 核心
├── ai_reply_engine.py    # AI 回复
├── cookie_manager.py     # Cookie 管理
├── db_manager.py         # 数据库
├── reply_server.py       # Web 服务
└── requirements.txt      # 依赖列表
```

## 开发流程

### 1. 创建功能分支

```bash
git checkout -b feature/your-feature
```

### 2. 编写代码

遵循 [编码规范](../team/conventions.md)

### 3. 编写测试

```python
# tests/test_example.py
import pytest
from module import function

def test_function():
    result = function(input)
    assert result == expected
```

### 4. 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_example.py

# 带覆盖率
pytest --cov=. --cov-report=html
```

### 5. 代码检查

```bash
# 类型检查
mypy .

# 代码风格
flake8 .

# 自动格式化
black .
isort .
```

### 6. 提交代码

```bash
git add .
git commit -m "feat: 添加新功能"
git push origin feature/your-feature
```

## 核心模块开发

### 添加新的 API 端点

```python
# reply_server.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/api/your-module", tags=["Your Module"])

class YourRequest(BaseModel):
    field: str

class YourResponse(BaseModel):
    result: str

@router.post("/action", response_model=YourResponse)
async def your_action(
    request: YourRequest,
    user = Depends(get_current_user)
):
    # 业务逻辑
    return YourResponse(result="success")
```

### 添加新的消息处理器

```python
# 在 XianyuAutoAsync.py 中

async def _handle_your_message_type(self, message: dict):
    """处理特定类型消息"""
    # 1. 解析消息
    content = message.get("content")
    
    # 2. 业务处理
    result = await self._process(content)
    
    # 3. 发送回复
    await self._send_reply(result)
```

### 添加新的数据库表

```python
# db_manager.py

def _create_your_table(self):
    """创建新表"""
    self.execute("""
        CREATE TABLE IF NOT EXISTS your_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
```

## 调试技巧

### 日志调试

```python
from loguru import logger

# 添加调试日志
logger.debug("变量值: {}", variable)

# 条件日志
logger.bind(cookie_id=cookie_id).info("处理消息")
```

### 断点调试

```python
# 添加断点
import pdb; pdb.set_trace()

# 或使用 ipdb
import ipdb; ipdb.set_trace()
```

### WebSocket 调试

```python
# 打印原始消息
logger.debug("收到消息: {}", json.dumps(message, ensure_ascii=False))
```

## 常见问题

### Playwright 安装失败

```bash
# 手动安装
playwright install chromium --with-deps
```

### 数据库锁定

```python
# 使用上下文管理器
with db_manager.transaction():
    db_manager.execute(...)
```

### 内存泄漏

```python
# 确保关闭连接
async with websockets.connect(url) as ws:
    # 使用连接
    pass
# 自动关闭
```

## 相关文档

- [编码规范](../team/conventions.md)
- [架构概览](../architecture/overview.md)
- [API 参考](../reference/api.md)

---

**维护者：** Doc Keeper Agent  
**最后更新：** 2026-03-25
