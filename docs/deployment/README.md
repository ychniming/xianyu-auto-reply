---
title: 部署方案总结
description: GitHub Actions + SSH 自动化部署方案索引和快速入口
lastUpdated: 2026-03-25
maintainer: Doc Keeper Agent
version: 1.0.0
---

# 🚀 部署方案总结

## 📌 一句话推荐

**使用 GitHub Actions + SSH 实现自动化部署** - 免费、自动、可靠，最适合个人开发者和小团队。

---

## 🎯 最佳方案

### GitHub Actions + SSH 自动部署

**工作流程**:
```
本地开发 → Git 提交 → GitHub → Actions 自动部署 → VPS 服务器 (122.51.107.43)
```

**核心优势**:
- ✅ 完全免费（2000 分钟/月）
- ✅ 提交代码自动部署
- ✅ 无需手动操作
- ✅ 完整的部署日志
- ✅ 支持回滚

---

## 📚 完整文档索引

| 文档 | 用途 | 阅读时间 |
|------|------|----------|
| [**快速设置指南**](./GITHUB_ACTIONS_SETUP.md) ⭐ | **立即执行** | 5 分钟 |
| [完整方案文档](./CI_CD_DEPLOYMENT_PLAN.md) | 详细了解 | 15 分钟 |
| [方案对比](./DEPLOYMENT_COMPARISON.md) | 方案选择 | 10 分钟 |
| [GitHub Actions 配置](../../.github/workflows/deploy.yml) | 实际配置 | - |

---

## 🔥 15 分钟快速开始

### 步骤 1-3：服务器配置（10 分钟）

```bash
# 1. 连接服务器
ssh -i "C:\Users\Lenovo、\.ssh\niming2.pem" ubuntu@122.51.107.43

# 2. 创建部署用户
sudo adduser git --disabled-password
sudo su - git
mkdir -p ~/.ssh && chmod 700 ~/.ssh

# 3. 生成 SSH 密钥
ssh-keygen -t ed25519 -C "github-actions-deploy-key" -f ~/.ssh/github_actions
cat ~/.ssh/github_actions  # 复制私钥内容
```

### 步骤 4-5：GitHub 配置（5 分钟）

1. **GitHub 仓库** → Settings → Secrets and variables → Actions
2. 添加 4 个 Secrets:
   - `SERVER_SSH_KEY`: 步骤 3 复制的私钥
   - `SERVER_HOST`: `122.51.107.43`
   - `SERVER_USER`: `git`
   - `DEPLOY_PATH`: `/www/wwwroot/xianyu-auto-reply`

### 步骤 6：测试部署

```bash
# 提交代码触发自动部署
git add .
git commit -m "测试自动部署"
git push origin main

# 查看部署状态
# 访问：https://github.com/你的用户名/xianyu-auto-reply/actions
```

---

## 📊 方案对比速查

| 方案 | 成本 | 难度 | 推荐指数 |
|------|------|------|----------|
| **GitHub Actions + SSH** | 免费 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 宝塔面板 Git | 免费 | ⭐⭐ | ⭐⭐⭐⭐ |
| Jenkins | 免费+服务器 | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Docker Hub | 免费 | ⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## 🎓 核心概念

### 什么是 CI/CD？

- **CI** (Continuous Integration) = 持续集成 = 代码提交自动构建测试
- **CD** (Continuous Deployment) = 持续部署 = 自动部署到服务器

### GitHub Actions 是什么？

GitHub 内置的自动化工具，可以：
- 代码提交时自动运行
- 定时执行任务
- 手动触发工作流

### 为什么选择 GitHub Actions？

1. **免费**: 个人项目完全够用
2. **集成**: 与 GitHub 无缝集成
3. **简单**: YAML 配置文件即可
4. **强大**: 支持各种复杂场景

---

## 🔧 常用命令速查

### 本地开发

```bash
# 提交代码
git add .
git commit -m "feat: 添加 XX 功能"
git push origin main

# 查看远程仓库
git remote -v
```

### 服务器管理

```bash
# 连接服务器
ssh -i "C:\Users\Lenovo、\.ssh\niming2.pem" git@122.51.107.43

# 查看部署
cd /www/wwwroot/xianyu-auto-reply
ls -la

# 查看 Docker 状态
cd deploy
sudo docker-compose ps
sudo docker-compose logs -f
```

### 部署管理

```bash
# 手动重启服务
cd /www/wwwroot/xianyu-auto-reply/deploy
sudo docker-compose restart

# 查看日志
sudo docker-compose logs -f

# 停止服务
sudo docker-compose down
```

---

## ⚠️ 常见问题

### Q1: SSH 密钥用哪个？

**A**: 新服务器使用 `niming2.pem`（不是 `niming.pem`）

### Q2: 部署失败怎么办？

**A**: 
1. 查看 GitHub Actions 日志
2. 检查 SSH 连接是否正常
3. 确认服务器防火墙设置

### Q3: 如何回滚？

**A**: 
```bash
git revert HEAD
git push origin main
# 会自动触发新的部署
```

### Q4: 多久部署一次？

**A**: 每次 `git push` 都会触发部署

---

## 📞 获取帮助

### 文档

- 📘 [快速设置指南](./GITHUB_ACTIONS_SETUP.md) - **从这里开始**
- 📗 [完整方案文档](./CI_CD_DEPLOYMENT_PLAN.md)
- 📙 [方案对比](./DEPLOYMENT_COMPARISON.md)

### 在线资源

- GitHub Actions 文档: https://docs.github.com/actions
- GitHub 社区: https://github.community

### 调试技巧

```bash
# 测试 SSH 连接
ssh -v -i "C:\Users\Lenovo、\.ssh\niming2.pem" git@122.51.107.43

# 查看服务器日志
ssh -i "C:\Users\Lenovo、\.ssh\niming2.pem" git@122.51.107.43
cd /www/wwwroot/xianyu-auto-reply/deploy
sudo docker-compose logs -f
```

---

## ✅ 检查清单

### 部署前

- [ ] 项目已上传到 GitHub
- [ ] SSH 密钥文件存在（niming2.pem）
- [ ] 服务器可正常连接
- [ ] 已阅读快速设置指南

### 部署后

- [ ] GitHub Actions 显示成功 ✅
- [ ] 可以访问应用（http://122.51.107.43:8080）
- [ ] Docker 容器正常运行
- [ ] 日志无错误信息

---

## 🎯 下一步

### 立即行动（今天）

1. ⭐ 阅读 [快速设置指南](./GITHUB_ACTIONS_SETUP.md)
2. 🔑 配置 SSH 密钥和 GitHub Secrets
3. 🚀 测试第一次自动部署

### 本周完成

1. 📝 熟悉 GitHub Actions 使用
2. 🔍 查看部署日志
3. ✅ 验证部署结果

### 后续优化

1. 🔔 添加部署通知
2. 🌍 配置多环境部署
3. 🔄 设置自动回滚

---

## 🌟 总结

**GitHub Actions + SSH** 是目前最适合你的部署方案：

- 💰 **零成本**: 完全免费
- ⚡ **高效率**: 提交即部署
- 🛡️ **可靠**: GitHub 官方支持
- 📈 **可扩展**: 支持各种场景

**立即开始**: [快速设置指南](./GITHUB_ACTIONS_SETUP.md) - 15 分钟完成首次部署！

---

**最后更新**: 2026-03-25  
**维护者**: 开发团队  
**版本**: v1.0
