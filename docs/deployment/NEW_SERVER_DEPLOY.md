---
title: 新服务器部署指南
description: 腾讯云新服务器完整部署步骤，包括Docker安装、环境配置和Nginx反向代理
lastUpdated: 2026-03-25
maintainer: Doc Keeper Agent
version: 1.0.0
---

# 新服务器部署指南

**服务器信息：**
- **IP 地址**: 122.51.107.43
- **用户名**: ubuntu
- **SSH 密钥**: `C:\Users\Lenovo、\.ssh\niming2.pem` ⭐

---

## 快速部署步骤

### 步骤 1：连接服务器

```bash
# Windows PowerShell
ssh -i "C:\Users\Lenovo、\.ssh\niming2.pem" -o StrictHostKeyChecking=no ubuntu@122.51.107.43
```

### 步骤 2：安装 Docker 和 Docker Compose

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com | sudo bash

# 启动 Docker
sudo systemctl enable docker
sudo systemctl start docker

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

### 步骤 3：上传项目文件

**方式 A：使用 SCP 上传**

在本地 PowerShell 执行：

```powershell
# 创建远程目录
ssh -i "C:\Users\Lenovo、\.ssh\niming2.pem" ubuntu@122.51.107.43 "mkdir -p /www/wwwroot/xianyu-auto-reply"

# 上传整个项目
scp -i "C:\Users\Lenovo、\.ssh\niming2.pem" -r ./* ubuntu@122.51.107.43:/www/wwwroot/xianyu-auto-reply/
```

**方式 B：使用 Git 克隆**

```bash
# 在服务器上执行
cd /www/wwwroot
sudo git clone https://github.com/zhinianboke/xianyu-auto-reply.git
cd xianyu-auto-reply
```

### 步骤 4：配置环境变量

```bash
# 进入项目目录
cd /www/wwwroot/xianyu-auto-reply

# 创建配置目录
mkdir -p configs

# 复制配置模板
cp configs/.env.example configs/.env

# 编辑配置文件
nano configs/.env
```

**必须配置的变量：**

```bash
# 安全配置（必须修改）
JWT_SECRET_KEY=your-random-secret-key-32-chars-long
INITIAL_ADMIN_PASSWORD=your-secure-password

# OpenAI 配置（AI 回复功能）
OPENAI_API_KEY=sk-your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1

# 数据库路径
DB_PATH=/app/data/xianyu_data.db

# 日志级别
LOG_LEVEL=INFO

# 时区
TZ=Asia/Shanghai
```

### 步骤 5：启动服务

```bash
# 进入部署目录
cd /www/wwwroot/xianyu-auto-reply/deploy

# 启动 Docker 容器
sudo docker-compose up -d

# 查看启动日志
sudo docker-compose logs -f

# 按 Ctrl+C 退出日志查看
```

### 步骤 6：验证部署

```bash
# 查看容器状态
sudo docker-compose ps

# 测试健康检查
curl http://localhost:8080/health

# 查看应用日志
sudo docker-compose logs xianyu-app
```

### 步骤 7：配置 Nginx 反向代理（可选）

如果需要从外网访问：

```bash
# 使用宝塔面板配置
# 1. 登录宝塔面板
# 2. 网站 → 添加站点
# 3. 域名：your-domain.com
# 4. 反向代理：http://127.0.0.1:8080
```

**或手动配置 Nginx：**

```bash
sudo nano /etc/nginx/sites-available/xianyu
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8080/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

```bash
# 启用配置
sudo ln -s /etc/nginx/sites-available/xianyu /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
```

### 步骤 8：配置防火墙

```bash
# 如果使用 UFW
sudo ufw allow 8080/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 如果使用防火墙（云服务器）
# 在云控制台安全组中开放端口：8080, 80, 443
```

---

## 访问信息

| 项目 | 地址 |
|------|------|
| **应用访问** | http://122.51.107.43:8080 |
| **API 文档** | http://122.51.107.43:8080/docs |
| **健康检查** | http://122.51.107.43:8080/health |

**默认登录信息：**
- **用户名**: admin
- **密码**: admin123（或你在 `.env` 中设置的密码）

---

## 常用管理命令

```bash
# 进入项目目录
cd /www/wwwroot/xianyu-auto-reply

# 查看服务状态
sudo docker-compose ps

# 查看实时日志
sudo docker-compose logs -f

# 重启服务
sudo docker-compose restart

# 停止服务
sudo docker-compose down

# 重新构建并启动
sudo docker-compose up -d --build

# 备份数据
sudo cp /www/wwwroot/xianyu-auto-reply/data/xianyu_data.db /root/backups/xianyu_$(date +%Y%m%d).db
```

---

## 使用部署脚本（推荐）

项目提供了自动化部署脚本：

```bash
# 在服务器上执行
cd /www/wwwroot/xianyu-auto-reply/deploy

# 执行快速部署
sudo bash docker-deploy.sh

# 或选择交互式部署
sudo bash docker-deploy.sh init
sudo bash docker-deploy.sh start
```

---

## 常见问题

### 1. SSH 连接失败

**问题**: `Permission denied (publickey)`

**解决**:
```bash
# 检查密钥文件权限
chmod 600 "C:\Users\Lenovo、\.ssh\niming2.pem"

# 使用正确的密钥
ssh -i "C:\Users\Lenovo、\.ssh\niming2.pem" ubuntu@122.51.107.43
```

### 2. Docker 容器无法启动

**检查日志**:
```bash
sudo docker-compose logs xianyu-app
```

**常见原因**:
- 配置文件缺失
- 端口被占用
- 权限问题

### 3. 无法访问服务

**检查防火墙**:
```bash
# 查看防火墙状态
sudo ufw status

# 开放端口
sudo ufw allow 8080/tcp
```

**检查端口监听**:
```bash
sudo netstat -tlnp | grep 8080
```

### 4. 数据库连接失败

**检查数据库文件**:
```bash
ls -la /www/wwwroot/xianyu-auto-reply/data/
```

---

**相关文档**:
- [GitHub Actions 自动部署](./GITHUB_ACTIONS_SETUP.md) - 自动化 CI/CD 部署
- [部署方案总结](./README.md) - 部署方案对比

---

**最后更新**: 2026-03-25
