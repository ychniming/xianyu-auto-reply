---
title: GitHub Actions 自动部署 - 快速设置指南
description: 15分钟完成GitHub Actions SSH自动部署配置
lastUpdated: 2026-03-25
maintainer: Doc Keeper Agent
version: 1.0.0
---

# GitHub Actions 自动部署 - 快速设置指南

## 🎯 目标

实现代码提交到 GitHub 后，自动部署到服务器（122.51.107.43）

---

## ️ 预计时间

- **首次设置**: 15-20 分钟
- **后续部署**: 自动（2-5 分钟）

---

## 📋 前置条件

- ✅ 项目已上传到 GitHub
- ✅ 新服务器可正常访问（使用 niming2.pem）
- ✅ 服务器已安装 Docker（或准备自动安装）

---

## 🚀 快速设置（5 步完成）

### 步骤 1：在服务器创建部署用户（5 分钟）

```bash
# 1. 连接服务器
ssh -i "C:\Users\Lenovo、\.ssh\niming2.pem" ubuntu@122.51.107.43

# 2. 创建部署用户
sudo adduser git --disabled-password
# 提示输入密码时直接回车（禁用密码登录）

# 3. 切换到 git 用户
sudo su - git

# 4. 创建 .ssh 目录
mkdir -p ~/.ssh && chmod 700 ~/.ssh

# 5. 生成 SSH 密钥对
ssh-keygen -t ed25519 -C "github-actions-deploy-key" -f ~/.ssh/github_actions
# 提示输入密码时直接回车（无密码短语）

# 6. 查看并复制私钥
cat ~/.ssh/github_actions
```

**重要**: 复制输出的**完整内容**（包括 `-----BEGIN...` 和 `-----END...`）

### 步骤 2：配置服务器授权（2 分钟）

```bash
# 仍在 git 用户下执行：

# 1. 将公钥加入授权列表
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# 2. 创建部署目录
sudo mkdir -p /www/wwwroot/xianyu-auto-reply
sudo chown -R git:git /www/wwwroot/xianyu-auto-reply

# 3. 退出 git 用户
exit
```

### 步骤 3：在 GitHub 配置 Secrets（3 分钟）

1. 打开你的 GitHub 仓库页面
2. 点击 **Settings** 标签
3. 左侧菜单选择 **Secrets and variables** → **Actions**
4. 点击 **New repository secret**
5. 依次添加以下 4 个 Secrets：

| Name | Value | 说明 |
|------|-------|------|
| `SERVER_SSH_KEY` | 步骤 1 复制的私钥内容 | 完整的 SSH 私钥 |
| `SERVER_HOST` | `122.51.107.43` | 服务器公网 IP |
| `SERVER_USER` | `git` | 部署用户名 |
| `DEPLOY_PATH` | `/www/wwwroot/xianyu-auto-reply` | 部署目标路径 |

### 步骤 4：提交 GitHub Actions 配置（2 分钟）

```bash
# 在本地项目根目录执行：

# 1. 确认 .github/workflows/deploy.yml 文件已存在
# （我已帮你创建好）

# 2. 提交到 GitHub
git add .github/workflows/deploy.yml
git commit -m "添加 GitHub Actions 自动部署配置"
git push origin main
```

### 步骤 5：验证部署（5 分钟）

1. 打开 GitHub 仓库页面
2. 点击 **Actions** 标签
3. 查看最近的工作流运行
4. 等待部署完成（约 2-5 分钟）
5. 访问 `http://122.51.107.43:8080` 验证

---

## ✅ 验证清单

部署成功后，你应该能看到：

- [ ] GitHub Actions 显示绿色对勾 ✅
- [ ] 访问 `http://122.51.107.43:8080` 可以打开应用
- [ ] 服务器上的部署目录有最新代码
- [ ] Docker 容器正常运行

---

## 🔍 故障排查

### 问题 1：Actions 执行失败 - SSH 连接错误

**可能原因**:
- SSH 私钥配置错误
- 服务器防火墙阻止连接
- 部署用户权限问题

**解决方法**:
```bash
# 测试本地 SSH 连接
ssh -i "C:\Users\Lenovo、\.ssh\niming2.pem" git@122.51.107.43

# 如果连接失败，检查：
# 1. 服务器安全组是否开放 22 端口
# 2. 部署用户是否存在
# 3. authorized_keys 权限是否正确
```

### 问题 2：部署后无法访问服务

**可能原因**:
- Docker 容器启动失败
- 端口被占用
- 配置文件缺失

**解决方法**:
```bash
# 1. 连接服务器查看日志
ssh -i "C:\Users\Lenovo、\.ssh\niming2.pem" git@122.51.107.43
cd /www/wwwroot/xianyu-auto-reply/deploy
sudo docker-compose logs

# 2. 检查容器状态
sudo docker-compose ps

# 3. 重启服务
sudo docker-compose down
sudo docker-compose up -d
```

### 问题 3：Actions 一直显示运行中

**可能原因**:
- 网络问题导致 SSH 连接超时
- 健康检查失败
- 脚本执行卡住

**解决方法**:
1. 在 Actions 页面查看详细日志
2. 找到卡住的步骤
3. 根据错误信息排查
4. 可以手动取消运行并重新触发

---

## 🎨 自定义配置

### 修改触发分支

编辑 `.github/workflows/deploy.yml`:

```yaml
on:
  push:
    branches:
      - main    # 改为你的分支名
      - develop # 可以添加多个分支
```

### 添加手动触发

已配置 `workflow_dispatch`，可以在 Actions 页面手动触发部署。

### 添加部署通知

在 Secrets 中添加：
- `SLACK_WEBHOOK`: Slack 通知 Webhook
- `DISCORD_WEBHOOK`: Discord 通知 Webhook

---

## 📊 部署流程可视化

```
┌──────────────┐
│  本地开发    │
│  git push    │
└─────────────┘
       │
       ▼
┌──────────────┐
│   GitHub     │
│   接收代码   │
└──────┬───────┘
       │ 自动触发
       ▼
┌──────────────┐
│   GitHub     │
│   Actions    │
│              │
│ 1. 检出代码  │
│ 2. 构建镜像  │
│ 3. SSH 连接  │
│ 4. 传输文件  │
│ 5. 重启服务  │
│ 6. 健康检查  │
└──────┬───────┘
       │ 部署完成
       ▼
┌──────────────┐
│  122.51.107. │
│     43       │
│  自动运行    │
└──────────────┘
```

---

## 🔄 日常使用

### 正常开发流程

```bash
# 1. 本地开发
# 编写代码...

# 2. 提交代码
git add .
git commit -m "实现 XX 功能"

# 3. 推送到 GitHub
git push origin main

# 4. 等待自动部署
# 打开 GitHub Actions 查看进度
# 约 2-5 分钟后部署完成
```

### 查看部署历史

访问：`https://github.com/你的用户名/xianyu-auto-reply/actions`

### 回滚到旧版本

1. 在 GitHub 找到要回滚的提交
2. 复制提交 SHA
3. 本地执行：
   ```bash
   git revert HEAD
   git push origin main
   ```
4. 会自动触发新的部署

---

## 📚 相关资源

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [ssh-deploy Action 使用](https://github.com/easingthemes/ssh-deploy)
- [ssh-action 使用](https://github.com/appleboy/ssh-action)
- [完整部署方案文档](./CI_CD_DEPLOYMENT_PLAN.md)

---

## 🆘 需要帮助？

如果遇到无法解决的问题：

1. 查看 [CI/CD 部署方案](./CI_CD_DEPLOYMENT_PLAN.md) 的详细文档
2. 查看 GitHub Actions 的完整日志
3. 检查服务器日志：`sudo docker-compose logs`
4. 使用测试连接：`ssh -v -i "niming2.pem" git@122.51.107.43`

---

**最后更新**: 2026-03-25  
**维护者**: 开发团队  
**版本**: v1.0
