# Tasks - 前端代码三阶段重构

## 阶段1：清理和稳定（立即实施）

### 任务 1.1: 统一API调用入口
- [ ] 1.1.1: 审查 `keywords.js` 中的所有fetch调用
- [ ] 1.1.2: 审查 `cookies.js` 中的所有fetch调用
- [ ] 1.1.3: 审查 `items.js` 中的所有fetch调用
- [ ] 1.1.4: 审查 `dashboard.js` 中的所有fetch调用
- [ ] 1.1.5: 审查 `delivery.js` 中的所有fetch调用
- [ ] 1.1.6: 重构所有直接fetch为 `API.fetchJSON()` 调用
- [ ] 1.1.7: 验证API功能正常工作

### 任务 1.2: 抽取公共函数到utils.js
- [ ] 1.2.1: 审查所有模块中的 `escapeHtml` 实现
- [ ] 1.2.2: 确认 `utils.js` 中 `escapeHtml` 为唯一实现
- [ ] 1.2.3: 更新 `keywords.js` 使用 `Utils.escapeHtml`
- [ ] 1.2.4: 更新 `dashboard.js` 使用 `Utils.escapeHtml`
- [ ] 1.2.5: 更新其他模块使用 `Utils.escapeHtml`
- [ ] 1.2.6: 验证HTML转义功能正常

### 任务 1.3: 规范化window暴露模式
- [ ] 1.3.1: 分析 `app.js` 中所有 `window.*` 暴露
- [ ] 1.3.2: 创建 `App` 命名空间结构
- [ ] 1.3.3: 将各模块函数挂载到 `App.*` 命名空间
- [ ] 1.3.4: 保持必要的 `window.funcName` 暴露供HTML onclick使用
- [ ] 1.3.5: 验证所有HTML onclick调用正常工作

---

## 阶段2：架构优化（2-4周）

### 任务 2.1: Modal HTML动态创建
- [ ] 2.1.1: 列出 `index.html` 中所有Modal HTML
- [ ] 2.1.2: 创建 `ModalService` 模块
- [ ] 2.1.3: 实现 `ModalService.show(modalId)` 方法
- [ ] 2.1.4: 实现 `ModalService.hide(modalId)` 方法
- [ ] 2.1.5: 逐个迁移Modal到动态创建（qrCodeLoginModal, addCardModal, addDeliveryRuleModal等）
- [ ] 2.1.6: 验证所有Modal功能正常

### 任务 2.2: 拆分keywords.js过长函数
- [ ] 2.2.1: 分析 `renderKeywordsList()` 函数结构
- [ ] 2.2.2: 拆分 `renderKeywordItem()` 函数
- [ ] 2.2.3: 拆分 `renderKeywordBadges()` 函数
- [ ] 2.2.4: 拆分 `renderKeywordContent()` 函数
- [ ] 2.2.5: 分析 `addKeyword()` 函数结构
- [ ] 2.2.6: 拆分 `validateKeywordInput()` 函数
- [ ] 2.2.7: 拆分 `buildKeywordData()` 函数
- [ ] 2.2.8: 拆分 `saveKeyword()` 函数
- [ ] 2.2.9: 验证关键词CRUD功能正常

### 任务 2.3: 添加请求取消机制
- [ ] 2.3.1: 在 `API` 模块添加 `AbortController` 支持
- [ ] 2.3.2: 实现请求去抖/节流
- [ ] 2.3.3: 在账号切换场景添加取消逻辑
- [ ] 2.3.4: 验证快速切换不会导致数据错乱

### 任务 2.4: 实现状态管理Store
- [ ] 2.4.1: 创建 `App.Store` 模块
- [ ] 2.4.2: 实现 `Store.get(key)` 方法
- [ ] 2.4.3: 实现 `Store.set(key, value)` 方法
- [ ] 2.4.4: 实现状态变更订阅机制
- [ ] 2.4.5: 迁移全局变量到Store管理
- [ ] 2.4.6: 验证状态同步正常

### 任务 2.5: 重构其他模块
- [ ] 2.5.1: 重构 `cards.js` 过长函数
- [ ] 2.5.2: 重构 `delivery.js` 过长函数
- [ ] 2.5.3: 重构 `notifications.js` 过长函数
- [ ] 2.5.4: 验证所有模块功能正常

---

## 阶段3：质量提升（持续）

### 任务 3.1: CSS架构优化
- [ ] 3.1.1: 审查 `variables.css` 中的CSS变量
- [ ] 3.1.2: 在所有CSS中统一使用CSS变量
- [ ] 3.1.3: 创建通用组件样式类
- [ ] 3.1.4: 验证样式一致性

### 任务 3.2: 添加单元测试
- [ ] 3.2.1: 配置Jest测试框架
- [ ] 3.2.2: 为 `Utils.escapeHtml` 编写测试
- [ ] 3.2.3: 为 `API.fetchJSON` 编写测试
- [ ] 3.2.4: 为 `App.Store` 编写测试
- [ ] 3.2.5: 建立CI测试流程

### 任务 3.3: API配置化
- [ ] 3.3.1: 创建API配置文件
- [ ] 3.3.2: 实现API版本管理
- [ ] 3.3.3: 添加API请求拦截器
- [ ] 3.3.4: 验证API配置生效

---

## Task Dependencies

```
阶段1:
├── [1.1] 统一API调用入口
│   └── 必须在 [1.2] 之前完成，以便统一调用方式
├── [1.2] 抽取公共函数
│   └── 独立任务，可并行执行
└── [1.3] 规范化window暴露
    └── 必须在 [1.2] 之后完成

阶段2:
├── [2.1] Modal动态创建
│   └── 可在阶段1完成后独立执行
├── [2.2] 拆分keywords.js
│   └── 可在阶段1完成后独立执行
├── [2.3] 请求取消机制
│   └── 依赖 [1.1] API统一
└── [2.4] 状态管理Store
    └── 依赖 [1.3] window规范化

阶段3:
├── [3.1] CSS优化
│   └── 可在任何阶段执行
├── [3.2] 单元测试
│   └── 依赖阶段1和阶段2完成
└── [3.3] API配置化
    └── 依赖 [2.3] 请求取消机制
```
