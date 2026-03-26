# 贡献指南

感谢您考虑为闲鱼自动回复系统做出贡献！

## 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发流程](#开发流程)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [测试要求](#测试要求)

## 行为准则

本项目采用贡献者公约作为行为准则。参与此项目即表示您同意遵守其条款。

## 如何贡献

### 报告 Bug

1. 在 [Issues](../../issues) 中搜索是否已有相同问题
2. 如果没有，使用 [Bug 报告模板](.github/ISSUE_TEMPLATE/bug_report.md) 创建新 Issue
3. 提供详细的复现步骤和环境信息

### 提出新功能

1. 在 [Issues](../../issues) 中讨论您的想法
2. 使用 [功能请求模板](.github/ISSUE_TEMPLATE/feature_request.md) 创建 Issue
3. 等待维护者反馈后再开始实现

### 提交代码

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 开发流程

### 环境设置

```bash
# 克隆仓库
git clone https://github.com/your-username/xianyu-auto-reply.git
cd xianyu-auto-reply

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows

# 安装开发依赖
make dev

# 安装 pre-commit 钩子
pre-commit install
```

### 运行测试

```bash
# 运行所有测试
make test

# 运行单元测试
make test-unit

# 运行测试并生成覆盖率报告
make test-cov
```

### 代码检查

```bash
# 运行 lint 检查
make lint

# 格式化代码
make format

# 类型检查
make type-check

# 运行所有检查
make check
```

## 代码规范

### Python

- 遵循 [PEP 8](https://pep8.org/) 规范
- 使用类型注解
- 函数和类添加文档字符串
- 单行不超过 120 字符
- 使用 ruff 进行代码格式化

### JavaScript

- 使用 ES6+ 语法
- 遵循项目现有的代码风格
- 函数添加 JSDoc 注释

### 文档

- 更新相关文档
- 使用中文编写文档
- 保持文档简洁明了

## 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型 (type)

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

### 示例

```
feat(keywords): add regex match support

- Add regex match type to keyword matcher
- Update database schema for match_type field
- Add unit tests for regex matching

Closes #123
```

## 测试要求

- 新功能必须添加单元测试
- Bug 修复必须添加回归测试
- 测试覆盖率不应降低
- 所有测试必须通过

### 测试命名

```python
def test_<功能>_<场景>_<预期结果>():
    pass

# 示例
def test_keyword_match_exact_input_returns_match():
    pass
```

## Pull Request 检查清单

- [ ] 代码遵循项目规范
- [ ] 已添加必要的测试
- [ ] 所有测试通过
- [ ] 已更新相关文档
- [ ] 提交信息符合规范
- [ ] PR 描述清晰完整

## 获取帮助

- 查看 [文档](docs/)
- 在 [Discussions](../../discussions) 中提问
- 联系维护者

再次感谢您的贡献！
