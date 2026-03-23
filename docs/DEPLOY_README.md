# 闲鱼自动回复系统 - 宝塔面板部署指南

## 📦 部署包内容

```
xianyu-auto-reply/
├── Start.py                 # 项目启动文件
├── requirements.txt         # Python 依赖
├── Dockerfile              # Docker 镜像配置
├── docker-compose.yml      # Docker Compose 配置
├── deploy.sh               # 一键部署脚本 ⭐
├── .env.example            # 环境变量示例
├── DEPLOY_README.md        # 本文件
├── reply_server.py         # Web 服务
├── db_manager.py           # 数据库管理
├── cookie_manager.py       # Cookie 管理
├── XianyuAutoAsync.py      # 闲鱼自动回复核心
├── ai_reply_engine.py      # AI 回复引擎
├── secure_confirm_ultra.py # 自动确认发货
├── secure_freeshipping_ultra.py # 自动免拼发货
├── config.py               # 配置文件
├── utils/                  # 工具函数目录
├── static/                 # 静态资源目录
├── templates/              # 模板目录
└── 虚拟商品话术模板.xlsx    # 关键词话术模板
```

## 🚀 快速部署（推荐）

### 方式一：一键部署脚本（最简单）

1. **上传项目文件到服务器**
   ```bash
   # 使用宝塔文件管理器或 SCP 上传
   scp -r xianyu-auto-reply root@43.134.89.158:/root/
   ```

2. **执行部署脚本**
   ```bash
   cd /root/xianyu-auto-reply
   sudo bash deploy.sh
   ```

3. **按提示完成配置**
   - 输入域名（或直接回车使用 IP）
   - 等待部署完成

4. **访问系统**
   - 地址：http://你的域名 或 http://服务器IP
   - 默认账号：admin / admin123

### 方式二：手动部署

1. **安装 Docker**
   ```bash
   curl -fsSL https://get.docker.com | bash
   systemctl enable docker
   systemctl start docker
   ```

2. **安装 Docker Compose**
   ```bash
   curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   chmod +x /usr/local/bin/docker-compose
   ```

3. **创建项目目录**
   ```bash
   mkdir -p /www/wwwroot/xianyu-auto-reply
   cd /www/wwwroot/xianyu-auto-reply
   ```

4. **上传项目文件**
   - 上传所有项目文件到 `/www/wwwroot/xianyu-auto-reply/`

5. **配置环境变量**
   ```bash
   cp .env.example .env
   nano .env
   # 修改 JWT_SECRET_KEY 和 INITIAL_ADMIN_PASSWORD
   ```

6. **启动服务**
   ```bash
   docker-compose up -d
   ```

7. **配置 Nginx 反向代理**
   - 宝塔面板 → 网站 → 添加站点
   - 域名：你的域名
   - 反向代理到：http://127.0.0.1:8080

## ⚙️ 环境变量配置

编辑 `.env` 文件：

```bash
# 安全配置（重要！请修改）
JWT_SECRET_KEY=your-random-secret-key-32-chars-long
INITIAL_ADMIN_PASSWORD=your-secure-password

# 数据库配置
DB_PATH=/app/data/xianyu_data.db

# 日志配置
LOG_LEVEL=INFO
TZ=Asia/Shanghai
```

## 🔧 管理命令

```bash
# 启动服务
./start.sh

# 停止服务
./stop.sh

# 重启服务
./restart.sh

# 查看日志
./logs.sh

# 更新服务
./update.sh

# 手动管理
docker-compose up -d      # 启动
docker-compose down       # 停止
docker-compose restart    # 重启
docker-compose logs -f    # 查看日志
```

## 📋 部署前检查清单

- [ ] 服务器已安装宝塔面板
- [ ] 已开放 8080 端口（或配置 Nginx 反向代理）
- [ ] 已准备域名（可选）
- [ ] 已修改默认密码和 JWT 密钥

## 🔒 安全配置建议

1. **修改默认密码**
   - 首次登录后立即修改 admin 密码

2. **设置强密钥**
   - JWT_SECRET_KEY 至少 32 位随机字符串
   - 可使用命令生成：`openssl rand -base64 32`

3. **配置 HTTPS**
   - 在宝塔面板申请 SSL 证书
   - 开启强制 HTTPS

4. **限制访问 IP**
   - 如仅需本地管理，可配置防火墙只允许特定 IP

## 🐛 常见问题

### 1. 端口被占用

```bash
# 查看端口占用
netstat -tlnp | grep 8080

# 修改端口（编辑 docker-compose.yml）
ports:
  - "8081:8080"  # 改为 8081
```

### 2. 权限不足

```bash
# 确保使用 root 权限
sudo bash deploy.sh

# 或切换到 root
sudo su
```

### 3. Docker 安装失败

```bash
# 手动安装 Docker
apt-get update
apt-get install -y docker.io
systemctl enable docker
systemctl start docker
```

### 4. 无法访问

```bash
# 检查防火墙
ufw status

# 开放端口
ufw allow 8080/tcp
ufw allow 80/tcp
ufw allow 443/tcp
```

## 📞 技术支持

- 项目地址：https://github.com/your-repo/xianyu-auto-reply
- 问题反馈：请提交 Issue
- 文档更新：关注项目 README

## 📝 更新日志

### v1.0.0 (2026-03-12)
- ✨ 初始版本发布
- 🐳 支持 Docker 部署
- 🔧 支持宝塔面板一键部署
- 🔒 增强安全配置

---

**部署时间**: 2026-03-12  
**文档版本**: v1.0.0
