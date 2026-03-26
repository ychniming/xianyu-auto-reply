# 闲鱼自动回复系统 - 部署快速指南

## 📍 服务器信息

| 服务器 | IP 地址 | 用途 | 状态 |
|--------|---------|------|------|
| **新服务器** | 122.51.107.43 | 闲鱼自动回复 | 🟢 准备部署 |
| 旧服务器 | 43.134.89.158 | 宝塔面板管理 | 🟡 保留 |

**SSH 密钥**: `C:\Users\Lenovo、\.ssh\niming2.pem` ⭐

---

## 🚀 快速部署（推荐）

### 方式一：PowerShell 一键部署（Windows）

```powershell
# 在项目根目录执行
.\deploy\deploy-to-new-server.ps1
```

### 方式二：SSH 手动部署（Linux/Mac）

```bash
# 1. 连接服务器
ssh -i "C:\Users\Lenovo、\.ssh\niming2.pem" ubuntu@122.51.107.43

# 2. 安装 Docker
curl -fsSL https://get.docker.com | sudo bash

# 3. 上传项目（在本地执行）
scp -i "C:\Users\Lenovo、\.ssh\niming2.pem" -r ./* ubuntu@122.51.107.43:/www/wwwroot/xianyu-auto-reply/

# 4. 执行部署（在服务器上）
cd /www/wwwroot/xianyu-auto-reply/deploy
sudo bash quick-deploy.sh deploy
```

---

## 📋 部署文档

| 文档 | 说明 | 位置 |
|------|------|------|
| **新服务器部署指南** | 详细的服务器部署步骤 | [deploy/NEW_SERVER_DEPLOY.md](./deploy/NEW_SERVER_DEPLOY.md) |
| **部署脚本** | 自动化部署脚本 | [deploy/quick-deploy.sh](./deploy/quick-deploy.sh) |
| **PowerShell 脚本** | Windows 一键部署 | [deploy/deploy-to-new-server.ps1](./deploy/deploy-to-new-server.ps1) |
| **完整部署指南** | 所有部署方式和配置 | [docs/guides/deployment.md](./docs/guides/deployment.md) |

---

## 🔧 配置说明

### 必须配置的环境变量

在 `configs/.env` 文件中配置：

```bash
# 安全配置（必须修改）
JWT_SECRET_KEY=your-random-secret-key-32-chars-long
INITIAL_ADMIN_PASSWORD=your-secure-password

# OpenAI 配置（AI 回复功能）
OPENAI_API_KEY=sk-your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
```

### 可选配置

```bash
# 数据库路径
DB_PATH=/app/data/xianyu_data.db

# 日志级别
LOG_LEVEL=INFO

# 时区
TZ=Asia/Shanghai
```

---

## 🌐 访问信息

部署完成后：

| 服务 | 地址 | 说明 |
|------|------|------|
| **Web 界面** | http://122.51.107.43:8080 | 主界面 |
| **API 文档** | http://122.51.107.43:8080/docs | Swagger API 文档 |
| **健康检查** | http://122.51.107.43:8080/health | 服务状态检查 |

**默认登录信息：**
- 用户名：`admin`
- 密码：`admin123`（或你在 `.env` 中设置的密码）

---

## 📊 管理命令

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

# 重新构建
sudo docker-compose up -d --build

# 备份数据
sudo cp data/xianyu_data.db /root/backups/xianyu_$(date +%Y%m%d).db
```

---

## 🔍 故障排查

### SSH 连接失败

```bash
# 检查密钥权限（Windows）
icacls "C:\Users\Lenovo、\.ssh\niming2.pem"

# 修复权限
icacls "C:\Users\Lenovo、\.ssh\niming2.pem" /grant "$env:USERNAME:R"

# 测试连接
ssh -i "C:\Users\Lenovo、\.ssh\niming2.pem" -v ubuntu@122.51.107.43
```

### Docker 容器无法启动

```bash
# 查看详细日志
sudo docker-compose logs xianyu-app

# 检查配置文件
cat configs/.env

# 重新构建
sudo docker-compose down
sudo docker-compose up -d --build
```

### 无法访问服务

```bash
# 检查防火墙
sudo ufw status
sudo ufw allow 8080/tcp

# 检查端口监听
sudo netstat -tlnp | grep 8080

# 检查 Docker 容器
sudo docker-compose ps
```

---

## 📦 文件结构

```
deploy/
├── NEW_SERVER_DEPLOY.md      # 新服务器部署指南
├── quick-deploy.sh           # 服务器端快速部署脚本
├── deploy-to-new-server.ps1  # Windows 一键部署脚本
├── docker-deploy.sh          # 通用部署脚本
├── docker-compose.yml        # Docker Compose 配置
└── docker-compose-cn.yml     # 国内加速版配置
```

---

## 🆘 获取帮助

1. **查看部署日志**
   ```bash
   cd /www/wwwroot/xianyu-auto-reply/deploy
   sudo docker-compose logs -f
   ```

2. **查看完整文档**
   - [部署指南](./docs/guides/deployment.md)
   - [运维指南](./docs/guides/operations.md)
   - [架构说明](./.trae/rules/02-architecture.md)

3. **常见问题**
   - 查看 [NEW_SERVER_DEPLOY.md](./deploy/NEW_SERVER_DEPLOY.md) 的"常见问题"章节

---

**最后更新**: 2026-03-25  
**维护者**: 开发团队
