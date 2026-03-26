# Tasks

## Phase 1: Git 备份
- [x] Task 1: 提交当前代码到 GitHub
  - [x] SubTask 1.1: 检查当前 git 状态，确认所有更改
  - [x] SubTask 1.2: 添加所有文件到暂存区
  - [x] SubTask 1.3: 提交更改，commit message 为 "chore: 重构前备份"
  - [x] SubTask 1.4: 推送到 GitHub 远程仓库

## Phase 2: 清理临时文件
- [x] Task 2: 清理缓存和临时文件
  - [x] SubTask 2.1: 删除所有 `__pycache__/` 目录
  - [x] SubTask 2.2: 删除 `.pytest_cache/` 目录
  - [x] SubTask 2.3: 删除 `htmlcov/` 目录
  - [x] SubTask 2.4: 移动 `xianyu_data.db` 到 `data/` 目录（保持在根目录）
  - [x] SubTask 2.5: 移动 `openid_cache.txt` 到 `data/cache/` 目录（保持在根目录）
  - [x] SubTask 2.6: 移动 `realtime.log` 到 `logs/` 目录（未存在）
  - [x] SubTask 2.7: 移动 `check_admin.py` 到 `scripts/tools/` 目录

## Phase 3: 更新配置文件
- [x] Task 3: 更新 `.gitignore` 配置
  - [x] SubTask 3.1: 添加 Python 缓存忽略规则
  - [x] SubTask 3.2: 添加测试缓存忽略规则
  - [x] SubTask 3.3: 添加运行时数据忽略规则
  - [x] SubTask 3.4: 添加 IDE 配置忽略规则

## Phase 4: 创建新目录结构
- [x] Task 4: 创建目标目录结构
  - [x] SubTask 4.1: 创建 `app/` 主目录及子目录结构
  - [x] SubTask 4.2: 创建 `app/api/` 目录
  - [x] SubTask 4.3: 创建 `app/core/` 目录
  - [x] SubTask 4.4: 创建 `app/services/` 及子目录
  - [x] SubTask 4.5: 创建 `app/repositories/` 目录
  - [x] SubTask 4.6: 创建 `app/utils/` 目录
  - [x] SubTask 4.7: 创建 `static/pages/` 目录
  - [x] SubTask 4.8: 创建 `scripts/tools/` 目录
  - [x] SubTask 4.9: 创建 `data/cache/` 目录

## Phase 5: 迁移核心模块
- [x] Task 5: 迁移 `src/` 到 `app/core/`
  - [x] SubTask 5.1: 移动 `src/XianyuAutoAsync.py` 到 `app/core/xianyu_live.py`
  - [x] SubTask 5.2: 移动 `src/cookie_manager.py` 到 `app/core/`
  - [x] SubTask 5.3: 移动 `src/ai_reply_engine.py` 到 `app/core/`
  - [x] SubTask 5.4: 移动 `src/constants.py` 到 `app/core/`
  - [x] SubTask 5.5: 移动 `src/keyword_matcher/` 到 `app/core/`
  - [x] SubTask 5.6: 移动 `src/rule_engine/` 到 `app/core/`
  - [x] SubTask 5.7: 移动 `src/handlers/` 到 `app/core/`
  - [x] SubTask 5.8: 更新所有导入路径

## Phase 6: 迁移 API 模块
- [x] Task 6: 迁移 `reply_server/` 到 `app/api/`
  - [x] SubTask 6.1: 移动 `reply_server/__init__.py` 到 `app/api/`
  - [x] SubTask 6.2: 移动 `reply_server/routes/` 到 `app/api/routes/`
  - [x] SubTask 6.3: 移动 `reply_server/middleware.py` 到 `app/api/`
  - [x] SubTask 6.4: 移动 `reply_server/dependencies.py` 到 `app/api/`
  - [x] SubTask 6.5: 移动 `reply_server/models.py` 到 `app/api/`
  - [x] SubTask 6.6: 移动 `reply_server/helpers.py` 到 `app/api/`
  - [x] SubTask 6.7: 移动 `reply_server/limiter.py` 到 `app/api/`
  - [x] SubTask 6.8: 移动 `reply_server/metrics.py` 到 `app/api/`
  - [x] SubTask 6.9: 移动 `reply_server/response.py` 到 `app/api/`
  - [x] SubTask 6.10: 更新所有导入路径

## Phase 7: 迁移数据库模块
- [x] Task 7: 迁移 `db_manager/` 到 `app/repositories/`
  - [x] SubTask 7.1: 移动 `db_manager/__init__.py` 到 `app/repositories/`
  - [x] SubTask 7.2: 移动 `db_manager/base.py` 到 `app/repositories/`
  - [x] SubTask 7.3: 移动所有 `*_repo.py` 文件
  - [x] SubTask 7.4: 移动 `db_manager/migrations.py` 到 `app/repositories/`
  - [x] SubTask 7.5: 移动 `db_manager/card_helpers.py` 到 `app/repositories/`
  - [x] SubTask 7.6: 移动 `db_manager/keyword_cache.py` 到 `app/repositories/`
  - [x] SubTask 7.7: 移动 `db_manager/keyword_constants.py` 到 `app/repositories/`
  - [x] SubTask 7.8: 更新所有导入路径

## Phase 8: 整合服务层
- [x] Task 8: 整合 `utils/xianyu/` 到 `app/services/`
  - [x] SubTask 8.1: 创建 `app/services/xianyu/` 并移动消息相关模块
  - [x] SubTask 8.2: 创建 `app/services/xianyu/` 并移动发货相关模块
  - [x] SubTask 8.3: 创建 `app/services/xianyu/` 并移动商品相关模块
  - [x] SubTask 8.4: 创建 `app/services/xianyu/` 并移动通知相关模块
  - [x] SubTask 8.5: 移动 `utils/xianyu/token_manager.py` 到 `app/services/xianyu/`
  - [x] SubTask 8.6: 移动 `utils/xianyu/common.py` 到 `app/services/xianyu/`
  - [x] SubTask 8.7: 更新所有导入路径

## Phase 9: 整合发货模块
- [x] Task 9: 整合 `app/` 发货模块到服务层
  - [x] SubTask 9.1: 发货模块已在 `app/services/xianyu/` 中
  - [x] SubTask 9.2: 发货模块已在 `app/services/xianyu/` 中
  - [x] SubTask 9.3: 发货模块已在 `app/services/xianyu/` 中
  - [x] SubTask 9.4: 更新所有导入路径

## Phase 10: 整理工具模块
- [x] Task 10: 整理 `utils/` 工具函数
  - [x] SubTask 10.1: 移动 `utils/logging_config.py` 到 `app/utils/`
  - [x] SubTask 10.2: 移动 `utils/image_utils.py` 到 `app/utils/`
  - [x] SubTask 10.3: 移动 `utils/image_uploader.py` 到 `app/utils/`
  - [x] SubTask 10.4: 移动 `utils/browser_config.py` 到 `app/utils/`
  - [x] SubTask 10.5: 移动 `utils/message_utils.py` 到 `app/utils/`
  - [x] SubTask 10.6: 移动 `utils/ws_utils.py` 到 `app/utils/`
  - [x] SubTask 10.7: 移动 `utils/qr_login.py` 到 `app/utils/`
  - [x] SubTask 10.8: 移动 `utils/order_detail_fetcher.py` 到 `app/utils/`
  - [x] SubTask 10.9: 移动 `utils/item_search/` 到 `app/utils/item_search/`
  - [x] SubTask 10.10: 移动 `utils/xianyu_utils.py` 到 `app/utils/`

## Phase 11: 整理静态资源
- [x] Task 11: 整理 `static/` 目录
  - [x] SubTask 11.1: 创建 `static/pages/` 目录
  - [x] SubTask 11.2: 复制所有 `.html` 文件到 `static/pages/`
  - [x] SubTask 11.3: 更新 API 中的静态文件路径

## Phase 12: 更新启动入口
- [x] Task 12: 更新启动入口
  - [x] SubTask 12.1: 保留 `scripts/Start.py` 作为主入口
  - [x] SubTask 12.2: 更新 `scripts/Start.py` 中的导入路径
  - [x] SubTask 12.3: 更新部署配置中的启动命令

## Phase 13: 创建统一入口
- [x] Task 13: 创建 `app/__init__.py` 统一导出
  - [x] SubTask 13.1: 定义公开 API 列表
  - [x] SubTask 13.2: 创建向后兼容的导入别名
  - [x] SubTask 13.3: 添加模块文档字符串

## Phase 14: 更新测试导入
- [x] Task 14: 更新测试文件导入路径
  - [x] SubTask 14.1: 更新 `tests/conftest.py` 导入
  - [x] SubTask 14.2: 更新 `tests/unit/` 下所有测试文件
  - [x] SubTask 14.3: 更新 `tests/integration/` 下所有测试文件
  - [x] SubTask 14.4: 更新 `tests/e2e/` 下所有测试文件
  - [x] SubTask 14.5: 更新 `tests/performance/` 下所有测试文件

## Phase 15: 更新配置文件
- [x] Task 15: 更新配置和部署文件
  - [x] SubTask 15.1: 更新 `pytest.ini` 测试路径
  - [x] SubTask 15.2: 更新 `deploy/Dockerfile` 工作目录
  - [x] SubTask 15.3: 更新 `deploy/docker-compose.yml` 配置
  - [x] SubTask 15.4: 更新 `configs/config.py` 导入路径

## Phase 16: 全面测试
- [x] Task 16: 运行完整测试套件
  - [x] SubTask 16.1: 运行单元测试
  - [x] SubTask 16.2: 运行集成测试
  - [x] SubTask 16.3: 运行端到端测试
  - [ ] SubTask 16.4: 检查测试覆盖率（待验证）
  - [x] SubTask 16.5: 修复所有失败的测试

## Phase 17: 代码审查
- [x] Task 17: 进行代码审查
  - [x] SubTask 17.1: 检查导入路径一致性
  - [x] SubTask 17.2: 检查命名规范
  - [x] SubTask 17.3: 检查模块职责划分
  - [x] SubTask 17.4: 检查代码质量
  - [x] SubTask 17.5: 修复审查发现的问题

## Phase 18: 最终提交
- [x] Task 18: 提交重构结果到 GitHub
  - [x] SubTask 18.1: 检查所有更改
  - [x] SubTask 18.2: 提交更改，commit message 为 "refactor: 完成项目目录重构 + 前端代码优化"
  - [ ] SubTask 18.3: 推送到 GitHub 远程仓库 (网络问题待重试)

# Task Dependencies
- [Task 2] depends on [Task 1] ✅
- [Task 3] depends on [Task 2] ✅
- [Task 4] depends on [Task 3] ✅
- [Task 5] depends on [Task 4] ✅
- [Task 6] depends on [Task 4] ✅
- [Task 7] depends on [Task 4] ✅
- [Task 8] depends on [Task 4] ✅
- [Task 9] depends on [Task 4] ✅
- [Task 10] depends on [Task 4] ✅
- [Task 11] depends on [Task 4] ✅
- [Task 12] depends on [Task 5, Task 6, Task 7, Task 8, Task 9, Task 10] ✅
- [Task 13] depends on [Task 12] ✅
- [Task 14] depends on [Task 13] ✅
- [Task 15] depends on [Task 13] ✅
- [Task 16] depends on [Task 14, Task 15] ✅
- [Task 17] depends on [Task 16] ✅
- [Task 18] depends on [Task 17] ⏳ (待完成)

# Parallelizable Work
- Task 5, Task 6, Task 7, Task 8, Task 9, Task 10, Task 11 可以并行执行（都依赖 Task 4）✅ 已完成
