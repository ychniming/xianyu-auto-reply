---
title: 智能体入口
description: AI 助手快速理解项目的入口文档，提供核心知识地图
lastUpdated: 2026-03-26
maintainer: Doc Keeper Agent
maxLines: 100
---

# 智能体入口 (AGENTS.md)

> 本文档为 AI 助手提供项目核心知识，遵循 OpenAI Codex 工程实践，控制在 100 行以内。

## 项目是什么

闲鱼自动回复系统 - 企业级闲鱼消息自动处理平台，支持智能回复、自动发货、多账号管理。

## 技术栈

`FastAPI` `SQLite` `OpenAI` `Playwright` `WebSocket` `Docker`

## 核心模块

| 模块 | 文件 | 职责 |
|------|------|------|
| 启动入口 | `scripts/Start.py` | 初始化服务 |
| WebSocket 核心 | `XianyuAutoAsync.py` | 消息收发、自动回复 |
| Web 服务 | `reply_server.py` | RESTful API、认证 |
| Cookie 管理 | `cookie_manager.py` | 多账号调度 |
| 数据库 | `db_manager.py` | SQLite 操作 |
| AI 回复 | `ai_reply_engine.py` | OpenAI 集成 |

## 目录结构

```
├── configs/          # 配置文件
├── deploy/           # Docker 部署
├── docs/             # 文档
├── scripts/          # 启动脚本
├── static/           # 前端资源
├── utils/            # 工具函数
└── *.py              # 核心模块
```

## 快速查找

| 我想知道... | 去哪里看 |
|-------------|----------|
| 系统架构 | [architecture/overview.md](./docs/architecture/overview.md) |
| 如何部署 | [guides/deployment.md](./docs/guides/deployment.md) |
| CI/CD 自动化部署 | [deployment/README.md](./docs/deployment/README.md) |
| API 接口 | [reference/api.md](./docs/reference/api.md) |
| 编码规范 | [team/conventions.md](./docs/team/conventions.md) |
| 产品原则 | [team/principles.md](./docs/team/principles.md) |

## 关键约定

1. **代码规范**：Python 大驼峰类名，小写下划线函数名
2. **数据库**：SQLite，通过 `db_manager.py` 访问
3. **认证**：JWT Token，存储在 `users` 表
4. **日志**：loguru，按日期分割到 `logs/` 目录
5. **配置**：环境变量 + `configs/config.py`

## 常见任务

```bash
# 启动服务
python scripts/Start.py

# Docker 部署
cd deploy && docker-compose up -d

# 运行测试（所有）
pytest tests/ -n auto

# 运行单元测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v

# 运行带报告的测试
pytest tests/ --html=reports/report.html --self-contained-html

# 生成Allure报告
allure serve reports/allure-results

# 查看日志
tail -f logs/xianyu_$(date +%Y-%m-%d).log
```

## 测试框架

| 类型 | 工具 | 说明 |
|------|------|------|
| 单元测试 | `pytest` + `pytest-xdist` | 并行执行 |
| API测试 | `FastAPI TestClient` | 集成测试 |
| E2E测试 | `Playwright` | 浏览器自动化 |
| 报告 | `Allure` + `pytest-html` | 可视化报告 |

## 测试目录

```
tests/
├── conftest.py           # pytest配置和fixtures
├── unit/                 # 单元测试
├── integration/           # 集成测试
├── performance/           # 性能测试
├── e2e/                  # 端到端测试
└── ai/                   # AI辅助测试
```

## 重要提醒

- Cookie 有效期约 7 天，需定期刷新
- WebSocket 断开后自动重连
- AI 回复需要配置 OpenAI API Key
- 数据库文件：`data/xianyu_data.db`
- 测试覆盖率目标：≥80%

---

**下一步：** 根据任务类型，查阅对应的详细文档。
