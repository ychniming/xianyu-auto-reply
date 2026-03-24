# 前端重构任务清单

## Phase 1: 清理和稳定 (1-2周)

### 1.1 全局命名空间清理
- [x] Task 1.1.1: 创建 `App` 命名空间对象，迁移 `app.js` 中的核心函数
  - [x] 定义 `window.App = {}` 作为主命名空间
  - [x] 迁移 `showSection`, `toggleSidebar`, `showToast` 等核心函数
  - [x] 更新 `index.html` 中的所有 `window.*` 调用为 `App.*`
  - [x] 验证所有功能正常工作

- [x] Task 1.1.2: 清理各模块中的 `window.*` 暴露
  - [x] 检查 `cookies.js`, `keywords.js`, `dashboard.js` 等模块
  - [x] 将 `window.showToast`, `window.showLoading` 等改为模块内部调用
  - [x] 验证模块加载正常

### 1.2 公共函数抽取
- [x] Task 1.2.1: 统一 `escapeHtml` 实现到 `utils.js`
  - [x] 在 `utils.js` 中实现完整的 `escapeHtml` 函数
  - [x] 从 `keywords.js`, `dashboard.js` 中移除重复实现
  - [x] 更新所有导入路径
  - [x] 测试HTML转义功能正常

- [x] Task 1.2.2: 抽取其他公共函数
  - [x] 检查并抽取重复的 `formatDate`, `validateForm` 等函数
  - [x] 统一 `showToast`, `showLoading` 调用方式
  - [x] 更新文档

### 1.3 统一API调用入口
- [x] Task 1.3.1: 重构 `api.js` 结构
  - [x] 创建 `API` 命名空间
  - [x] 定义 `API.cookies`, `API.keywords`, `API.items` 等端点组
  - [x] 实现统一的请求拦截器 (添加Authorization header)
  - [x] 实现统一的错误处理

- [x] Task 1.3.2: 迁移各模块API调用
  - [x] 从 `cookies.js` 迁移到 `API.cookies.*`
  - [x] 从 `keywords.js` 迁移到 `API.keywords.*`
  - [x] 从 `items.js` 迁移到 `API.items.*`
  - [x] 从 `dashboard.js` 迁移到 `API.dashboard.*`
  - [x] 从 `ai.js` 迁移到 `API.ai.*`
  - [x] 从 `delivery.js` 迁移到 `API.delivery.*`
  - [x] 移除各模块中的直接 `fetch` 调用
  - [x] 验证所有API功能正常

- [x] Task 1.3.3: 添加请求取消机制
  - [x] 实现 `API.abortController` 管理
  - [x] 在 `api.js` 中提供 `API.cancelPending()` 方法
  - [x] 在页面切换时自动取消 pending 请求
  - [x] 测试取消机制正常工作

## Phase 2: 架构优化 (2-4周)

### 2.1 Modal HTML 分离
- [ ] Task 2.1.1: 创建 Modal 动态渲染器
  - [ ] 在 `utils.js` 中实现 `ModalManager` 类
  - [ ] 定义各 Modal 的 HTML 模板
  - [ ] 实现 `ModalManager.show(modalId)` 方法

- [ ] Task 2.1.2: 迁移 QRCode Login Modal
  - [ ] 将 `#qrCodeLoginModal` HTML 从 `index.html` 移出
  - [ ] 实现 `ModalManager.showQRCodeLogin()` 方法
  - [ ] 保留原有功能

- [ ] Task 2.1.3: 迁移其他 Modal
  - [ ] 迁移 `addCardModal`, `editCardModal` 等
  - [ ] 更新 `index.html` 移除内联 Modal HTML
  - [ ] 验证所有 Modal 正常工作

### 2.2 函数拆分重构
- [ ] Task 2.2.1: 拆分 `keywords.js` 中的长函数
  - [ ] 分析 `renderKeywordsList()` 函数 (160+ 行)
  - [ ] 拆分为: `renderKeywordsTable()`, `renderKeywordRow()`, `bindKeywordEvents()`
  - [ ] 分析 `addKeyword()` 函数 (170+ 行)
  - [ ] 拆分为: `showAddKeywordForm()`, `validateKeywordInput()`, `submitKeyword()`
  - [ ] 验证关键词管理功能正常

- [ ] Task 2.2.2: 拆分其他长函数
  - [ ] 检查并拆分 `cookies.js` 中超过50行的函数
  - [ ] 检查并拆分 `items.js` 中超过50行的函数
  - [ ] 验证功能完整性

### 2.3 简单状态管理
- [ ] Task 2.3.1: 实现 Store 模式
  - [ ] 创建 `store.js` 模块
  - [ ] 实现 `Store.create(name, initialState)` 工厂函数
  - [ ] 实现 `getState()`, `setState()`, `subscribe()` 方法

- [ ] Task 2.3.2: 迁移全局状态到 Store
  - [ ] 迁移 `keywordsData`, `currentCookieId` 到 `Store`
  - [ ] 迁移 `dashboardData` 到 `Store`
  - [ ] 迁移 `aiSettings` 到 `Store`
  - [ ] 更新各模块使用 Store 访问状态

### 2.4 CSS 架构优化
- [ ] Task 2.4.1: 审查并统一CSS变量使用
  - [ ] 检查 `variables.css` 中定义的变量
  - [ ] 确保所有CSS文件引用统一变量
  - [ ] 移除硬编码的颜色、间距等值

- [ ] Task 2.4.2: 组件样式抽象
  - [ ] 定义 `.btn-primary`, `.card`, `.modal` 等基础组件样式
  - [ ] 统一各页面的样式引用
  - [ ] 验证视觉一致性

## Phase 3: 质量提升 (持续)

### 3.1 单元测试框架搭建
- [ ] Task 3.1.1: 选择测试框架
  - [ ] 选择 Jest 或 Vitest
  - [ ] 创建 `tests/` 目录结构
  - [ ] 配置测试环境

- [ ] Task 3.1.2: 编写基础单元测试
  - [ ] 测试 `utils.js` 公共函数
  - [ ] 测试 `escapeHtml` 转义逻辑
  - [ ] 测试 `ModalManager` 渲染

- [ ] Task 3.1.3: 编写API层测试
  - [ ] Mock fetch 调用
  - [ ] 测试 `API.cookies.list()` 等方法
  - [ ] 测试错误处理

### 3.2 性能优化
- [ ] Task 3.2.1: 减少重复API调用
  - [ ] 分析 `loadDashboard()` 和 `loadCookies()` 中的重复请求
  - [ ] 实现API响应缓存 (简单内存缓存)
  - [ ] 添加缓存失效机制

- [ ] Task 3.2.2: 优化DOM操作
  - [ ] 使用 DocumentFragment 批量更新DOM
  - [ ] 减少 innerHTML 拼接
  - [ ] 添加事件委托

### 3.3 代码文档化
- [ ] Task 3.3.1: JSDoc 注释
  - [ ] 为 `api.js` 所有导出函数添加 JSDoc
  - [ ] 为 `utils.js` 公共函数添加 JSDoc
  - [ ] 为 Store 添加使用文档

---

## Task Dependencies

```
Phase 1: ✅ 已完成
  Task 1.1.1 → Task 1.1.2 ✅
  Task 1.2.1 → Task 1.2.2 ✅
  Task 1.3.1 → Task 1.3.2 → Task 1.3.3 ✅

Phase 2:
  Task 2.1.1 → Task 2.1.2 → Task 2.1.3
  Task 2.2.1 → Task 2.2.2
  Phase 1 完成后 → Task 2.3.1 → Task 2.3.2
  Task 2.4.1 → Task 2.4.2

Phase 3:
  Phase 2 完成后 → Task 3.1.1 → Task 3.1.2 → Task 3.1.3
  Phase 2 完成后 → Task 3.2.1 → Task 3.2.2
  Task 3.2 完成后 → Task 3.3.1
```

---

## 验收标准

- [x] Phase 1 完成后: `window.*` 全局函数 < 10个
- [x] Phase 1 完成后: 无重复的 `escapeHtml` 实现
- [x] Phase 1 完成后: 所有API调用通过 `API.*` 发起
- [ ] Phase 2 完成后: `index.html` < 1500行
- [ ] Phase 2 完成后: `keywords.js` 最大函数 < 80行
- [ ] Phase 2 完成后: Store 模式正常运作
- [ ] Phase 3 完成后: 单元测试覆盖率 > 60%
- [ ] Phase 3 完成后: 性能提升 30%+
