# Tasks

## Phase 1: Git 备份
- [x] Task 1: 提交当前代码到 GitHub
  - [x] SubTask 1.1: 检查当前 git 状态，确认所有更改
  - [x] SubTask 1.2: 添加所有文件到暂存区
  - [x] SubTask 1.3: 提交更改，commit message 为 "chore: 架构修复前备份"
  - [ ] SubTask 1.4: 推送到 GitHub 远程仓库 (网络问题，稍后重试)
  - [x] SubTask 1.5: 创建备份分支 `backup/pre-architecture-fix`

## Phase 2: 安全性修复 (CRITICAL)

### 2.1 敏感数据加密
- [x] Task 2: 实现敏感数据加密工具
  - [x] SubTask 2.1: 创建 `app/utils/encryption.py` 加密工具模块
  - [x] SubTask 2.2: 实现 AES-256 加密/解密函数
  - [x] SubTask 2.3: 实现密钥管理（从环境变量读取）
  - [ ] SubTask 2.4: 添加加密相关单元测试

- [x] Task 3: 加密存储 API Key
  - [x] SubTask 3.1: 修改 `ai_reply_settings` 表，添加 `api_key_encrypted` 字段
  - [x] SubTask 3.2: 修改 `db_manager.save_ai_reply_settings()` 加密存储
  - [x] SubTask 3.3: 修改 `db_manager.get_ai_reply_settings()` 解密读取
  - [x] SubTask 3.4: 修改 `AIReplyEngine.get_client()` 使用解密后的 Key
  - [x] SubTask 3.5: 数据迁移脚本：加密现有明文 API Key

- [x] Task 4: 加密存储 Cookie
  - [x] SubTask 4.1: 修改 `cookies` 表，添加 `value_encrypted` 字段
  - [x] SubTask 4.2: 修改 `CookieRepository` 加密存储
  - [x] SubTask 4.3: 修改 `CookieManager` 解密读取
  - [x] SubTask 4.4: 数据迁移脚本：加密现有明文 Cookie

### 2.2 全局异常处理
- [x] Task 5: 实现自定义异常体系
  - [x] SubTask 5.1: 创建 `app/core/exceptions.py` 异常模块
  - [x] SubTask 5.2: 定义 `XianyuBaseException` 基类
  - [x] SubTask 5.3: 定义业务异常类（AuthenticationError, ResourceNotFoundError, PermissionDeniedError 等）
  - [x] SubTask 5.4: 定义错误码枚举

- [x] Task 6: 实现全局异常处理器
  - [x] SubTask 6.1: 创建 `app/api/exception_handlers.py`
  - [x] SubTask 6.2: 实现业务异常处理器
  - [x] SubTask 6.3: 实现 Pydantic 验证异常处理器
  - [x] SubTask 6.4: 实现通用异常处理器（过滤敏感信息）
  - [ ] SubTask 6.5: 在 FastAPI 应用中注册异常处理器

### 2.3 权限检查完善
- [x] Task 7: 实现权限装饰器
  - [x] SubTask 7.1: 创建 `app/api/decorators.py` 权限装饰器模块
  - [x] SubTask 7.2: 实现 `@require_owner` 装饰器
  - [x] SubTask 7.3: 实现 `@require_admin` 装饰器
  - [x] SubTask 7.4: 实现 `@check_resource_access` 装饰器

- [x] Task 8: 应用权限检查到路由
  - [x] SubTask 8.1: 审查 `routes/cookies.py` 添加权限检查
  - [x] SubTask 8.2: 审查 `routes/keywords.py` 添加权限检查
  - [x] SubTask 8.3: 审查 `routes/cards.py` 添加权限检查
  - [x] SubTask 8.4: 审查 `routes/items.py` 添加权限检查

### 2.4 Session 黑名单
- [x] Task 9: 实现 Session 黑名单
  - [x] SubTask 9.1: 创建 `token_blacklist` 表
  - [x] SubTask 9.2: 修改 `logout()` 添加 Token 到黑名单
  - [x] SubTask 9.3: 修改 `get_token_data()` 检查黑名单
  - [x] SubTask 9.4: 实现黑名单定期清理

## Phase 3: 代码质量改进 (HIGH)

### 3.1 依赖注入重构
- [x] Task 10: 创建依赖注入容器
  - [x] SubTask 10.1: 创建 `app/core/container.py` 依赖注入容器
  - [x] SubTask 10.2: 定义服务接口
  - [x] SubTask 10.3: 实现服务工厂函数

- [ ] Task 11: 重构数据库管理器
  - [ ] SubTask 11.1: 移除 `db_manager` 全局实例
  - [ ] SubTask 11.2: 创建 `get_db_manager()` 依赖函数
  - [ ] SubTask 11.3: 更新所有路由使用依赖注入

- [ ] Task 12: 重构 Cookie 管理器
  - [ ] SubTask 12.1: 移除 `manager` 全局变量
  - [ ] SubTask 12.2: 创建 `get_cookie_manager()` 依赖函数
  - [ ] SubTask 12.3: 更新所有使用处

- [ ] Task 13: 重构 AI 回复引擎
  - [ ] SubTask 13.1: 移除 `ai_reply_engine` 全局实例
  - [ ] SubTask 13.2: 创建 `get_ai_reply_engine()` 依赖函数
  - [ ] SubTask 13.3: 更新所有使用处

### 3.2 循环导入修复
- [ ] Task 14: 修复 xianyu_message_handler.py 循环导入
  - [ ] SubTask 14.1: 分析循环依赖链
  - [ ] SubTask 14.2: 重构 `MessageHandler` 使用依赖注入
  - [ ] SubTask 14.3: 移除 `from src import cookie_manager` 运行时导入

### 3.3 RESTful API 规范
- [x] Task 15: 修复路由 HTTP 方法
  - [x] SubTask 15.1: 修改 `routes/items.py` 搜索接口为 GET
  - [x] SubTask 15.2: 修改 `routes/items.py` 多页搜索为 GET
  - [x] SubTask 15.3: 审查其他路由，确保 HTTP 方法正确

- [ ] Task 16: 统一路由前缀
  - [ ] SubTask 16.1: 为所有路由添加 `/api/v1` 前缀
  - [ ] SubTask 16.2: 更新前端 API 调用路径
  - [ ] SubTask 16.3: 添加 API 版本兼容层

- [ ] Task 17: 修复 HTTP 状态码
  - [ ] SubTask 17.1: 修改 `routes/auth.py` 使用正确的 HTTP 状态码
  - [ ] SubTask 17.2: 审查所有路由，确保状态码正确

### 3.4 事务管理
- [x] Task 18: 实现事务管理器
  - [x] SubTask 18.1: 创建 `app/repositories/transaction.py` 事务管理模块
  - [x] SubTask 18.2: 实现上下文管理器 `with_transaction()`
  - [x] SubTask 18.3: 实现事务装饰器 `@transactional`

- [x] Task 19: 应用事务到关键操作
  - [x] SubTask 19.1: 修改 `import_backup()` 使用事务
  - [x] SubTask 19.2: 修改批量操作使用事务
  - [x] SubTask 19.3: 修改关联数据更新使用事务

### 3.5 类型注解完善
- [ ] Task 20: 添加类型注解
  - [ ] SubTask 20.1: 为 `CookieManager` 所有方法添加返回类型
  - [ ] SubTask 20.2: 为 `DBManager` 所有方法添加返回类型
  - [ ] SubTask 20.3: 为 `AIReplyEngine` 所有方法添加返回类型
  - [ ] SubTask 20.4: 运行 mypy 检查并修复错误

## Phase 4: 性能优化 (MEDIUM)

### 4.1 N+1 查询修复
- [x] Task 21: 实现批量查询方法
  - [x] SubTask 21.1: 在 `ItemRepository` 添加 `get_items_by_cookie_ids()` 方法
  - [x] SubTask 21.2: 修改 `routes/items.py` 使用批量查询

### 4.2 缓存优化
- [x] Task 22: 修复 AI 客户端缓存
  - [x] SubTask 22.1: 为 `AIReplyEngine.clients` 添加 LRU 缓存限制
  - [x] SubTask 22.2: 实现定期清理过期客户端

- [ ] Task 23: 实现规则引擎缓存
  - [ ] SubTask 23.1: 实现 `RuleEngine._rule_cache` 缓存逻辑
  - [ ] SubTask 23.2: 添加缓存命中率统计

## Phase 5: 测试与验证

### 5.1 单元测试
- [ ] Task 24: 编写单元测试
  - [ ] SubTask 24.1: 加密工具单元测试
  - [ ] SubTask 24.2: 异常处理器单元测试
  - [ ] SubTask 24.3: 权限装饰器单元测试
  - [ ] SubTask 24.4: 事务管理器单元测试

### 5.2 集成测试
- [ ] Task 25: 编写集成测试
  - [ ] SubTask 25.1: API 接口集成测试
  - [ ] SubTask 25.2: 权限检查集成测试
  - [ ] SubTask 25.3: 事务集成测试

### 5.3 安全测试
- [ ] Task 26: 安全测试
  - [ ] SubTask 26.1: SQL 注入测试
  - [ ] SubTask 26.2: 权限绕过测试
  - [ ] SubTask 26.3: 敏感数据泄露测试

## Phase 6: 最终提交与复查

- [ ] Task 27: 代码审查
  - [ ] SubTask 27.1: 检查所有修改是否符合规范
  - [ ] SubTask 27.2: 检查是否有遗漏的问题
  - [ ] SubTask 27.3: 检查测试覆盖率

- [ ] Task 28: 提交修复结果
  - [ ] SubTask 28.1: 检查所有更改
  - [ ] SubTask 28.2: 提交更改，commit message 为 "fix: 后端架构问题修复"
  - [ ] SubTask 28.3: 推送到 GitHub 远程仓库

# Task Dependencies

- [Task 2] depends on [Task 1] (需要先备份)
- [Task 3] depends on [Task 2] (需要加密工具)
- [Task 4] depends on [Task 2] (需要加密工具)
- [Task 5] depends on [Task 1] (需要先备份)
- [Task 6] depends on [Task 5] (需要异常类)
- [Task 7] depends on [Task 5] (需要异常类)
- [Task 8] depends on [Task 7] (需要装饰器)
- [Task 9] depends on [Task 1] (需要先备份)
- [Task 10] depends on [Task 1] (需要先备份)
- [Task 11] depends on [Task 10] (需要容器)
- [Task 12] depends on [Task 10] (需要容器)
- [Task 13] depends on [Task 10] (需要容器)
- [Task 14] depends on [Task 11, Task 12] (需要依赖注入)
- [Task 15] depends on [Task 1] (需要先备份)
- [Task 16] depends on [Task 15] (需要路由修复)
- [Task 17] depends on [Task 15] (需要路由修复)
- [Task 18] depends on [Task 1] (需要先备份)
- [Task 19] depends on [Task 18] (需要事务管理器)
- [Task 20] depends on [Task 1] (需要先备份)
- [Task 21] depends on [Task 1] (需要先备份)
- [Task 22] depends on [Task 13] (需要 AI 引擎重构)
- [Task 23] depends on [Task 1] (需要先备份)
- [Task 24] depends on [Task 2-23] (需要所有修复完成)
- [Task 25] depends on [Task 24] (需要单元测试)
- [Task 26] depends on [Task 24] (需要单元测试)
- [Task 27] depends on [Task 24, Task 25, Task 26] (需要所有测试)
- [Task 28] depends on [Task 27] (需要审查通过)

# Parallelizable Tasks

以下任务可以并行执行：
- Task 2, Task 5, Task 7, Task 9, Task 10, Task 15, Task 18, Task 20, Task 21, Task 23 (都依赖 Task 1)
- Task 3, Task 4 (都依赖 Task 2)
- Task 11, Task 12, Task 13 (都依赖 Task 10)
- Task 24, Task 25, Task 26 (测试任务可并行)
