---
title: 部署指南
description: 闲鱼自动回复系统的部署方式和配置说明
lastUpdated: 2026-03-25
maintainer: Doc Keeper Agent
---

# 部署指南

[返回索引](../INDEX.md)

## 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|---------|---------|
| 操作系统 | Ubuntu 18.04+ | Ubuntu 20.04 LTS |
| CPU | 2核 | 4核+ |
| 内存 | 2GB | 4GB+ |
| 存储 | 10GB | 20GB+ SSD |
| Python | 3.11+ | 3.11+ |
| Docker | 20.10+ | 24.0+ |

## 部署方式

### 方式一：Docker 部署（推荐）

#### 1. 安装 Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | bash
systemctl enable docker
systemctl start docker

# 安装 Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

#### 2. 配置环境变量

```bash
# 创建配置目录
mkdir -p /www/wwwroot/xianyu-auto-reply
cd /www/wwwroot/xianyu-auto-reply

# 复制配置模板
cp configs/.env.example configs/.env

# 编辑配置
nano configs/.env
```

**必须配置项：**

```bash
# 安全配置（必须修改）
JWT_SECRET_KEY=your-random-secret-key-32-chars-long
INITIAL_ADMIN_PASSWORD=your-secure-password

# OpenAI 配置（AI 回复功能）
OPENAI_API_KEY=sk-your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
```

#### 3. 启动服务

```bash
cd deploy
docker-compose up -d
```

#### 4. 验证部署

```bash
# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 测试访问
curl http://localhost:8080/health
```

### 方式二：本地开发部署

#### 1. 克隆项目

```bash
git clone https://github.com/zhinianboke/xianyu-auto-reply.git
cd xianyu-auto-reply
```

#### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows
```

#### 3. 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. 安装 Playwright

```bash
playwright install chromium
```

#### 5. 配置环境变量

```bash
cp configs/.env.example configs/.env
# 编辑 configs/.env
```

#### 6. 启动服务

```bash
python scripts/Start.py
```

## Nginx 配置

### 反向代理配置

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

### HTTPS 配置

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

## 数据目录

```
data/
├── xianyu_data.db      # SQLite 数据库
├── cookies/            # Cookie 备份
├── logs/               # 日志文件
└── backups/            # 数据备份
```

## 常见问题

### 端口被占用

```bash
# 查看端口占用
lsof -i :8080

# 修改端口
# 编辑 docker-compose.yml 或 configs/config.py
```

### 权限问题

```bash
# 修复数据目录权限
chown -R 1000:1000 data/
```

### 容器无法启动

```bash
# 查看详细日志
docker-compose logs --tail 100

# 重建容器
docker-compose down
docker-compose up -d --build
```

## 更新部署

```bash
# 拉取最新代码
git pull

# 重建并重启
cd deploy
docker-compose down
docker-compose up -d --build
```

## 相关文档

- [运维指南](./operations.md)
- [配置参考](../reference/config.md)
- [归档文档](../archive/v1/DEPLOY_README.md)

## 新服务器部署（122.51.107.43）

### 快速部署（推荐）

在 Windows 本地执行：

```powershell
# 使用 PowerShell 脚本一键部署
cd d:\我的\创业\xianyu-auto-reply-main
.\deploy\deploy-to-new-server.ps1
```

### 手动部署

1. **连接服务器**
   ```bash
   ssh -i "C:\Users\Lenovo、\.ssh\niming2.pem" ubuntu@122.51.107.43
   ```

2. **安装 Docker**
   ```bash
   curl -fsSL https://get.docker.com | sudo bash
   sudo systemctl start docker
   ```

3. **上传项目**
   ```bash
   # 本地执行
   scp -i "C:\Users\Lenovo、\.ssh\niming2.pem" -r ./* ubuntu@122.51.107.43:/www/wwwroot/xianyu-auto-reply/
   ```

4. **执行部署脚本**
   ```bash
   cd /www/wwwroot/xianyu-auto-reply/deploy
   sudo bash quick-deploy.sh deploy
   ```

### 访问地址

- **应用**: http://122.51.107.43:8080
- **API**: http://122.51.107.43:8080/docs

详细部署指南请参考：[新服务器部署文档](../../deploy/NEW_SERVER_DEPLOY.md)

---

**维护者：** Doc Keeper Agent  
**最后更新：** 2026-03-25
