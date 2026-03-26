---
title: 配置参考
description: 闲鱼自动回复系统的配置项说明
lastUpdated: 2026-03-25
maintainer: Doc Keeper Agent
---

# 配置参考

[返回索引](../INDEX.md)

## 环境变量配置

配置文件位置：`configs/.env`

### 安全配置

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `JWT_SECRET_KEY` | ✅ | - | JWT 签名密钥，至少 32 字符 |
| `INITIAL_ADMIN_PASSWORD` | ✅ | - | 初始管理员密码 |

### OpenAI 配置

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `OPENAI_API_KEY` | ⚠️ | - | OpenAI API Key（AI 回复功能必需） |
| `OPENAI_BASE_URL` | ❌ | `https://api.openai.com/v1` | API 基础 URL |
| `OPENAI_MODEL` | ❌ | `gpt-3.5-turbo` | 使用的模型 |

### 服务器配置

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `HOST` | ❌ | `0.0.0.0` | 监听地址 |
| `PORT` | ❌ | `8080` | 监听端口 |
| `DEBUG` | ❌ | `false` | 调试模式 |

### 数据库配置

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `DATABASE_URL` | ❌ | `sqlite:///data/xianyu_data.db` | 数据库连接 URL |

### 日志配置

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `LOG_LEVEL` | ❌ | `INFO` | 日志级别 |
| `LOG_DIR` | ❌ | `logs` | 日志目录 |

## 配置类说明

配置文件位置：`configs/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 安全配置
    JWT_SECRET_KEY: str
    INITIAL_ADMIN_PASSWORD: str
    
    # OpenAI 配置
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    DEBUG: bool = False
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///data/xianyu_data.db"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    
    class Config:
        env_file = "configs/.env"
        env_file_encoding = "utf-8"

config = Settings()
```

## 功能配置

### 自动回复配置

```python
# 自动回复开关
AUTO_REPLY_ENABLED = True

# 回复延迟范围（秒）
REPLY_DELAY_MIN = 1
REPLY_DELAY_MAX = 5

# AI 回复开关
AI_REPLY_ENABLED = True

# AI 回复概率（0-1）
AI_REPLY_PROBABILITY = 0.3
```

### 自动发货配置

```python
# 自动发货开关
AUTO_DELIVERY_ENABLED = True

# 发货延迟范围（秒）
DELIVERY_DELAY_MIN = 5
DELIVERY_DELAY_MAX = 30

# 发货失败重试次数
DELIVERY_RETRY_COUNT = 3
```

### WebSocket 配置

```python
# WebSocket 重连间隔（秒）
WS_RECONNECT_INTERVAL = 5

# 心跳间隔（秒）
WS_HEARTBEAT_INTERVAL = 30

# 连接超时（秒）
WS_CONNECTION_TIMEOUT = 60
```

### 限流配置

```python
# 全局限流（请求/分钟）
RATE_LIMIT_GLOBAL = 100

# 登录限流（请求/分钟）
RATE_LIMIT_LOGIN = 5

# API 限流（请求/分钟）
RATE_LIMIT_API = 60
```

## 数据库配置

### SQLite 配置（默认）

```python
DATABASE_URL = "sqlite:///data/xianyu_data.db"

# 连接池配置（SQLite 不适用）
# DATABASE_POOL_SIZE = 5
# DATABASE_MAX_OVERFLOW = 10
```

### PostgreSQL 配置（可选）

```python
DATABASE_URL = "postgresql://user:password@localhost:5432/xianyu"

# 连接池配置
DATABASE_POOL_SIZE = 5
DATABASE_MAX_OVERFLOW = 10
DATABASE_POOL_TIMEOUT = 30
```

## Docker 配置

### docker-compose.yml

```yaml
version: '3.8'

services:
  xianyu-auto-reply:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - INITIAL_ADMIN_PASSWORD=${INITIAL_ADMIN_PASSWORD}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Nginx 配置

### 反向代理

```nginx
upstream xianyu_backend {
    server 127.0.0.1:8080;
}

server {
    listen 80;
    server_name your-domain.com;
    
    client_max_body_size 10M;
    
    location / {
        proxy_pass http://xianyu_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location /ws {
        proxy_pass http://xianyu_backend/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
```

## 配置验证

### 检查配置

```bash
# 验证环境变量
python -c "from config import config; print(config.model_dump())"

# 检查必需配置
python -c "from config import config; assert config.JWT_SECRET_KEY"
```

### 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| JWT 验证失败 | 密钥不匹配 | 检查 JWT_SECRET_KEY |
| 数据库连接失败 | 路径错误 | 检查 DATABASE_URL |
| AI 回复无响应 | API Key 无效 | 检查 OPENAI_API_KEY |

## 相关文档

- [API 参考](./api.md)
- [部署指南](../guides/deployment.md)
- [运维指南](../guides/operations.md)

---

**维护者：** Doc Keeper Agent  
**最后更新：** 2026-03-25
