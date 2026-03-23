# 开发流程

[返回主目录](./project_rules.md)

---

## 4.1 分支管理策略

```
main (生产分支)
  │
  ├── develop (开发分支)
  │     │
  │     ├── feature/xxx (功能分支)
  │     ├── feature/yyy
  │     │
  │     └── bugfix/zzz (修复分支)
  │
  └── hotfix/aaa (紧急修复分支)
```

### 分支命名规范

| 分支类型 | 命名格式 | 示例 |
|---------|---------|------|
| 功能分支 | feature/功能描述 | feature/ai-reply-enhance |
| 修复分支 | bugfix/问题描述 | bugfix/websocket-reconnect |
| 紧急修复 | hotfix/问题描述 | hotfix/security-patch |
| 发布分支 | release/版本号 | release/v1.2.0 |

---

## 4.2 开发工作流

```
1. 创建功能分支
   git checkout -b feature/new-feature

2. 开发和测试
   - 编写代码
   - 编写单元测试
   - 本地测试通过

3. 提交代码
   git add .
   git commit -m "feat: 添加新功能描述"

4. 推送分支
   git push origin feature/new-feature

5. 创建 Pull Request
   - 填写PR描述
   - 关联Issue
   - 请求代码审查

6. 代码审查
   - 通过审查后合并
   - 删除功能分支

7. 部署测试
   - 在测试环境验证
   - 确认无误后合并到main
```

---

## 4.3 Commit 规范

### Commit 消息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

| 类型 | 说明 | 示例 |
|------|------|------|
| feat | 新功能 | feat: 添加AI智能回复功能 |
| fix | 修复Bug | fix: 修复WebSocket断连问题 |
| docs | 文档更新 | docs: 更新部署文档 |
| style | 代码格式 | style: 格式化代码缩进 |
| refactor | 重构 | refactor: 重构Cookie管理模块 |
| perf | 性能优化 | perf: 优化数据库查询性能 |
| test | 测试 | test: 添加单元测试 |
| chore | 构建/工具 | chore: 更新依赖版本 |

### 示例

```bash
# 功能添加
git commit -m "feat(ai): 添加意图分类功能

- 支持价格、技术、默认三种意图
- 添加自定义提示词配置
- 优化响应时间"

# Bug修复
git commit -m "fix(ws): 修复WebSocket重连逻辑

解决网络波动导致的连接丢失问题，添加指数退避重试机制

Closes #123"

# 文档更新
git commit -m "docs: 更新API文档"
```

---

## 4.4 代码审查清单

### 功能正确性

- [ ] 功能是否按需求实现
- [ ] 边界条件是否处理
- [ ] 错误处理是否完善
- [ ] 日志记录是否充分

### 代码质量

- [ ] 代码是否遵循规范
- [ ] 命名是否清晰准确
- [ ] 是否有冗余代码
- [ ] 是否有安全风险

### 测试覆盖

- [ ] 是否有单元测试
- [ ] 测试覆盖率是否达标
- [ ] 边界情况是否测试
- [ ] 异常情况是否测试

### 性能考虑

- [ ] 是否有性能问题
- [ ] 数据库查询是否优化
- [ ] 是否有内存泄漏风险
- [ ] 并发处理是否正确
