# 前端代码重构规范

## Why
当前前端代码存在严重的可维护性和可扩展性问题：全局命名空间污染、函数过长、重复代码、缺少架构抽象。根据代码审查评分（2.3/5），需要进行系统性重构以提升代码质量。

## What Changes

### Phase 1: 清理和稳定 (1-2周)
- [P0] 移除 `window.*` 全局函数暴露，改用 `App.*` 命名空间
- [P0] 抽取重复的 `escapeHtml` 到 `utils.js`
- [P0] 统一API调用入口 `api.js`，避免各模块直接使用fetch
- [P1] 抽取重复的表单验证逻辑到 `utils.js`
- [P1] 统一错误处理机制

### Phase 2: 架构优化 (2-4周)
- [P1] 将 `index.html` 中的Modal HTML分离到JS动态创建
- [P1] 拆分 `keywords.js` 中过长的函数（>50行拆分为小函数）
- [P1] 添加请求取消机制 (AbortController)
- [P2] 实现简单的状态管理 (Store模式)
- [P2] 抽取CSS变量，统一组件样式
- [P2] API端点配置化

### Phase 3: 质量提升 (持续)
- [P2] 添加基础单元测试
- [P2] 性能优化：减少重复API调用
- [P2] 添加API Mock
- [P3] E2E测试框架搭建

## Impact
- Affected specs: 前端JavaScript模块、CSS架构、HTML结构
- Affected code:
  - `static/js/app.js` (345行 → 重构)
  - `static/js/modules/api.js` (857行 → 重构)
  - `static/js/modules/keywords.js` (1518行 → 拆分)
  - `static/js/modules/utils.js` (73行 → 扩展)
  - `static/index.html` (2392行 → 分离Modal)
  - `static/css/*.css` (统一架构)

---

## ADDED Requirements

### Requirement: 全局命名空间清理
系统 SHALL 移除所有直接暴露到 `window` 对象的函数，改用统一的命名空间 `App.*` 访问。

#### Scenario: 函数调用重构
- **WHEN** 前端代码调用 `showSection('dashboard')`
- **THEN** 应改为 `App.showSection('dashboard')`
- **AND** 所有 `window.showSection = function()` 改为 `App.showSection = function()`

### Requirement: 统一API入口
系统 SHALL 提供统一的API调用层，所有模块必须通过 `API.*` 方法发起请求，禁止直接使用 `fetch`。

#### Scenario: 统一API调用
- **WHEN** 模块需要获取Cookie列表
- **THEN** 必须调用 `API.cookies.list()` 而非直接 `fetch(apiBase + '/cookies/details')`

### Requirement: 公共函数抽取
系统 SHALL 在 `utils.js` 中维护所有公共函数，各模块不得重复实现相同功能。

#### Scenario: escapeHtml 统一使用
- **WHEN** 任何模块需要HTML转义
- **THEN** 必须导入并使用 `utils.escapeHtml()`
- **AND** 移除所有模块中的重复实现

---

## MODIFIED Requirements

### Requirement: API模块重构
现有API函数散布在各个业务模块中，缺乏统一管理。

**Modified**: 创建 `API` 命名空间对象，统一管理所有API端点和调用逻辑。

---

## REMOVED Requirements

### Requirement: 直接Fetch调用
各模块直接使用 `fetch()` 调用API的方式被移除。

**Reason**: 导致代码重复、难以添加拦截器、无法统一错误处理
**Migration**: 所有API调用必须通过 `API.*` 封装

---

## 技术债务清单

| ID | 问题 | 优先级 | 估计工时 |
|----|------|--------|----------|
| T1 | window.* 全局污染 | P0 | 4h |
| T2 | escapeHtml 重复实现 (3处) | P0 | 1h |
| T3 | API调用不统一 | P0 | 8h |
| T4 | index.html Modal内联 | P1 | 6h |
| T5 | keywords.js 函数过长 | P1 | 8h |
| T6 | 缺少请求取消机制 | P1 | 2h |
| T7 | 状态管理缺失 | P2 | 12h |
| T8 | CSS架构混乱 | P2 | 6h |
| T9 | 单元测试缺失 | P2 | 16h |
| T10 | 性能优化 | P2 | 8h |

**总计**: ~71小时 (约2-3周)
