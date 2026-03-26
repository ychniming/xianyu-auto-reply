---
title: 闲鱼自动回复系统 - 知识库索引
description: 文档知识库总入口，提供完整的文档导航和快速检索
lastUpdated: 2026-03-25
maintainer: Doc Keeper Agent
---

# 知识库索引

## 快速导航

| 区域 | 用途 | 入口文档 |
|------|------|----------|
| **智能体入口** | AI 助手快速理解项目 | [AGENTS.md](../AGENTS.md) |
| **架构文档** | 系统设计和技术决策 | [architecture/overview.md](./architecture/overview.md) |
| **操作指南** | 部署、运维、开发指南 | [guides/deployment.md](./guides/deployment.md) |
| **CI/CD 部署** | GitHub Actions 自动化 | [deployment/README.md](./deployment/README.md) |
| **执行计划** | 功能开发和技术债务 | [plans/active/](./plans/active/) |
| **参考资料** | API 文档和配置参考 | [reference/api.md](./reference/api.md) |
| **团队知识** | 原则、规范和文化 | [team/principles.md](./team/principles.md) |

## 文档结构

```
docs/
├── INDEX.md              # 本文件 - 知识库索引
├── architecture/         # 架构文档
│   ├── overview.md       # 系统架构概览
│   ├── domains.md        # 领域划分
│   └── layers.md         # 分层设计
├── guides/               # 操作指南
│   ├── deployment.md     # 部署指南
│   ├── operations.md     # 运维指南
│   └── development.md    # 开发指南
├── deployment/           # CI/CD 部署（GitHub Actions）
│   ├── README.md         # 部署方案总结
│   ├── CI_CD_DEPLOYMENT_PLAN.md  # 完整方案
│   ├── DEPLOYMENT_COMPARISON.md   # 方案对比
│   ├── GITHUB_ACTIONS_SETUP.md    # 快速设置
│   └── NEW_SERVER_DEPLOY.md       # 新服务器手动部署
├── plans/                # 执行计划
│   ├── active/           # 进行中的计划
│   ├── completed/        # 已完成的计划
│   └── tech-debt/        # 技术债务
├── reference/            # 参考资料
│   ├── api.md            # API 参考
│   ├── config.md         # 配置参考
│   ├── specs/            # 规格文档
│   ├── import-validation-report.md  # 导入验证报告
│   └── deletion-log.md   # 清理日志
├── team/                 # 团队知识
│   ├── principles.md     # 产品原则
│   ├── conventions.md    # 工程规范
│   └── culture.md        # 团队文化
└── archive/              # 归档文档
    └── v1/               # 旧版文档
```

## 核心概念

### 系统定位

闲鱼自动回复系统是一个功能完整的闲鱼消息自动处理平台，支持：
- 多用户、多账号管理
- 智能回复和自动发货
- 商品管理和订单处理
- Web 管理界面

### 技术栈

| 类别 | 技术 |
|------|------|
| 后端 | FastAPI + Uvicorn |
| 数据库 | SQLite |
| AI 引擎 | OpenAI SDK |
| 浏览器自动化 | Playwright |
| 前端 | Bootstrap 5 |
| 容器化 | Docker |

## 文档质量标准

| 维度 | A 级 | B 级 | C 级 | D 级 |
|------|------|------|------|------|
| 新鲜度 | <7天 | <30天 | <90天 | >90天 |
| 准确性 | 100% | >90% | >75% | <75% |
| 覆盖率 | 完整 | 主要覆盖 | 部分覆盖 | 缺失 |
| 可读性 | 优秀 | 良好 | 一般 | 差 |

## 相关资源

- [项目规则](../.trae/rules/project_rules.md) - Trae IDE 项目配置
- [README.md](../README.md) - 项目说明
- [归档文档](./archive/v1/) - 历史版本

---

**维护者：** Doc Keeper Agent  
**最后更新：** 2026-03-25
