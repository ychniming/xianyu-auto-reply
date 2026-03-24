# 前端代码三阶段重构 Spec

## Why

当前前端代码存在严重的可维护性和可扩展性问题：
- 200+个函数暴露到 `window` 全局命名空间，导致高冲突风险
- `keywords.js` 单文件超过1500行，违反单一职责原则
- `index.html` 超过2300行，DOM结构混乱
- API端点硬编码，无法配置版本和拦截器
- 缺少状态管理，模块间通过全局变量通信
- 没有测试覆盖，重构风险高

需要分三个阶段渐进式重构，逐步提升代码质量。

## What Changes

### 阶段1：清理和稳定（P0 - 立即实施）
- 统一API调用入口，移除各模块直接fetch调用
- 抽取公共函数（escapeHtml等），消除重复代码
- 规范化 `window.*` 暴露模式，改用 `App.*` 命名空间

### 阶段2：架构优化（P1 - 2-4周）
- 将 `index.html` 中的Modal HTML分离到JS动态创建
- 拆分 `keywords.js` 中过长的函数（>50行）
- 添加请求取消机制（AbortController）
- 实现简单的状态管理模式

### 阶段3：质量提升（P2 - 持续）
- 抽取CSS变量，统一组件样式
- 添加基础单元测试
- API端点配置化

### **BREAKING** 变更
- 阶段1会改变 `window.showSection` 等函数的调用方式
- 阶段2会改变Modal的创建方式

## Impact

- Affected specs: 前端所有模块
- Affected code:
  - `static/js/app.js` (修改) - 移除直接window暴露
  - `static/js/modules/api.js` (修改) - 统一API入口
  - `static/js/modules/utils.js` (修改) - 抽取公共函数
  - `static/js/modules/keywords.js` (修改) - 拆分过长函数
  - `static/index.html` (修改) - Modal动态创建
  - `static/js/modules/cards.js` (修改)
  - `static/js/modules/delivery.js` (修改)
  - `static/js/modules/notifications.js` (修改)

## ADDED Requirements

### Requirement: 统一API调用入口（阶段1 - 立即实施）

所有模块必须通过 `API.*` 命名空间调用接口，禁止直接使用fetch。

#### Scenario: API模块统一
- **WHEN** 需要调用后端API
- **THEN** 必须使用 `API.fetchJSON()` 或 `API.loadCookies()` 等封装方法

#### Scenario: 直接fetch调用
- **WHEN** 发现模块中使用 `fetch()` 直接调用API
- **THEN** 必须重构为使用 `API.fetchJSON()` 封装

### Requirement: 公共函数抽取（阶段1 - 立即实施）

消除重复实现的 `escapeHtml` 函数。

#### Scenario: escapeHtml统一
- **WHEN** 任何模块需要HTML转义
- **THEN** 必须使用 `Utils.escapeHtml()` 而非自己实现

#### Scenario: 重复实现检测
- **WHEN** 代码审查发现重复函数实现
- **THEN** 必须抽取到 `utils.js` 并在原位置引用

### Requirement: 命名空间规范化（阶段1 - 立即实施）

规范化全局函数暴露，避免命名冲突。

#### Scenario: window暴露清理
- **WHEN** `app.js` 中使用 `window.funcName = function`
- **THEN** 改为 `App.ModuleName.funcName` 方式挂载

#### Scenario: 函数调用方式
- **WHEN** HTML onclick 调用全局函数
- **THEN** 保持 `onclick="showSection('dashboard')"` 方式，但函数定义在App命名空间

### Requirement: Modal动态创建（阶段2 - 短期实施）

将 `index.html` 中散落的Modal HTML分离到JS模块动态创建。

#### Scenario: Modal HTML移除
- **WHEN** 重构完成
- **THEN** `index.html` 不包含任何 `<div class="modal">` 元素

#### Scenario: Modal模块化
- **WHEN** 需要显示Modal
- **THEN** 调用如 `ModalService.show('qrCodeLogin')` 方法

### Requirement: 函数长度限制（阶段2 - 短期实施）

拆分超过50行的函数，遵循单一职责原则。

#### Scenario: renderKeywordsList拆分
- **WHEN** `renderKeywordsList` 函数超过50行
- **THEN** 拆分为 `renderKeywordItem()`, `renderKeywordBadges()`, `renderKeywordContent()` 等

#### Scenario: addKeyword拆分
- **WHEN** `addKeyword` 函数超过50行
- **THEN** 拆分为 `validateKeywordInput()`, `buildKeywordData()`, `saveKeyword()` 等

### Requirement: 请求取消机制（阶段2 - 短期实施）

添加 AbortController 支持，避免快速切换时的竞态条件。

#### Scenario: 请求取消
- **WHEN** 用户快速切换账号
- **THEN** 旧请求被取消，新请求生效

#### Scenario: AbortController集成
- **WHEN** `API.fetchJSON` 被调用
- **THEN** 支持传入 `signal` 参数用于取消请求

### Requirement: 状态管理模式（阶段2 - 短期实施）

引入简单的Store模式，集中管理应用状态。

#### Scenario: 全局状态集中
- **WHEN** 需要共享状态
- **THEN** 使用 `App.Store.get('keywordsData')` 而非全局变量

#### Scenario: 状态更新通知
- **WHEN** 状态发生变更
- **THEN** Store通知所有订阅者更新UI

### Requirement: CSS架构优化（阶段3 - 中期实施）

统一CSS变量使用，建立组件抽象层。

#### Scenario: CSS变量统一
- **WHEN** 需要使用主题色
- **THEN** 使用 `var(--primary-color)` 而非硬编码 `#4f46e5`

#### Scenario: 组件样式复用
- **WHEN** 需要创建类似按钮样式
- **THEN** 使用 `.btn-primary` 而非重复样式定义

### Requirement: 单元测试覆盖（阶段3 - 中期实施）

添加基础单元测试，确保重构质量。

#### Scenario: 工具函数测试
- **WHEN** `Utils.escapeHtml` 被修改
- **THEN** 必须通过单元测试验证

#### Scenario: API模块测试
- **WHEN** `API.fetchJSON` 被修改
- **THEN** 必须通过单元测试验证

## MODIFIED Requirements

### Requirement: app.js 导出方式

原有方式：
```javascript
window.showSection = function(sectionName) { ... }
window.loadCookies = Cookies.loadCookies;
```

修改后方式：
```javascript
window.App = {
    Utils,
    API,
    Auth,
    // ... 其他模块
    showSection: function(sectionName) { ... }
};

// window 仍然暴露必要的全局函数供HTML onclick使用
window.showSection = App.showSection;
```

## REMOVED Requirements

### Requirement: 直接fetch调用
**Reason**: 分散的fetch调用无法统一管理API版本、拦截器、错误处理
**Migration**: 统一通过 `API.*` 模块调用

### Requirement: 重复的escapeHtml实现
**Reason**: 违反DRY原则，维护困难
**Migration**: 统一使用 `Utils.escapeHtml()`

## Implementation Phases

### 阶段1：清理和稳定（P0 - 立即实施）
**目标：统一API入口，消除重复代码**

1. 审查所有模块的fetch调用点
2. 确保所有API调用通过 `API.fetchJSON()` 封装
3. 抽取 `keywords.js`, `dashboard.js` 中的 `escapeHtml` 到 `utils.js`
4. 规范化 `app.js` 中的 `window.*` 暴露模式
5. 验证功能完整性

### 阶段2：架构优化（P1 - 2-4周）
**目标：改善代码结构，降低维护成本**

1. 提取 `index.html` 中的Modal HTML到独立JS文件
2. 实现 `ModalService` 动态创建模态框
3. 拆分 `keywords.js` 中过长的函数
4. 添加 `AbortController` 支持
5. 实现简单的 `App.Store` 状态管理
6. 重构 `cards.js`, `delivery.js` 等模块
7. 验证功能完整性

### 阶段3：质量提升（P2 - 持续）
**目标**: 提升代码质量和可测试性

1. 统一CSS变量使用
2. 添加Jest/Vitest单元测试框架
3. 为工具函数编写单元测试
4. 添加API模块集成测试
5. 建立CI/CD测试流程

## Performance Requirements

| 指标 | 目标值 |
|------|--------|
| 首屏加载时间 | <2s |
| 模块懒加载 | 支持 |
| API请求重试 | 3次自动重试 |
| 请求取消 | <50ms响应 |

## Compatibility Requirements

| 需求 | 说明 |
|------|------|
| HTML onclick兼容 | `onclick="showSection('xxx')"` 必须继续工作 |
| 浏览器兼容 | Chrome 80+, Firefox 75+, Safari 13+ |
| 渐进增强 | 基础功能在旧浏览器可用 |
