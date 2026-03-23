# Checklist

## Phase 1: Git 备份
- [ ] Git 状态检查完成，确认所有更改已暂存
- [ ] 代码已提交到本地仓库
- [ ] 代码已推送到 GitHub 远程仓库

## Phase 2: 清理临时文件
- [ ] 所有 `__pycache__/` 目录已删除
- [ ] `.pytest_cache/` 目录已删除
- [ ] `htmlcov/` 目录已删除
- [ ] `xianyu_data.db` 已移动到 `data/` 目录
- [ ] `openid_cache.txt` 已移动到 `data/cache/` 目录
- [ ] `realtime.log` 已移动到 `logs/` 目录
- [ ] `check_admin.py` 已移动到 `scripts/tools/` 目录

## Phase 3: 配置更新
- [ ] `.gitignore` 已更新，包含所有必要的忽略规则

## Phase 4: 目录结构
- [ ] `app/` 主目录已创建
- [ ] `app/api/` 目录已创建
- [ ] `app/core/` 目录已创建
- [ ] `app/services/` 及子目录已创建
- [ ] `app/repositories/` 目录已创建
- [ ] `app/utils/` 目录已创建
- [ ] `static/pages/` 目录已创建
- [ ] `scripts/tools/` 目录已创建
- [ ] `data/cache/` 目录已创建

## Phase 5: 核心模块迁移
- [ ] `XianyuAutoAsync.py` 已迁移到 `app/core/xianyu_live.py`
- [ ] `cookie_manager.py` 已迁移到 `app/core/`
- [ ] `ai_reply_engine.py` 已迁移到 `app/core/`
- [ ] `constants.py` 已迁移到 `app/core/`
- [ ] `keyword_matcher/` 已迁移到 `app/core/`
- [ ] `rule_engine/` 已迁移到 `app/core/`
- [ ] `handlers/` 已迁移到 `app/core/`
- [ ] 核心模块导入路径已全部更新

## Phase 6: API 模块迁移
- [ ] `reply_server/__init__.py` 已迁移到 `app/api/`
- [ ] `reply_server/routes/` 已迁移到 `app/api/routes/`
- [ ] `reply_server/middleware.py` 已迁移到 `app/api/`
- [ ] `reply_server/dependencies.py` 已迁移到 `app/api/`
- [ ] `reply_server/models.py` 已迁移到 `app/api/`
- [ ] `reply_server/helpers.py` 已迁移到 `app/api/`
- [ ] `reply_server/limiter.py` 已迁移到 `app/api/`
- [ ] `reply_server/metrics.py` 已迁移到 `app/api/`
- [ ] `reply_server/response.py` 已迁移到 `app/api/`
- [ ] API 模块导入路径已全部更新

## Phase 7: 数据库模块迁移
- [ ] `db_manager/__init__.py` 已迁移到 `app/repositories/`
- [ ] `db_manager/base.py` 已迁移到 `app/repositories/`
- [ ] 所有 `*_repo.py` 文件已迁移
- [ ] `db_manager/migrations.py` 已迁移到 `app/repositories/`
- [ ] `db_manager/card_helpers.py` 已迁移到 `app/repositories/`
- [ ] `db_manager/keyword_cache.py` 已迁移到 `app/repositories/`
- [ ] `db_manager/keyword_constants.py` 已迁移到 `app/repositories/`
- [ ] 数据库模块导入路径已全部更新

## Phase 8: 服务层整合
- [ ] 消息相关模块已迁移到 `app/services/message/`
- [ ] 发货相关模块已迁移到 `app/services/delivery/`
- [ ] 商品相关模块已迁移到 `app/services/item/`
- [ ] 通知相关模块已迁移到 `app/services/notification/`
- [ ] `token_manager.py` 已迁移到 `app/services/`
- [ ] `common.py` 已迁移到 `app/utils/`
- [ ] 服务层导入路径已全部更新

## Phase 9: 发货模块整合
- [ ] `base_delivery.py` 已迁移到 `app/services/delivery/`
- [ ] `secure_confirm_ultra.py` 已迁移到 `app/services/delivery/`
- [ ] `secure_freeshipping_ultra.py` 已迁移到 `app/services/delivery/`
- [ ] 发货模块导入路径已全部更新

## Phase 10: 工具模块整理
- [ ] `logging_config.py` 已迁移到 `app/utils/`
- [ ] `image_utils.py` 已迁移到 `app/utils/`
- [ ] `image_uploader.py` 已迁移到 `app/utils/`
- [ ] `browser_config.py` 已迁移到 `app/utils/`
- [ ] `message_utils.py` 已迁移到 `app/utils/`
- [ ] `ws_utils.py` 已迁移到 `app/utils/`
- [ ] `qr_login.py` 已迁移到 `app/utils/`
- [ ] `order_detail_fetcher.py` 已迁移到 `app/services/delivery/`
- [ ] `item_search/` 已迁移到 `app/services/item/`
- [ ] `xianyu_utils.py` 已迁移到 `app/utils/`
- [ ] 工具模块导入路径已全部更新

## Phase 11: 静态资源整理
- [ ] `static/pages/` 目录已创建
- [ ] 所有 `.html` 文件已移动到 `static/pages/`
- [ ] API 静态文件路径已更新

## Phase 12: 启动入口更新
- [ ] `scripts/Start.py` 已迁移到 `app/main.py`
- [ ] 兼容入口 `scripts/Start.py` 已创建
- [ ] `app/main.py` 导入路径已更新
- [ ] 部署配置启动命令已更新

## Phase 13: 统一入口
- [ ] `app/__init__.py` 已创建
- [ ] 公开 API 已定义
- [ ] 向后兼容的导入别名已创建
- [ ] 模块文档字符串已添加

## Phase 14: 测试导入更新
- [ ] `tests/conftest.py` 导入已更新
- [ ] `tests/unit/` 下测试文件导入已更新
- [ ] `tests/integration/` 下测试文件导入已更新
- [ ] `tests/e2e/` 下测试文件导入已更新
- [ ] `tests/performance/` 下测试文件导入已更新

## Phase 15: 配置文件更新
- [ ] `pytest.ini` 测试路径已更新
- [ ] `deploy/Dockerfile` 工作目录已更新
- [ ] `deploy/docker-compose.yml` 配置已更新
- [ ] `configs/config.py` 导入路径已更新

## Phase 16: 测试验证
- [ ] 单元测试全部通过
- [ ] 集成测试全部通过
- [ ] 端到端测试全部通过
- [ ] 测试覆盖率不低于重构前
- [ ] 所有失败的测试已修复

## Phase 17: 代码审查
- [ ] 导入路径一致性检查通过
- [ ] 命名规范检查通过
- [ ] 模块职责划分检查通过
- [ ] 代码质量检查通过
- [ ] 审查发现的问题已修复

## Phase 18: 最终提交
- [ ] 所有更改已检查
- [ ] 代码已提交到本地仓库
- [ ] 代码已推送到 GitHub 远程仓库

## 功能验证
- [ ] 应用可以正常启动
- [ ] API 接口可以正常访问
- [ ] WebSocket 连接正常
- [ ] 数据库操作正常
- [ ] 自动回复功能正常
- [ ] 自动发货功能正常
