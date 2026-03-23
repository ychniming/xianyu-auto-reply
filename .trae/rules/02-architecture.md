# 项目架构说明

[返回主目录](./project_rules.md)

---

## 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      用户界面层                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Web管理界面 │  │  登录/注册   │  │  数据管理   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API服务层                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              FastAPI (reply_server.py)               │   │
│  │  • RESTful API  • JWT认证  • 请求限流  • 日志记录    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      业务逻辑层                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │CookieManager│  │ AIReplyEngine│  │自动发货模块 │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ XianyuLive  │  │ 商品管理    │  │ 用户管理    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据访问层                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              DBManager (db_manager.py)               │   │
│  │  • SQLite操作  • 数据迁移  • 事务管理  • 缓存       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      外部服务层                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 闲鱼WebSocket│  │ 闲鱼API    │  │ OpenAI API  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

---

## 2.2 目录结构

```
xianyu-auto-reply-main/
├── .trae/                          # Trae IDE 配置目录
│   ├── rules/                      # 项目规则
│   │   └── project_rules.md        # 本文件
│   └── specs/                      # 规格文档
│
├── configs/                        # 配置文件目录
│   ├── .env                        # 环境变量（敏感信息，不提交）
│   ├── .env.example                # 环境变量示例
│   ├── config.py                   # 配置管理类
│   ├── global_config.yml           # 全局配置
│   └── *.conf                      # Nginx配置文件
│
├── deploy/                         # 部署文件目录
│   ├── Dockerfile                  # Docker镜像构建
│   ├── Dockerfile-cn               # 国内加速版
│   ├── docker-compose.yml          # Docker Compose配置
│   ├── docker-compose-cn.yml       # 国内版
│   ├── entrypoint.sh               # 容器入口脚本
│   └── nginx.conf                  # Nginx配置模板
│
├── docs/                           # 文档目录
│   ├── DEPLOY_README.md            # 部署指南
│   ├── OPERATIONS_GUIDE.md         # 运维指南
│   ├── server-update-guide.md      # 更新指南
│   └── *.md                        # 其他文档
│
├── logs/                           # 日志目录
│   └── xianyu_YYYY-MM-DD.log       # 按日期分割的日志
│
├── backups/                        # 备份目录
│   ├── *.bak                       # 备份文件
│   └── xianyu_data.db              # 数据库备份
│
├── scripts/                        # 脚本目录
│   ├── Start.py                    # 项目启动入口
│   ├── update-server.sh            # 服务器更新脚本
│   ├── generate_keywords.py        # 关键词生成
│   └── file_log_collector.py       # 日志收集
│
├── static/                         # 静态资源目录
│   ├── css/                        # 样式文件
│   ├── js/                         # JavaScript文件
│   │   ├── app.js                  # 主入口
│   │   ├── api.js                  # API模块
│   │   ├── auth.js                 # 认证模块
│   │   ├── utils.js                # 工具函数
│   │   └── modules/                # 功能模块
│   ├── lib/                        # 第三方库
│   └── *.html                      # HTML页面
│
├── utils/                          # 工具函数目录
│   ├── xianyu_utils.py             # 闲鱼API工具
│   ├── message_utils.py            # 消息处理工具
│   ├── image_utils.py              # 图片处理工具
│   ├── image_uploader.py           # 图片上传工具
│   ├── qr_login.py                 # 二维码登录
│   ├── ws_utils.py                 # WebSocket工具
│   ├── item_search.py              # 商品搜索
│   └── order_detail_fetcher.py     # 订单详情获取
│
├── XianyuAutoAsync.py              # 闲鱼WebSocket核心
├── ai_reply_engine.py              # AI回复引擎
├── cookie_manager.py               # Cookie管理器
├── db_manager.py                   # 数据库管理
├── reply_server.py                 # Web服务器
├── secure_confirm_ultra.py         # 自动确认发货
├── secure_freeshipping_ultra.py    # 自动免拼发货
├── requirements.txt                # Python依赖
├── README.md                       # 项目说明
└── PROJECT_STRUCTURE.md            # 项目结构说明
```

---

## 2.3 核心模块说明

| 模块 | 文件 | 职责 |
|------|------|------|
| 启动入口 | scripts/Start.py | 初始化CookieManager和FastAPI服务 |
| WebSocket核心 | XianyuAutoAsync.py | 闲鱼消息收发、自动回复、自动发货 |
| Web服务 | reply_server.py | RESTful API、用户认证、管理界面 |
| Cookie管理 | cookie_manager.py | 多账号管理、任务调度 |
| 数据库管理 | db_manager.py | SQLite操作、数据迁移、缓存 |
| AI回复 | ai_reply_engine.py | OpenAI集成、意图识别、智能回复 |
| 自动发货 | secure_*_ultra.py | 自动确认发货、免拼发货 |

---

## 2.4 数据库设计

### 核心表结构

```sql
-- 用户表
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT UNIQUE,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cookie账号表
CREATE TABLE cookies (
    id TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    user_id INTEGER,
    enabled INTEGER DEFAULT 1,
    auto_confirm INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 关键词表
CREATE TABLE keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cookie_id TEXT NOT NULL,
    keyword TEXT NOT NULL,
    reply TEXT NOT NULL,
    item_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cookie_id) REFERENCES cookies(id)
);

-- 发货规则表
CREATE TABLE delivery_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cookie_id TEXT NOT NULL,
    item_keyword TEXT,
    delivery_content TEXT,
    card_data TEXT,
    enabled INTEGER DEFAULT 1,
    FOREIGN KEY (cookie_id) REFERENCES cookies(id)
);

-- 操作日志表
CREATE TABLE operation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    details TEXT,
    ip_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```
