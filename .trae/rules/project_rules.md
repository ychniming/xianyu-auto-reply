# 闲鱼自动回复系统 - 项目规则文档

## 生产环境信息

| 项目 | 内容 |
|------|------|
| **服务器 IP** | 43.134.89.158 |
| **服务器位置** | 新加坡 |
| **操作系统** | Ubuntu 20.04 |
| **宝塔面板** | https://43.134.89.158:18788/590183d8 |
| **域名** | xianyu.niming.cyou |
| **项目路径** | /www/wwwroot/xianyu-auto-reply |
| **数据路径** | /www/wwwroot/data |
| **主要服务** | Docker (闲鱼自动回复)、Xray、RustDesk、Nginx |

### SSH 连接

```bash
# Windows PowerShell 连接
ssh -i "C:\Users\Lenovo、\.ssh\niming.pem" -o StrictHostKeyChecking=no ubuntu@43.134.89.158

# Linux/macOS 连接
ssh -i ~/.ssh/niming.pem ubuntu@43.134.89.158
```

---

## 文档目录

本规则文档已拆分为多个子文档，便于阅读和维护：

| 文档 | 说明 |
|------|------|
| [01-project-overview.md](./01-project-overview.md) | 项目概述 - 项目简介、技术栈、项目目标 |
| [02-architecture.md](./02-architecture.md) | 项目架构说明 - 系统架构图、目录结构、核心模块、数据库设计 |
| [03-code-standards.md](./03-code-standards.md) | 代码规范 - Python/JavaScript规范、文件大小限制 |
| [04-development-process.md](./04-development-process.md) | 开发流程 - 分支管理、工作流、Commit规范、代码审查 |
| [05-testing-standards.md](./05-testing-standards.md) | 测试标准 - 测试类型、单元测试规范、测试执行 |
| [06-deployment-process.md](./06-deployment-process.md) | 部署流程 - 部署环境、检查清单、部署命令、CI/CD |
| [07-operations-specifications.md](./07-operations-specifications.md) | 运维规范 - 日常任务、监控告警、日志管理、容量规划 |
| [08-security-policy.md](./08-security-policy.md) | 安全策略 - 认证授权、数据安全、API安全、安全检查清单 |
| [09-documentation-management.md](./09-documentation-management.md) | 文档管理要求 - 文档类型、文档规范、版本管理 |
| [10-team-collaboration.md](./10-team-collaboration.md) | 团队协作机制 - 角色分工、沟通机制、代码协作、问题处理 |
| [appendix.md](./appendix.md) | 附录 - 常用命令、环境变量、相关链接、端口说明 |

---

**文档版本**: v1.2  
**更新时间**: 2026-03-16  
**适用服务器**: 43.134.89.158 (新加坡)  
**维护团队**: 开发团队
