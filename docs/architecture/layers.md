---
title: 分层设计
description: 系统的分层架构和职责划分
lastUpdated: 2026-03-25
maintainer: Doc Keeper Agent
---

# 分层设计

[返回架构](./overview.md) | [返回索引](../INDEX.md)

## 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│ 第1层：表现层 (Presentation Layer)                          │
│ 职责：用户界面、请求处理、响应格式化                         │
│ 文件：static/*.html, static/js/*.js, reply_server.py       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 第2层：应用层 (Application Layer)                           │
│ 职责：用例编排、事务管理、权限控制                           │
│ 文件：reply_server.py (API路由)                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 第3层：领域层 (Domain Layer)                                │
│ 职责：业务逻辑、领域规则、状态管理                           │
│ 文件：XianyuAutoAsync.py, ai_reply_engine.py,               │
│       cookie_manager.py, secure_*_ultra.py                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 第4层：基础设施层 (Infrastructure Layer)                    │
│ 职责：数据持久化、外部服务、工具函数                         │
│ 文件：db_manager.py, utils/*.py, configs/config.py          │
└─────────────────────────────────────────────────────────────┘
```

## 层次职责

### 第1层：表现层

**职责：**
- 渲染用户界面
- 处理 HTTP 请求
- 格式化响应数据
- 输入验证

**关键文件：**

| 文件 | 职责 |
|------|------|
| `static/index.html` | 主页面 |
| `static/js/app.js` | 前端入口 |
| `static/js/api.js` | API 调用 |
| `static/js/auth.js` | 认证逻辑 |

**设计原则：**
- 不包含业务逻辑
- 只负责展示和交互
- 通过 API 与后端通信

### 第2层：应用层

**职责：**
- 定义 API 路由
- 编排业务用例
- 管理事务边界
- 执行权限检查

**关键文件：**

| 文件 | 职责 |
|------|------|
| `reply_server.py` | FastAPI 应用 |
| API 路由 | 各业务端点 |

**设计原则：**
- 薄层，不包含复杂逻辑
- 协调领域对象完成任务
- 处理异常并返回适当响应

### 第3层：领域层

**职责：**
- 实现核心业务逻辑
- 定义领域规则
- 管理领域状态
- 处理业务事件

**关键文件：**

| 文件 | 职责 |
|------|------|
| `XianyuAutoAsync.py` | WebSocket 消息处理 |
| `ai_reply_engine.py` | AI 回复逻辑 |
| `cookie_manager.py` | 账号管理 |
| `secure_*_ultra.py` | 自动发货 |

**设计原则：**
- 不依赖外部框架
- 可独立测试
- 封装业务规则

### 第4层：基础设施层

**职责：**
- 数据库操作
- 外部服务集成
- 工具函数
- 配置管理

**关键文件：**

| 文件 | 职责 |
|------|------|
| `db_manager.py` | 数据库操作 |
| `utils/xianyu_utils.py` | 闲鱼 API 工具 |
| `utils/ws_utils.py` | WebSocket 工具 |
| `configs/config.py` | 配置管理 |

**设计原则：**
- 为上层提供抽象接口
- 隔离外部依赖
- 可替换实现

## 依赖规则

```
依赖方向：上层依赖下层

表现层 ──依赖──> 应用层 ──依赖──> 领域层 ──依赖──> 基础设施层

禁止：下层依赖上层
允许：同层之间适度依赖
```

## 数据流

### 请求流程

```
1. 表现层接收 HTTP 请求
2. 应用层解析参数、验证权限
3. 领域层执行业务逻辑
4. 基础设施层持久化数据
5. 响应沿层次返回
```

### 示例：发送消息

```
[表现层] 用户点击发送按钮
    │
    ▼
[应用层] POST /api/message/send
    │ 验证 JWT Token
    │ 解析请求参数
    ▼
[领域层] XianyuAutoAsync.send_message()
    │ 检查账号状态
    │ 构建消息内容
    │ 调用发送逻辑
    ▼
[基础设施层] ws_utils.send_ws_message()
    │ WebSocket 连接
    │ 发送数据帧
    ▼
[外部服务] 闲鱼 WebSocket 服务器
```

## 模块边界

### 跨层通信

| 场景 | 方式 |
|------|------|
| 同步调用 | 直接方法调用 |
| 异步事件 | 回调函数 |
| 状态变更 | 状态模式 |

### 层间接口

```python
# 应用层调用领域层示例
@router.post("/message/send")
async def send_message(request: MessageRequest, user: User = Depends(get_current_user)):
    # 应用层：权限检查、参数验证
    if not user.has_permission("message:send"):
        raise HTTPException(403)
    
    # 调用领域层
    result = await xianyu_client.send_message(
        cookie_id=request.cookie_id,
        content=request.content
    )
    
    # 返回响应
    return {"success": result.success}
```

## 相关文档

- [架构概览](./overview.md)
- [领域划分](./domains.md)
- [编码规范](../team/conventions.md)

---

**维护者：** Doc Keeper Agent  
**最后更新：** 2026-03-25
