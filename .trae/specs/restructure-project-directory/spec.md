# 项目目录结构重构 Spec

## Why
当前项目目录结构存在根目录文件混乱、模块职责重叠、utils目录臃肿等问题，严重影响代码可维护性、可读性和团队协作效率。需要进行大规模重构以符合行业最佳实践。

## What Changes
- **BREAKING** 重构整个项目目录结构为分层架构
- 将散落在根目录的临时文件移动到正确位置
- 整合 `utils/xianyu/` 业务模块到 `app/services/`
- 合并 `app/` 发货模块到服务层
- 重命名 `reply_server/` 为 `app/api/`
- 重命名 `src/` 为 `app/core/`
- 重命名 `db_manager/` 为 `app/repositories/`
- 整理静态资源结构
- 清理缓存文件和临时文件
- 更新所有导入路径

## Impact
- Affected specs: 所有模块的导入路径
- Affected code: 全部 Python 模块文件
- Affected configs: pytest.ini, requirements.txt, 部署配置

## ADDED Requirements

### Requirement: Git 备份到 GitHub
在重构前，系统 SHALL 将当前代码完整提交并推送到 GitHub 远程仓库，确保代码安全可回滚。

#### Scenario: Git 提交成功
- **WHEN** 执行 git add, commit, push 操作
- **THEN** 所有更改成功推送到远程仓库

### Requirement: 分层目录结构
系统 SHALL 采用清晰的分层目录结构，遵循以下规范：
- `app/` 作为应用主目录
- `app/api/` 存放 API 路由和中间件
- `app/core/` 存放核心业务逻辑
- `app/services/` 存放业务服务层
- `app/repositories/` 存放数据访问层
- `app/utils/` 存放纯工具函数

#### Scenario: 目录结构符合规范
- **WHEN** 检查项目目录结构
- **THEN** 所有模块按职责正确分类存放

### Requirement: 导入路径统一
系统 SHALL 提供统一的模块导入入口，所有公开 API 通过 `app/__init__.py` 导出。

#### Scenario: 导入路径可预测
- **WHEN** 开发者需要导入某个模块
- **THEN** 可以通过统一的路径 `from app.xxx import yyy` 导入

### Requirement: 静态资源规范
系统 SHALL 将 HTML 页面文件统一存放在 `static/pages/` 目录下。

#### Scenario: 静态资源组织清晰
- **WHEN** 检查 static 目录
- **THEN** HTML 文件在 pages/ 子目录，JS/CSS/lib 各自独立

### Requirement: 临时文件清理
系统 SHALL 清理所有缓存文件和临时文件，并更新 `.gitignore` 防止再次提交。

#### Scenario: 缓存文件已清理
- **WHEN** 检查项目根目录
- **THEN** 不存在 `__pycache__/`, `.pytest_cache/`, `htmlcov/` 等缓存目录

### Requirement: 全面测试验证
重构完成后 SHALL 运行完整测试套件，确保所有功能正常工作。

#### Scenario: 测试全部通过
- **WHEN** 执行 pytest 测试
- **THEN** 所有测试用例通过，覆盖率不低于重构前

### Requirement: 代码审查
重构完成后 SHALL 进行代码审查，确保代码质量符合规范。

#### Scenario: 代码审查通过
- **WHEN** 审查重构后的代码
- **THEN** 代码结构清晰、命名规范、无冗余代码

## MODIFIED Requirements

### Requirement: 启动入口位置
启动入口从 `scripts/Start.py` 移动到 `app/main.py`，保持向后兼容的符号链接。

### Requirement: 配置文件位置
配置文件保持在 `configs/` 目录不变，但更新内部导入路径。

## REMOVED Requirements

### Requirement: 旧的目录结构
**Reason**: 不符合分层架构原则，职责混乱
**Migration**: 按新结构逐步迁移，保留向后兼容的导入别名
