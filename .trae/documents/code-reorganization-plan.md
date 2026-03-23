# 代码文件整理方案

## 一、当前项目结构分析

### 1.1 现有目录结构

```
# 代码文件整理方案

## 状态：✅ 已完成

## 一、当前项目结构分析

### 1.1 现有目录结构

```
xianyu-auto-reply-main/
├── .trae/                      # Trae IDE 配置
│   ├── documents/
│   └── rules/
├── app/                        # ✅ 核心业务模块 [新增]
│   ├── __init__.py
│   ├── secure_confirm_ultra.py
│   └── secure_freeshipping_ultra.py
├── configs/                    # ✅ 配置文件目录 [新增]
│   ├── config.py
│   └── global_config.yml
├── db_manager/                 # ✅ 已重构 - 数据库模块
│   ├── __init__.py
│   ├── base.py
│   ├── cookie_repo.py
│   ├── keyword_repo.py
│   ├── user_repo.py
│   ├── notification_repo.py
│   └── card_repo.py
├── deploy/                     # ✅ 部署配置 [新增]
│   ├── Dockerfile
│   ├── Dockerfile-cn
│   ├── docker-compose.yml
│   ├── docker-compose-cn.yml
│   ├── docker-compose-simple.yml
│   ├── docker-compose-v3.yml
│   ├── entrypoint.sh
│   └── docker-deploy.*
├── docs/                       # 文档目录
├── logs/                       # 日志目录
├── nginx/                      # Nginx 配置
├── reply_server/               # ✅ 已重构 - API 服务
│   ├── __init__.py
│   └── routes/
│       ├── auth.py
│       ├── cookies.py
│       ├── keywords.py
│       ├── cards.py
│       ├── items.py
│       ├── settings.py
│       └── admin.py
├── scripts/                    # ✅ 脚本目录 [新增]
│   ├── __init__.py
│   ├── Start.py
│   └── file_log_collector.py
├── static/                     # 静态资源
├── tests/                      # ✅ 测试目录 [新增]
│   ├── __init__.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_secure_modules.py
│   │   ├── test_db_manager.py
│   │   ├── test_handlers.py
│   │   └── test_reply_server.py
│   └── integration/
│       └── __init__.py
├── utils/                      # ✅ 已重构 - 工具模块
│   ├── __init__.py
│   ├── xianyu/                 # ✅ xianyu 专用工具 [新增]
│   │   ├── __init__.py
│   │   ├── xianyu_utils.py
│   │   ├── xianyu_message_handler.py
│   │   ├── xianyu_delivery_handler.py
│   │   └── xianyu_notification_handler.py
│   ├── ws_utils.py
│   ├── message_utils.py
│   ├── image_utils.py
│   ├── image_uploader.py
│   ├── item_search.py
│   ├── order_detail_fetcher.py
│   └── qr_login.py
├── XianyuAutoAsync.py          # 闲鱼 WebSocket 核心
├── ai_reply_engine.py           # AI 回复引擎
├── cookie_manager.py            # Cookie 管理器
└── requirements.txt             # Python 依赖
```
```

### 1.2 根目录 Python 文件清单

| 文件 | 功能 | 建议操作 |
|------|------|----------|
| Start.py | 项目启动入口 | 移动到 scripts/ |
| XianyuAutoAsync.py | 闲鱼 WebSocket 核心 | 保留 |
| ai_reply_engine.py | AI 回复引擎 | 保留 |
| config.py | 配置管理 | 移动到 configs/ |
| cookie_manager.py | Cookie 管理器 | 保留 |
| db_manager.py | 数据库管理(旧) | 删除(已重构到db_manager/) |
| file_log_collector.py | 日志收集脚本 | 移动到 scripts/ |
| reply_server.py | API 服务(旧) | 删除(已重构到reply_server/) |
| secure_confirm_ultra.py | 自动确认发货 | 保留 |
| secure_freeshipping_ultra.py | 自动免拼发货 | 保留 |
| global_config.yml | 全局配置 | 移动到 configs/ |
| requirements.txt | 依赖 | 保留 |
| docker-*.yml | Docker 配置 | 移动到 deploy/ |
| Dockerfile* | Docker 镜像 | 移动到 deploy/ |
| entrypoint.sh | 容器入口 | 移动到 deploy/ |

### 1.3 测试文件清单

| 文件 | 功能 | 建议操作 |
|------|------|----------|
| test_secure_modules.py | 安全模块测试 | 移动到 tests/unit/ |
| test_db_manager.py | 数据库模块测试 | 移动到 tests/unit/ |
| test_handlers.py | Handler 模块测试 | 移动到 tests/unit/ |
| test_reply_server.py | API 服务测试 | 移动到 tests/unit/ |

## 二、目标目录结构

```
xianyu-auto-reply-main/
├── .trae/                          # Trae IDE 配置
│   ├── documents/
│   └── rules/
│
├── configs/                         # ✅ 配置文件目录
│   ├── config.py                    # 配置管理
│   ├── global_config.yml            # 全局配置
│   ├── .env.example                 # 环境变量示例
│   └── nginx.conf                   # Nginx 配置
│
├── scripts/                         # ✅ 脚本目录
│   ├── __init__.py
│   ├── Start.py                     # 项目启动入口
│   ├── file_log_collector.py        # 日志收集
│   └── generate_keywords.py          # 关键词生成(如果存在)
│
├── app/                             # ✅ 核心业务目录
│   ├── __init__.py
│   ├── XianyuAutoAsync.py          # 闲鱼 WebSocket 核心
│   ├── ai_reply_engine.py           # AI 回复引擎
│   ├── cookie_manager.py            # Cookie 管理器
│   ├── secure_confirm_ultra.py      # 自动确认发货
│   └── secure_freeshipping_ultra.py # 自动免拼发货
│
├── db_manager/                      # ✅ 数据库模块
│   ├── __init__.py
│   ├── base.py
│   ├── cookie_repo.py
│   ├── keyword_repo.py
│   ├── user_repo.py
│   ├── notification_repo.py
│   └── card_repo.py
│
├── reply_server/                    # ✅ API 服务模块
│   ├── __init__.py
│   └── routes/
│       ├── __init__.py
│       ├── auth.py
│       ├── cookies.py
│       ├── keywords.py
│       ├── cards.py
│       ├── items.py
│       ├── settings.py
│       └── admin.py
│
├── utils/                           # ✅ 工具模块
│   ├── __init__.py
│   ├── xianyu/
│   │   ├── __init__.py
│   │   ├── xianyu_utils.py
│   │   ├── xianyu_message_handler.py
│   │   ├── xianyu_delivery_handler.py
│   │   └── xianyu_notification_handler.py
│   ├── ws_utils.py
│   ├── message_utils.py
│   ├── image_utils.py
│   ├── image_uploader.py
│   ├── item_search.py
│   ├── order_detail_fetcher.py
│   └── qr_login.py
│
├── tests/                            # ✅ 测试目录
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_secure_modules.py
│   │   ├── test_db_manager.py
│   │   ├── test_handlers.py
│   │   └── test_reply_server.py
│   └── integration/
│
├── deploy/                           # ✅ 部署配置
│   ├── Dockerfile
│   ├── Dockerfile-cn
│   ├── docker-compose.yml
│   ├── docker-compose-cn.yml
│   ├── docker-compose-simple.yml
│   ├── docker-compose-v3.yml
│   ├── entrypoint.sh
│   └── docker-deploy.sh
│
├── docs/                             # 文档目录
├── logs/                             # 日志目录
├── static/                           # 静态资源
│
├── requirements.txt                  # Python 依赖
├── README.md                         # 项目说明
└── xianyu_data.db                   # SQLite 数据库
```

## 三、文件移动清单

### 3.1 需要移动的文件

| 原路径 | 新路径 | 操作 |
|--------|--------|------|
| config.py | configs/config.py | 移动 |
| global_config.yml | configs/global_config.yml | 移动 |
| Start.py | scripts/Start.py | 移动 |
| file_log_collector.py | scripts/file_log_collector.py | 移动 |
| Dockerfile | deploy/Dockerfile | 移动 |
| Dockerfile-cn | deploy/Dockerfile-cn | 移动 |
| docker-compose*.yml | deploy/ | 移动 |
| entrypoint.sh | deploy/entrypoint.sh | 移动 |
| docker-deploy.sh | deploy/docker-deploy.sh | 移动 |
| docker-deploy.bat | deploy/docker-deploy.bat | 移动 |
| nginx/nginx.conf | configs/nginx.conf | 移动 |
| test_*.py | tests/unit/ | 移动 |

### 3.2 需要删除的文件

| 文件 | 原因 |
|------|------|
| db_manager.py | 已重构到 db_manager/ 目录 |
| reply_server.py | 已重构到 reply_server/ 目录 |

### 3.3 需要创建的目录

- configs/
- scripts/
- scripts/__init__.py
- tests/
- tests/__init__.py
- tests/unit/
- tests/integration/
- app/
- app/__init__.py
- utils/xianyu/
- utils/xianyu/__init__.py
- deploy/

## 四、依赖关系图

```
scripts/Start.py
├── config.py → configs/config.py
├── cookie_manager.py → app/cookie_manager.py
├── db_manager/ → db_manager/
└── reply_server/ → reply_server/

app/XianyuAutoAsync.py
├── utils/xianyu_utils.py
├── utils/xianyu_message_handler.py
├── utils/xianyu_delivery_handler.py
├── utils/xianyu_notification_handler.py
├── secure_confirm_ultra.py → app/secure_confirm_ultra.py
├── secure_freeshipping_ultra.py → app/secure_freeshipping_ultra.py
└── db_manager/ → db_manager/

reply_server/__init__.py
├── db_manager/ → db_manager/
├── utils/qr_login.py
└── reply_server/routes/

app/ai_reply_engine.py
├── db_manager/ → db_manager/

utils/xianyu_utils.py
└── (无外部依赖)

db_manager/ → db_manager/
└── db_manager/base.py

deploy/*
└── (无代码依赖)
```

## 五、实施步骤

### 第一阶段：创建目录结构
1. 创建 configs/, scripts/, tests/, tests/unit/, tests/integration/, app/, deploy/ 目录
2. 创建必要的 __init__.py 文件

### 第二阶段：移动配置文件
1. 移动 config.py → configs/config.py
2. 移动 global_config.yml → configs/global_config.yml
3. 移动 nginx/nginx.conf → configs/nginx.conf

### 第三阶段：移动脚本文件
1. 移动 Start.py → scripts/Start.py
2. 移动 file_log_collector.py → scripts/file_log_collector.py

### 第四阶段：移动业务模块
1. 移动 secure_*.py → app/
2. 创建 utils/xianyu/ 子目录并移动 handler 文件

### 第五阶段：移动部署文件
1. 移动 Dockerfile* → deploy/
2. 移动 docker-compose* → deploy/
3. 移动 entrypoint.sh → deploy/
4. 移动 docker-deploy.* → deploy/

### 第六阶段：移动测试文件
1. 移动 test_*.py → tests/unit/

### 第七阶段：清理和验证
1. 删除旧的 db_manager.py 和 reply_server.py
2. 更新所有导入路径
3. 运行测试验证

## 六、注意事项

1. **保持向后兼容**：旧的导入路径通过符号链接或重导出保持兼容
2. **更新 Docker 配置**：确保 Dockerfile 和 docker-compose 指向新的目录结构
3. **更新启动脚本**：确保 entrypoint.sh 和 docker-deploy.sh 使用新路径
4. **更新文档**：更新 README.md 和其他文档中的路径引用
