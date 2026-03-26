---
title: API 参考
description: 闲鱼自动回复系统的 RESTful API 接口文档
lastUpdated: 2026-03-25
maintainer: Doc Keeper Agent
---

# API 参考

[返回索引](../INDEX.md)

## 基础信息

- **Base URL**: `http://your-domain:8080`
- **认证方式**: JWT Bearer Token
- **内容类型**: `application/json`

## 认证接口

### 登录

```
POST /api/auth/login
```

**请求体：**
```json
{
  "username": "admin",
  "password": "password123"
}
```

**响应：**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin"
  }
}
```

### 获取当前用户

```
GET /api/auth/me
Authorization: Bearer <token>
```

**响应：**
```json
{
  "id": 1,
  "username": "admin",
  "role": "admin",
  "created_at": "2024-01-01T00:00:00"
}
```

## 账号管理

### 获取账号列表

```
GET /api/accounts
Authorization: Bearer <token>
```

**响应：**
```json
{
  "accounts": [
    {
      "id": "cookie_123",
      "enabled": true,
      "auto_confirm": true,
      "status": "online",
      "created_at": "2024-01-01T00:00:00"
    }
  ]
}
```

### 添加账号

```
POST /api/cookie/add
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "cookieId": "user123",
  "cookieValue": "_m_h5_tk=xxx; _m_h5_tk_enc=xxx; ..."
}
```

**响应：**
```json
{
  "success": true,
  "message": "账号添加成功"
}
```

### 更新账号

```
POST /api/cookie/update
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "cookieId": "user123",
  "cookieValue": "新的Cookie值"
}
```

### 删除账号

```
POST /api/cookie/delete
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "cookieId": "user123"
}
```

### 切换账号状态

```
POST /api/cookie/toggle
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "cookieId": "user123",
  "enabled": false
}
```

## 关键词管理

### 获取关键词列表

```
GET /api/keywords/{cookie_id}
Authorization: Bearer <token>
```

**响应：**
```json
{
  "keywords": [
    {
      "id": 1,
      "keyword": "价格",
      "reply": "商品价格请在商品详情页查看",
      "item_id": null
    }
  ]
}
```

### 保存关键词

```
POST /api/keywords/save
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "cookieId": "user123",
  "keywords": [
    {
      "keyword": "价格",
      "reply": "商品价格请查看详情页"
    }
  ]
}
```

### 删除关键词

```
POST /api/keywords/delete
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "keywordId": 1
}
```

## 发货规则

### 获取发货规则

```
GET /api/delivery/rules/{cookie_id}
Authorization: Bearer <token>
```

**响应：**
```json
{
  "rules": [
    {
      "id": 1,
      "item_keyword": "激活码",
      "delivery_content": "您的激活码：{code}",
      "enabled": true
    }
  ]
}
```

### 保存发货规则

```
POST /api/delivery/rules/save
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "cookieId": "user123",
  "rules": [
    {
      "item_keyword": "激活码",
      "delivery_content": "您的激活码：{code}",
      "enabled": true
    }
  ]
}
```

## 商品管理

### 获取商品列表

```
GET /api/items/{cookie_id}
Authorization: Bearer <token>
```

**响应：**
```json
{
  "items": [
    {
      "item_id": "123456",
      "title": "商品名称",
      "price": 9.9,
      "status": "selling",
      "stock": 100
    }
  ]
}
```

### 更新商品状态

```
POST /api/items/update
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "itemId": "123456",
  "status": "sold_out"
}
```

## 消息管理

### 获取消息历史

```
GET /api/messages/{cookie_id}?page=1&size=20
Authorization: Bearer <token>
```

**响应：**
```json
{
  "messages": [
    {
      "id": 1,
      "from_user": "买家ID",
      "content": "你好",
      "reply": "您好，有什么可以帮您？",
      "created_at": "2024-01-01T12:00:00"
    }
  ],
  "total": 100,
  "page": 1,
  "size": 20
}
```

### 发送消息

```
POST /api/message/send
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "cookieId": "user123",
  "toUser": "买家ID",
  "content": "消息内容"
}
```

## 系统管理

### 健康检查

```
GET /health
```

**响应：**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 86400
}
```

### 获取系统状态

```
GET /api/system/status
Authorization: Bearer <token>
```

**响应：**
```json
{
  "accounts": {
    "total": 5,
    "online": 3,
    "offline": 2
  },
  "messages": {
    "today": 100,
    "replied": 95
  },
  "system": {
    "cpu": 25.5,
    "memory": 60.2,
    "disk": 45.0
  }
}
```

## 错误响应

所有错误响应格式：

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述"
  }
}
```

### 常见错误码

| 错误码 | 说明 |
|--------|------|
| `AUTH_FAILED` | 认证失败 |
| `TOKEN_EXPIRED` | Token 过期 |
| `PERMISSION_DENIED` | 权限不足 |
| `INVALID_PARAM` | 参数错误 |
| `ACCOUNT_NOT_FOUND` | 账号不存在 |
| `COOKIE_EXPIRED` | Cookie 过期 |

## 相关文档

- [配置参考](./config.md)
- [规格文档](./specs/INDEX.md)
- [导入验证报告](./import-validation-report.md)
- [清理日志](./deletion-log.md)
- [部署指南](../guides/deployment.md)
- [开发指南](../guides/development.md)

---

**维护者：** Doc Keeper Agent  
**最后更新：** 2026-03-25
