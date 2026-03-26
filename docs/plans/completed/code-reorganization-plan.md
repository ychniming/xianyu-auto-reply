---
title: 代码文件整理方案
description: 项目目录结构重组和文件整理方案
lastUpdated: 2026-03-25
status: completed
priority: P0
---

# 代码文件整理方案

[返回索引](../INDEX.md)

## 状态：✅ 已完成

## 一、目标目录结构

```
xianyu-auto-reply-main/
├── .trae/                          # Trae IDE 配置
├── configs/                         # ✅ 配置文件目录
│   ├── config.py                    # 配置管理
│   ├── global_config.yml            # 全局配置
│   └── .env.example                 # 环境变量示例
├── scripts/                         # ✅ 脚本目录
│   ├── __init__.py
│   └── Start.py                     # 项目启动入口
├── app/                             # ✅ 核心业务目录
│   ├── __init__.py
│   ├── XianyuAutoAsync.py          # 闲鱼 WebSocket 核心
│   ├── ai_reply_engine.py           # AI 回复引擎
│   └── cookie_manager.py            # Cookie 管理器
├── db_manager/                      # ✅ 数据库模块
│   ├── __init__.py
│   ├── base.py
│   ├── cookie_repo.py
│   ├── keyword_repo.py
│   ├── user_repo.py
│   ├── notification_repo.py
│   └── card_repo.py
├── reply_server/                    # ✅ API 服务模块
│   ├── __init__.py
│   └── routes/
│       ├── auth.py
│       ├── cookies.py
│       ├── keywords.py
│       ├── cards.py
│       ├── items.py
│       ├── settings.py
│       └── admin.py
├── utils/                           # ✅ 工具模块
│   ├── __init__.py
│   └── xianyu/                      # ✅ xianyu 专用工具
│       ├── xianyu_utils.py
│       ├── xianyu_message_handler.py
│       ├── xianyu_delivery_handler.py
│       └── xianyu_notification_handler.py
├── tests/                           # ✅ 测试目录
│   ├── unit/
│   └── integration/
├── deploy/                          # ✅ 部署配置
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── entrypoint.sh
├── docs/                            # 文档目录
├── static/                          # 静态资源
└── requirements.txt                 # Python 依赖
```

## 二、已完成的文件移动

| 原路径 | 新路径 | 状态 |
|--------|--------|------|
| config.py | configs/config.py | ✅ |
| global_config.yml | configs/global_config.yml | ✅ |
| Start.py | scripts/Start.py | ✅ |
| Dockerfile | deploy/Dockerfile | ✅ |
| docker-compose*.yml | deploy/ | ✅ |
| entrypoint.sh | deploy/entrypoint.sh | ✅ |
| test_*.py | tests/unit/ | ✅ |

## 三、已删除的冗余文件

| 文件 | 原因 |
|------|------|
| db_manager.py (旧) | 已重构到 db_manager/ 目录 |
| reply_server.py (旧) | 已重构到 reply_server/ 目录 |
| static/pages/*.html | 与根目录重复 |
| static/xianyu_js_version_2.js | 未被引用 |

## 四、依赖关系

```
scripts/Start.py
├── configs/config.py
├── app/cookie_manager.py
├── db_manager/
└── reply_server/

app/XianyuAutoAsync.py
├── utils/xianyu/
└── db_manager/

reply_server/
├── db_manager/
└── utils/
```

## 五、兼容性保证

- 旧的导入路径通过 `__init__.py` 重导出保持兼容
- 所有现有 API 端点继续正常工作
- Docker 配置已更新指向新目录

## 相关文档

- [代码可维护性优化计划](./code-maintainability-plan.md)
- [架构概览](../../architecture/overview.md)
- [开发指南](../../guides/development.md)

---

**维护者：** Doc Keeper Agent  
**最后更新：** 2026-03-25
