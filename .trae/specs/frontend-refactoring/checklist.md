# Checklist - 前端代码三阶段重构

## 阶段1：清理和稳定

### 任务 1.1: 统一API调用入口

- [ ] keywords.js 中所有fetch调用已重构为 API.fetchJSON()
- [ ] cookies.js 中所有fetch调用已重构为 API.fetchJSON()
- [ ] items.js 中所有fetch调用已重构为 API.fetchJSON()
- [ ] dashboard.js 中所有fetch调用已重构为 API.fetchJSON()
- [ ] delivery.js 中所有fetch调用已重构为 API.fetchJSON()
- [ ] 其他模块中的直接fetch调用已重构
- [ ] API功能测试通过

### 任务 1.2: 抽取公共函数到utils.js

- [ ] keywords.js 不再包含独立的 escapeHtml 实现
- [ ] dashboard.js 不再包含独立的 escapeHtml 实现
- [ ] 所有模块使用 Utils.escapeHtml()
- [ ] HTML转义功能验证正常

### 任务 1.3: 规范化window暴露模式

- [ ] App 命名空间结构已创建
- [ ] 各模块函数已挂载到 App.* 命名空间
- [ ] HTML onclick="showSection('xxx')" 调用正常工作
- [ ] HTML onclick="toggleSidebar()" 调用正常工作
- [ ] 其他全局函数调用正常工作

---

## 阶段2：架构优化

### 任务 2.1: Modal HTML动态创建

- [ ] ModalService 模块已创建
- [ ] ModalService.show() 方法已实现
- [ ] ModalService.hide() 方法已实现
- [ ] index.html 中Modal HTML已移除
- [ ] qrCodeLoginModal 动态创建正常
- [ ] addCardModal 动态创建正常
- [ ] addDeliveryRuleModal 动态创建正常
- [ ] 其他Modal动态创建正常

### 任务 2.2: 拆分keywords.js过长函数

- [ ] renderKeywordsList() 已拆分为多个小函数
- [ ] addKeyword() 已拆分为多个小函数
- [ ] 每个函数不超过50行
- [ ] 关键词CRUD功能验证正常

### 任务 2.3: 添加请求取消机制

- [ ] API 模块支持 AbortController
- [ ] 账号切换时旧请求被正确取消
- [ ] 快速切换不会导致数据错乱

### 任务 2.4: 实现状态管理Store

- [ ] App.Store 模块已创建
- [ ] Store.get() 方法已实现
- [ ] Store.set() 方法已实现
- [ ] 状态订阅机制已实现
- [ ] 全局变量已迁移到Store
- [ ] 状态同步验证正常

### 任务 2.5: 重构其他模块

- [ ] cards.js 函数已拆分
- [ ] delivery.js 函数已拆分
- [ ] notifications.js 函数已拆分
- [ ] 所有模块功能验证正常

---

## 阶段3：质量提升

### 任务 3.1: CSS架构优化

- [ ] CSS变量使用已统一
- [ ] 组件样式类已创建
- [ ] 样式一致性验证通过

### 任务 3.2: 添加单元测试

- [ ] Jest测试框架已配置
- [ ] Utils.escapeHtml 测试已编写
- [ ] API.fetchJSON 测试已编写
- [ ] App.Store 测试已编写
- [ ] CI测试流程已建立

### 任务 3.3: API配置化

- [ ] API配置文件已创建
- [ ] API版本管理已实现
- [ ] 请求拦截器已添加
- [ ] 测试/生产环境切换正常

---

## 最终验证

- [ ] 所有HTML onclick调用正常
- [ ] 所有API调用功能正常
- [ ] 所有Modal显示/隐藏正常
- [ ] 状态管理正常工作
- [ ] 无console错误
- [ ] 页面加载时间 <2s
