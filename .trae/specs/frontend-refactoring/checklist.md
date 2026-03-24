# 前端重构检查清单

## Phase 1: 清理和稳定

### 1.1 全局命名空间清理
- [ ] `window.App` 命名空间对象已创建
- [ ] `showSection`, `toggleSidebar`, `showToast` 等核心函数已迁移到 `App.*`
- [ ] `index.html` 中所有 `window.*` 调用已更新为 `App.*`
- [ ] 各模块中的 `window.showToast`, `window.showLoading` 已改为模块内部调用
- [ ] 功能验证: 页面导航正常
- [ ] 功能验证: Toast 通知正常
- [ ] 功能验证: Sidebar 切换正常

### 1.2 公共函数抽取
- [ ] `utils.js` 包含完整的 `escapeHtml` 实现
- [ ] `keywords.js` 中的重复 `escapeHtml` 已移除
- [ ] `dashboard.js` 中的重复 `escapeHtml` 已移除
- [ ] 所有需要HTML转义的地方都导入并使用 `utils.escapeHtml`
- [ ] 其他公共函数 (`formatDate`, `validateForm`) 已抽取到 `utils.js`
- [ ] 功能验证: 用户输入特殊字符正确转义显示

### 1.3 统一API调用入口
- [ ] `API` 命名空间已在 `api.js` 中定义
- [ ] `API.cookies.*` 端点组已实现
- [ ] `API.keywords.*` 端点组已实现
- [ ] `API.items.*` 端点组已实现
- [ ] `API.dashboard.*` 端点组已实现
- [ ] `API.ai.*` 端点组已实现
- [ ] `API.delivery.*` 端点组已实现
- [ ] 请求拦截器正确添加 Authorization header
- [ ] 统一错误处理机制已实现
- [ ] `cookies.js` 中的直接 `fetch` 调用已移除
- [ ] `keywords.js` 中的直接 `fetch` 调用已移除
- [ ] `items.js` 中的直接 `fetch` 调用已移除
- [ ] `dashboard.js` 中的直接 `fetch` 调用已移除
- [ ] `ai.js` 中的直接 `fetch` 调用已移除
- [ ] `delivery.js` 中的直接 `fetch` 调用已移除
- [ ] 功能验证: Cookie管理 CRUD 正常
- [ ] 功能验证: 关键词管理 CRUD 正常
- [ ] 功能验证: 商品管理 CRUD 正常
- [ ] 功能验证: Dashboard 数据加载正常
- [ ] 功能验证: AI配置保存正常
- [ ] 功能验证: 发货规则 CRUD 正常
- [ ] AbortController 已实现
- [ ] `API.cancelPending()` 方法已提供
- [ ] 页面切换时 pending 请求已自动取消
- [ ] 功能验证: 快速切换账号时无请求混乱

## Phase 2: 架构优化

### 2.1 Modal HTML 分离
- [ ] `ModalManager` 类已在 `utils.js` 中实现
- [ ] `#qrCodeLoginModal` HTML 已从 `index.html` 移除
- [ ] `ModalManager.showQRCodeLogin()` 方法已实现
- [ ] `#addCardModal` HTML 已从 `index.html` 移除
- [ ] `#editCardModal` HTML 已从 `index.html` 移除
- [ ] 其他内联 Modal HTML 已移除
- [ ] `index.html` 行数已减少到 < 1500行
- [ ] 功能验证: 扫码登录 Modal 正常打开/关闭
- [ ] 功能验证: 卡券 Modal 正常打开/关闭
- [ ] 功能验证: 所有 Modal 事件绑定正常

### 2.2 函数拆分重构
- [ ] `keywords.js` 中 `renderKeywordsList()` 已拆分 (< 80行)
- [ ] `keywords.js` 中 `addKeyword()` 已拆分 (< 80行)
- [ ] 新函数: `renderKeywordsTable()` 已实现
- [ ] 新函数: `renderKeywordRow()` 已实现
- [ ] 新函数: `bindKeywordEvents()` 已实现
- [ ] 新函数: `showAddKeywordForm()` 已实现
- [ ] 新函数: `validateKeywordInput()` 已实现
- [ ] 新函数: `submitKeyword()` 已实现
- [ ] `cookies.js` 中超过50行的函数已拆分
- [ ] `items.js` 中超过50行的函数已拆分
- [ ] 功能验证: 关键词列表渲染正常
- [ ] 功能验证: 添加关键词流程正常
- [ ] 功能验证: 编辑关键词流程正常
- [ ] 功能验证: 删除关键词流程正常

### 2.3 简单状态管理
- [ ] `store.js` 模块已创建
- [ ] `Store.create(name, initialState)` 工厂函数已实现
- [ ] `Store.getState()` 方法已实现
- [ ] `Store.setState()` 方法已实现
- [ ] `Store.subscribe()` 方法已实现
- [ ] `keywordsData` 状态已迁移到 Store
- [ ] `currentCookieId` 状态已迁移到 Store
- [ ] `dashboardData` 状态已迁移到 Store
- [ ] `aiSettings` 状态已迁移到 Store
- [ ] 功能验证: 状态更新触发UI更新
- [ ] 功能验证: 状态订阅通知正常

### 2.4 CSS 架构优化
- [ ] `variables.css` 中的所有变量已定义完整
- [ ] 所有CSS文件引用统一变量 (使用 `var(--*)`)
- [ ] 硬编码颜色值已替换为变量
- [ ] 硬编码间距值已替换为变量
- [ ] `.btn-primary`, `.card`, `.modal` 组件样式已统一
- [ ] 功能验证: 页面样式一致
- [ ] 功能验证: 主题变量修改生效

## Phase 3: 质量提升

### 3.1 单元测试框架
- [ ] Jest 或 Vitest 已配置
- [ ] `tests/` 目录结构已创建
- [ ] 测试环境已配置
- [ ] `utils.js` 函数测试已编写
- [ ] `escapeHtml` 测试覆盖: 正常文本、HTML标签、特殊字符、XSS场景
- [ ] `ModalManager` 测试已编写
- [ ] API Mock 已配置
- [ ] `API.cookies.list()` 测试已编写
- [ ] API 错误处理测试已编写
- [ ] 测试覆盖率 > 60%

### 3.2 性能优化
- [ ] `loadDashboard()` 和 `loadCookies()` 重复请求已分析
- [ ] API 响应缓存已实现
- [ ] 缓存失效机制已实现
- [ ] DocumentFragment 批量DOM更新已应用
- [ ] 事件委托已优化
- [ ] 功能验证: 页面加载时间减少 30%+
- [ ] 功能验证: 重复请求已消除

### 3.3 代码文档化
- [ ] `api.js` 所有导出函数已添加 JSDoc
- [ ] `utils.js` 公共函数已添加 JSDoc
- [ ] Store 使用文档已编写
- [ ] README 或 JSDoc 站点已搭建

---

## 最终验收

- [ ] `window.*` 全局函数 < 10个
- [ ] 无重复的 `escapeHtml` 实现
- [ ] 所有API调用通过 `API.*` 发起
- [ ] `index.html` < 1500行
- [ ] `keywords.js` 最大函数 < 80行
- [ ] Store 模式正常运作
- [ ] 单元测试覆盖率 > 60%
- [ ] 性能提升 30%+
- [ ] 所有功能回归测试通过
- [ ] 无 console.error 或未处理异常
