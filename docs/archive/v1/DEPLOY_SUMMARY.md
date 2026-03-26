# 部署文档和脚本更新总结

## 📅 更新时间
2026-03-25

## 🎯 更新目的
为新服务器（122.51.107.43）创建完整的部署文档和自动化脚本。

---

## 📄 新增文件

### 1. 部署文档

| 文件 | 说明 | 用途 |
|------|------|------|
| **DEPLOY_QUICKSTART.md** | 快速入门指南 | 提供一键部署和常用命令 |
| **deploy/NEW_SERVER_DEPLOY.md** | 详细部署指南 | 完整的手动部署步骤和故障排查 |

### 2. 部署脚本

| 文件 | 说明 | 使用方式 |
|------|------|---------|
| **deploy/quick-deploy.sh** | 服务器端部署脚本 | `sudo bash quick-deploy.sh deploy` |
| **deploy/deploy-to-new-server.ps1** | Windows 一键部署 | `.\deploy-to-new-server.ps1` |

---

## 🔄 更新的文件

### 1. 部署指南文档

**文件**: `docs/guides/deployment.md`

**更新内容**:
- ✅ 添加新服务器部署章节
- ✅ 添加一键部署命令示例
- ✅ 添加新服务器访问地址
- ✅ 添加相关链接

---

## 📋 服务器信息

### 新服务器（122.51.107.43）

| 项目 | 配置 |
|------|------|
| **IP 地址** | 122.51.107.43 |
| **用户名** | ubuntu |
| **SSH 密钥** | `C:\Users\Lenovo、\.ssh\niming2.pem` ⭐ |
| **部署目录** | `/www/wwwroot/xianyu-auto-reply` |
| **访问地址** | http://122.51.107.43:8080 |

### 旧服务器（43.134.89.158）

| 项目 | 配置 |
|------|------|
| **用途** | 宝塔面板管理 |
| **面板地址** | http://43.134.89.158:18788/login |
| **状态** | 保留，用于监控和管理 |

---

## 🚀 快速开始

### Windows 用户（推荐）

```powershell
# 在项目根目录执行
.\deploy\deploy-to-new-server.ps1
```

### Linux/Mac 用户

```bash
# 1. 连接服务器
ssh -i "C:\Users\Lenovo、\.ssh\niming.pem" ubuntu@122.51.107.43

# 2. 执行部署脚本
cd /www/wwwroot/xianyu-auto-reply/deploy
sudo bash quick-deploy.sh deploy
```

---

## 📖 文档结构

```
项目根目录/
├── DEPLOY_QUICKSTART.md          # ⭐ 快速入门（从这里开始）
├── DEPLOY_SUMMARY.md             # 📋 本文档
├── deploy/
│   ├── NEW_SERVER_DEPLOY.md      # 📘 详细部署指南
│   ├── quick-deploy.sh           # 🔧 服务器端部署脚本
│   ├── deploy-to-new-server.ps1  # 🪟 Windows 部署脚本
│   ├── docker-deploy.sh          # 通用部署脚本
│   └── docker-compose.yml        # Docker 配置
└── docs/guides/
    └── deployment.md             # 📚 完整部署文档（已更新）
```

---

## 🎯 部署流程

### 方式一：PowerShell 一键部署（最简单）

```
本地执行 PowerShell 脚本
  ↓
自动 SSH 连接服务器
  ↓
自动上传项目文件
  ↓
自动执行部署脚本
  ↓
显示访问信息
```

**预计时间**: 5-10 分钟

### 方式二：手动部署（最灵活）

```
1. SSH 连接服务器（使用 niming2.pem）
  ↓
2. 安装 Docker
  ↓
3. SCP 上传项目文件
  ↓
4. 配置环境变量
  ↓
5. 启动 Docker 容器
  ↓
6. 验证部署
```

**预计时间**: 10-15 分钟

---

## ✅ 部署检查清单

部署前请确认：

- [ ] SSH 密钥文件存在且权限正确
- [ ] 服务器可访问（能 ping 通）
- [ ] 服务器已安装 Docker（或准备自动安装）
- [ ] 已配置环境变量（.env 文件）
- [ ] OpenAI API Key 已准备（如果使用 AI 回复）

部署后请验证：

- [ ] Docker 容器正常运行
- [ ] 可以访问 http://122.51.107.43:8080
- [ ] 可以登录管理界面
- [ ] 日志无错误信息

---

## 🔧 常用命令速查

```bash
# 连接服务器
ssh -i "C:\Users\Lenovo、\.ssh\niming2.pem" ubuntu@122.51.107.43

# 查看服务状态
sudo docker-compose ps

# 查看日志
sudo docker-compose logs -f

# 重启服务
sudo docker-compose restart

# 停止服务
sudo docker-compose down

# 备份数据
sudo cp /www/wwwroot/xianyu-auto-reply/data/xianyu_data.db /root/backups/

# 更新部署
cd /www/wwwroot/xianyu-auto-reply
sudo git pull
cd deploy
sudo docker-compose down
sudo docker-compose up -d --build
```

---

## 🆘 故障排查

### SSH 连接问题

```bash
# 检查密钥文件权限（Windows）
icacls "C:\Users\Lenovo、\.ssh\niming2.pem"

# 测试连接（详细输出）
ssh -i "C:\Users\Lenovo、\.ssh\niming2.pem" -v ubuntu@122.51.107.43
```

### Docker 问题

```bash
# 查看容器日志
sudo docker-compose logs xianyu-app

# 重新构建
sudo docker-compose down
sudo docker-compose up -d --build

# 清理并重新部署
sudo docker-compose down -v --rmi all
sudo docker-compose up -d
```

### 网络问题

```bash
# 检查防火墙
sudo ufw status
sudo ufw allow 8080/tcp

# 检查端口监听
sudo netstat -tlnp | grep 8080
```

---

## 📞 获取帮助

1. **查看完整文档**
   - [快速入门](./DEPLOY_QUICKSTART.md)
   - [详细部署指南](./deploy/NEW_SERVER_DEPLOY.md)
   - [完整部署文档](./docs/guides/deployment.md)

2. **查看项目文档**
   - [架构说明](./.trae/rules/02-architecture.md)
   - [运维规范](./.trae/rules/07-operations-specifications.md)

3. **常见问题**
   - 查看各文档中的"常见问题"章节

---

## 📝 后续步骤

部署完成后：

1. **修改默认密码**
   - 登录管理界面
   - 修改 admin 账户密码

2. **配置环境变量**
   - 编辑 `configs/.env`
   - 配置 JWT_SECRET_KEY
   - 配置 OPENAI_API_KEY（可选）

3. **配置域名（可选）**
   - 在宝塔面板中添加站点
   - 配置 Nginx 反向代理
   - 配置 SSL 证书

4. **配置监控告警**
   - 在宝塔面板中配置监控
   - 设置告警通知

---

**创建者**: AI Assistant  
**审核者**: 开发团队  
**最后更新**: 2026-03-25
