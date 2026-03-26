---
title: CI/CD 自动化部署方案
description: 闲鱼自动回复系统GitHub Actions + SSH全自动化部署方案
lastUpdated: 2026-03-25
maintainer: Doc Keeper Agent
version: 1.0.0
---

# 闲鱼自动回复系统 - CI/CD 自动化部署方案

## 📋 方案对比

### 方案一：GitHub Actions + SSH 部署（推荐 ⭐⭐⭐⭐⭐）

**工作流程**:
```
本地开发 → Git 提交 → GitHub → Actions 自动部署 → VPS 服务器
```

**优点**:
- ✅ 免费（GitHub Actions 提供 2000 分钟/月 免费额度）
- ✅ 自动化程度高
- ✅ 无需额外服务器
- ✅ 与代码托管无缝集成
- ✅ 支持回滚到历史版本
- ✅ 完整的部署日志

**缺点**:
- ⚠️ 需要配置 SSH 密钥
- ⚠️ 首次设置稍复杂

**适用场景**: 个人开发者、小团队、初创项目

---

### 方案二：宝塔面板 + Git 部署（简单 ⭐⭐⭐⭐）

**工作流程**:
```
本地开发 → Git 提交 → GitHub → 宝塔面板 Git 插件 → 自动拉取部署
```

**优点**:
- ✅ 图形化界面，操作简单
- ✅ 支持 Webhook 自动触发
- ✅ 可以查看部署日志
- ✅ 支持多环境管理

**缺点**:
- ⚠️ 需要安装宝塔面板
- ⚠️ 功能相对基础

**适用场景**: 习惯图形化操作、已有宝塔面板

---

### 方案三：Jenkins CI/CD（企业 ⭐⭐⭐）

**工作流程**:
```
本地开发 → Git 提交 → Jenkins → 构建 → 部署 → VPS
```

**优点**:
- ✅ 功能最强大
- ✅ 支持复杂部署流程
- ✅ 插件生态丰富

**缺点**:
- ⚠️ 需要额外服务器运行 Jenkins
- ⚠️ 配置复杂
- ⚠️ 学习曲线陡峭

**适用场景**: 企业级项目、多环境部署

---

### 方案四：Docker Hub + 远程部署（现代 ⭐⭐⭐⭐）

**工作流程**:
```
本地开发 → 构建 Docker 镜像 → Docker Hub → 服务器拉取 → 运行
```

**优点**:
- ✅ 环境一致性最好
- ✅ 支持多架构
- ✅ 回滚方便
- ✅ 适合微服务

**缺点**:
- ⚠️ 需要 Docker 知识
- ⚠️ 镜像推送较慢

**适用场景**: 微服务架构、多服务器部署

---

## 🎯 推荐方案：GitHub Actions + SSH

基于你的需求和技术栈，我推荐使用 **GitHub Actions + SSH** 方案。

### 为什么选择这个方案？

1. **成本低**: 完全免费
2. **效率高**: 提交代码自动部署
3. **可靠性**: GitHub 官方支持，稳定性好
4. **易维护**: 配置文件在代码仓库中
5. **扩展性**: 支持多服务器、多环境

---

## 🚀 实施步骤

### 步骤 1：在服务器上创建部署用户

```bash
# 连接到新服务器
ssh -i "C:\Users\Lenovo、\.ssh\niming2.pem" ubuntu@122.51.107.43

# 创建专用部署用户（使用 git 用户名）
sudo adduser git --disabled-password

# 切换到该用户
sudo su - git

# 创建 .ssh 目录
mkdir -p ~/.ssh && chmod 700 ~/.ssh
```

### 步骤 2：生成 SSH 密钥对

```bash
# 在服务器上生成密钥
ssh-keygen -t ed25519 -C "github-actions-deploy-key" -f ~/.ssh/github_actions

# 查看私钥内容（用于配置 GitHub Secrets）
cat ~/.ssh/github_actions
```

复制输出的完整内容（包括 `-----BEGIN OPENSSH PRIVATE KEY-----` 和 `-----END OPENSSH PRIVATE KEY-----`）

### 步骤 3：配置服务器授权

```bash
# 将公钥加入授权列表
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 644 ~/.ssh/github_actions.pub

# 创建部署目录
sudo mkdir -p /www/wwwroot/xianyu-auto-reply
sudo chown -R git:git /www/wwwroot/xianyu-auto-reply

# 退出 git 用户
exit
```

### 步骤 4：配置 SSH 服务（可选，增强安全性）

```bash
# 编辑 SSH 配置
sudo nano /etc/ssh/sshd_config

# 确保以下配置项正确：
PubkeyAuthentication yes
PasswordAuthentication no
AllowUsers ubuntu git

# 重启 SSH 服务
sudo systemctl restart sshd
```

### 步骤 5：在 GitHub 配置 Secrets

1. 打开你的 GitHub 仓库
2. 进入 **Settings** → **Secrets and variables** → **Actions**
3. 点击 **New repository secret**
4. 添加以下 Secrets：

| Name | Value |
|------|-------|
| `SERVER_SSH_KEY` | 步骤 2 中复制的私钥内容 |
| `SERVER_HOST` | `122.51.107.43` |
| `SERVER_USER` | `git` |
| `DEPLOY_PATH` | `/www/wwwroot/xianyu-auto-reply` |

### 步骤 6：创建 GitHub Actions 工作流

在项目根目录创建文件：`.github/workflows/deploy.yml`

```yaml
name: Deploy to VPS

on:
  push:
    branches:
      - main  # 推送到 main 分支时触发
  pull_request:
    branches:
      - main  # PR 到 main 分支时也触发（可选）

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
        
      - name: Build Docker image
        run: |
          cd deploy
          docker-compose build --no-cache
          
      - name: Deploy to Server via SSH
        uses: easingthemes/ssh-deploy@v4
        with:
          SSH_PRIVATE_KEY: ${{ secrets.SERVER_SSH_KEY }}
          REMOTE_HOST: ${{ secrets.SERVER_HOST }}
          REMOTE_USER: ${{ secrets.SERVER_USER }}
          SOURCE: "."
          TARGET: ${{ secrets.DEPLOY_PATH }}
          ARGS: "-avz --delete"
          EXCLUDE: "/.git/, /node_modules/, /.env, /logs/, /data/, /.github/"
          
      - name: Restart Services on Server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: |
            cd ${{ secrets.DEPLOY_PATH }}/deploy
            sudo docker-compose pull
            sudo docker-compose up -d --build
            sudo docker-compose logs -f
```

### 步骤 7：测试部署

```bash
# 本地提交代码
git add .
git commit -m "测试自动部署"
git push origin main

# 查看 GitHub Actions 执行状态
# 访问：https://github.com/你的用户名/xianyu-auto-reply/actions
```

---

## 📁 完整的项目结构

```
xianyu-auto-reply/
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions 配置
├── deploy/
│   ├── docker-compose.yml      # Docker Compose 配置
│   ├── quick-deploy.sh         # 快速部署脚本
│   └── ...
├── src/                        # 源代码
├── configs/
│   └── .env.example            # 配置模板
├── docs/                       # 文档
├── .gitignore                  # Git 忽略文件
└── README.md                   # 项目说明
```

---

## 🔧 优化建议

### 1. 多环境部署

创建多个工作流文件：

```
.github/workflows/
├── deploy-dev.yml    # 开发环境
├── deploy-staging.yml # 测试环境
└── deploy-prod.yml   # 生产环境
```

### 2. 添加健康检查

```yaml
- name: Health Check
  uses: appleboy/ssh-action@master
  with:
    host: ${{ secrets.SERVER_HOST }}
    username: ${{ secrets.SERVER_USER }}
    key: ${{ secrets.SERVER_SSH_KEY }}
    script: |
      curl -f http://localhost:8080/health || exit 1
      sleep 5
      curl -f http://localhost:8080/health || exit 1
```

### 3. 添加回滚功能

```yaml
- name: Backup Current Version
  uses: appleboy/ssh-action@master
  with:
    host: ${{ secrets.SERVER_HOST }}
    username: ${{ secrets.SERVER_USER }}
    key: ${{ secrets.SERVER_SSH_KEY }}
    script: |
      cd ${{ secrets.DEPLOY_PATH }}
      tar -czf /root/backups/backup-$(date +%Y%m%d-%H%M%S).tar.gz .
```

### 4. 添加通知功能

```yaml
- name: Notify Deployment Status
  if: always()
  uses: rtCamp/action-slack-notify@v2
  env:
    SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
    SLACK_MESSAGE: "Deployment ${{ job.status }}"
```

---

## 🆘 常见问题

### Q1: GitHub Actions 执行失败怎么办？

**解决**:
1. 查看 Actions 标签页的详细日志
2. 检查 SSH 密钥配置是否正确
3. 确认服务器防火墙开放了 SSH 端口
4. 测试本地 SSH 连接是否正常

### Q2: 部署后服务没有更新？

**解决**:
1. 检查 Docker 容器是否重启
2. 查看 Docker 镜像是否重新构建
3. 确认部署目录权限正确
4. 检查 `.gitignore` 是否排除了必要文件

### Q3: 如何手动触发部署？

**方法**:
1. 在 GitHub Actions 页面找到工作流
2. 点击 "Run workflow" 按钮
3. 选择分支并确认运行

### Q4: 部署太慢怎么办？

**优化**:
1. 使用 Docker 镜像缓存
2. 减少不必要的文件传输
3. 使用增量部署（rsync）
4. 优化 Dockerfile 构建层

---

## 📊 部署流程图

```
┌─────────────┐
│  本地开发   │
│  编写代码   │
└──────┬──────┘
       │ git push
       ▼
┌─────────────┐
│   GitHub    │
│  接收代码   │
└──────┬──────┘
       │ 触发 Actions
       ▼
┌─────────────┐
│   GitHub    │
│   Actions   │
│ 1. 构建镜像 │
│ 2. SSH 连接 │
│ 3. 传输文件 │
│ 4. 重启服务 │
└────────────┘
       │ 部署完成
       ▼
┌─────────────┐
│  VPS 服务器  │
│ 122.51.107. │
│     43      │
│ 自动运行    │
└─────────────┘
```

---

## 🎯 下一步行动

1. **立即执行**（30 分钟）:
   - [ ] 在服务器创建部署用户
   - [ ] 生成 SSH 密钥对
   - [ ] 配置 GitHub Secrets

2. **本周完成**（1 小时）:
   - [ ] 创建 GitHub Actions 工作流
   - [ ] 测试自动部署
   - [ ] 验证部署结果

3. **后续优化**:
   - [ ] 添加健康检查
   - [ ] 配置多环境部署
   - [ ] 添加部署通知

---

## 参考资源

- [GitHub Actions 官方文档](https://docs.github.com/en/actions)
- [ssh-deploy Action](https://github.com/easingthemes/ssh-deploy)
- [ssh-action](https://github.com/appleboy/ssh-action)
- [Docker Compose 部署最佳实践](https://docs.docker.com/compose/production/)
- [部署指南](../guides/deployment.md)
- [部署文档](./)

---

**创建时间**: 2026-03-25  
**维护者**: 开发团队  
**版本**: v1.0
