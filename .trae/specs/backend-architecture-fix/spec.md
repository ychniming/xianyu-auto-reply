# 后端架构修复与改进 Spec

## Why

根据架构评估报告，发现 27 个问题，其中 2 个 CRITICAL、9 个 HIGH、13 个 MEDIUM、3 个 LOW。这些问题涉及安全性、代码质量、性能和可维护性，需要系统性修复以确保系统稳定、安全和可扩展。

## What Changes

### Phase 1: Git 备份 (CRITICAL)
- 提交当前代码到 GitHub 作为备份点
- 创建备份分支以便回滚

### Phase 2: 安全性修复 (CRITICAL/HIGH)
- **BREAKING**: API Key 和 Cookie 加密存储
- 实现全局异常处理器
- 完善权限检查机制
- 实现 Session 黑名单

### Phase 3: 代码质量改进 (HIGH/MEDIUM)
- 消除全局单例，使用依赖注入
- 修复循环导入问题
- 统一 RESTful API 规范
- 添加事务管理
- 完善类型注解

### Phase 4: 性能优化 (MEDIUM)
- 修复 N+1 查询问题
- 实现 AI 客户端缓存清理
- 修复规则引擎缓存

### Phase 5: 验证与测试
- 全面复查所有修复
- 运行测试套件
- 提交最终代码到 GitHub

## Impact

- Affected specs: 安全认证、API 设计、数据访问层
- Affected code: 
  - `app/api/` - 路由和中间件
  - `app/core/` - 核心服务
  - `app/repositories/` - 数据访问层
  - `app/utils/` - 工具函数

## ADDED Requirements

### Requirement: 敏感数据加密存储

系统 SHALL 对以下敏感数据进行加密存储：
- AI API Key
- 闲鱼 Cookie 值
- 其他第三方密钥

#### Scenario: 加密存储 API Key
- **WHEN** 用户保存 AI 回复设置
- **THEN** API Key 使用 AES-256 加密后存储到数据库

#### Scenario: 解密读取 API Key
- **WHEN** 系统需要使用 API Key
- **THEN** 从数据库读取加密数据并解密后使用

### Requirement: 全局异常处理

系统 SHALL 提供统一的异常处理机制：
- 自定义业务异常层次结构
- 全局异常处理器
- 统一错误响应格式
- 敏感信息过滤

#### Scenario: 业务异常处理
- **WHEN** 发生业务异常（如资源不存在）
- **THEN** 返回统一格式的错误响应，不暴露堆栈信息

#### Scenario: 未知异常处理
- **WHEN** 发生未预期的异常
- **THEN** 记录详细日志，返回通用错误信息

### Requirement: 依赖注入重构

系统 SHALL 使用 FastAPI 依赖注入管理实例生命周期：
- 消除全局单例
- 支持测试隔离
- 明确依赖关系

#### Scenario: 服务实例注入
- **WHEN** 路由需要访问数据库或服务
- **THEN** 通过依赖注入获取实例，而非全局变量

### Requirement: RESTful API 规范

系统 SHALL 遵循 RESTful API 设计规范：
- 使用正确的 HTTP 方法（GET 查询，POST 创建，PUT 更新，DELETE 删除）
- 统一路由前缀 `/api/v1/`
- 正确的 HTTP 状态码

#### Scenario: 查询操作
- **WHEN** 客户端请求查询商品
- **THEN** 使用 GET 方法，参数通过 query string 传递

### Requirement: 事务管理

系统 SHALL 为关键操作提供事务支持：
- 备份导入导出
- 批量操作
- 关联数据更新

#### Scenario: 备份导入事务
- **WHEN** 用户导入备份数据
- **THEN** 所有操作在一个事务中执行，失败时回滚

### Requirement: 权限检查完善

系统 SHALL 强制执行权限检查：
- 资源所有权验证
- 管理员权限验证
- 操作权限装饰器

#### Scenario: 资源访问控制
- **WHEN** 用户访问非自己的资源
- **THEN** 系统拒绝访问并返回 403 错误

### Requirement: 循环导入修复

系统 SHALL 消除循环导入问题：
- 使用依赖注入替代运行时导入
- 重构模块依赖关系
- 延迟导入改为显式依赖

#### Scenario: 模块导入
- **WHEN** 系统启动加载模块
- **THEN** 所有模块正常导入，无循环依赖错误

### Requirement: N+1 查询修复

系统 SHALL 优化数据库查询：
- 实现批量查询方法
- 使用 JOIN 减少数据库往返
- 添加查询缓存

#### Scenario: 批量获取商品
- **WHEN** 获取用户所有商品
- **THEN** 使用单次查询获取所有数据

### Requirement: 类型注解完善

系统 SHALL 为所有公共 API 添加类型注解：
- 函数参数类型
- 返回值类型
- 使用 mypy 验证

#### Scenario: 类型检查
- **WHEN** 运行 mypy 类型检查
- **THEN** 无类型错误

## MODIFIED Requirements

### Requirement: 数据库连接管理

原有单连接模式 SHALL 改为连接池模式，提升并发性能。

### Requirement: 错误响应格式

原有 HTTP 200 + 业务码模式 SHALL 改为 HTTP 状态码 + 业务码模式，保持一致性。

### Requirement: Session 管理

原有简单 Token 模式 SHALL 添加黑名单机制，支持主动失效。

## REMOVED Requirements

### Requirement: 全局单例模式

**Reason**: 违反依赖注入原则，导致测试困难和状态管理混乱
**Migration**: 使用 FastAPI 依赖注入系统替代

### Requirement: 运行时导入

**Reason**: 导致循环依赖和难以追踪的 bug
**Migration**: 使用显式依赖注入
