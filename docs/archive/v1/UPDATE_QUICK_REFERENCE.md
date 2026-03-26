# 服务器系统更新 - 快速参考卡

## 🚀 一键更新（推荐）

```bash
# SSH 登录服务器
ssh -i "C:\Users\Lenovo、\.ssh\niming.pem" ubuntu@43.134.89.158

# 执行更新脚本
sudo bash /home/ubuntu/update-server.sh
```

**脚本功能**：
- ✅ 自动备份所有数据和服务
- ✅ 执行系统安全更新
- ✅ 自动重启所有服务
- ✅ 创建回滚脚本
- ✅ 记录更新日志

---

## 📋 手动更新步骤

### 1. 更新软件包

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. 重启服务

```bash
# Docker 容器
sudo docker restart xianyu-auto-reply

# Nginx
sudo /www/server/nginx/sbin/nginx -s reload

# Xray
sudo systemctl restart xray

# RustDesk
sudo systemctl restart rustdesk-hbbs rustdesk-hbbr
```

### 3. 验证服务

```bash
# 查看 Docker 容器
sudo docker ps

# 查看服务状态
sudo systemctl status xray
sudo systemctl status rustdesk-hbbs

# 测试访问
curl -I https://xianyu.niming.cyou
```

---

## 🔄 回滚方法

如果更新后出现问题：

```bash
# 执行回滚脚本
sudo bash /root/backups/rollback.sh
```

---

## 📊 更新类型对比

| 更新类型 | 命令 | 风险 | 建议频率 |
|---------|------|------|---------|
| **安全更新** | `sudo apt upgrade --only-upgrade` | ⭐ 低 | 每月 1 次 |
| **完整更新** | `sudo apt upgrade -y` | ⭐⭐ 中 | 每季 1 次 |
| **系统升级** | `sudo do-release-upgrade` | ⭐⭐⭐⭐ 高 | 每年 1 次 |

---

## ⚠️ 更新前检查清单

- [ ] 已创建系统快照（云服务器控制台）
- [ ] 已备份 Docker 容器
- [ ] 已备份 Nginx 配置
- [ ] 已备份数据库
- [ ] 已备份 Xray/RustDesk 配置
- [ ] 已通知相关人员（如有用户）

---

## 🔍 验证服务正常

```bash
# 1. Docker 容器
sudo docker ps
# 应显示 xianyu-auto-reply 状态为 Up

# 2. 闲鱼系统
curl https://xianyu.niming.cyou/health
# 应返回 {"status":"healthy"}

# 3. 宝塔面板
# 访问 https://43.134.89.158:18788/590183d8

# 4. Xray 代理
sudo systemctl status xray
# 应显示 active (running)

# 5. RustDesk
sudo systemctl status rustdesk-hbbs
# 应显示 active (running)
```

---

## 📞 常见问题

### Q1: 更新后服务无法启动？

```bash
# 查看日志
sudo journalctl -xe

# 检查端口
sudo ss -tlnp

# 手动启动
sudo docker start xianyu-auto-reply
sudo /etc/init.d/nginx start
```

### Q2: SSH 连接断开？

- 使用云服务器控制台的 VNC 功能
- 等待服务器重启完成（约 2-5 分钟）
- 检查安全组规则

### Q3: Docker 容器异常？

```bash
# 查看日志
sudo docker logs xianyu-auto-reply --tail 100

# 重启容器
sudo docker restart xianyu-auto-reply

# 重新创建容器
cd /www/wwwroot
sudo docker-compose down
sudo docker-compose up -d
```

---

## 📁 备份位置

| 备份类型 | 位置 |
|---------|------|
| Docker 镜像 | `/root/backups/xianyu-auto-reply-*.tar.gz` |
| 数据目录 | `/root/backups/xianyu-data-*.tar.gz` |
| Nginx 配置 | `/root/backups/nginx-config-*/` |
| 数据库 | `/root/backups/xianyu-db-*.db` |
| 更新日志 | `/root/update-*.log` |

---

## 🌐 服务访问地址

| 服务 | 地址 |
|------|------|
| 闲鱼系统 | https://xianyu.niming.cyou |
| 宝塔面板 | https://43.134.89.158:18788/590183d8 |
| 直接访问 | http://43.134.89.158:8080 |

---

**文档版本**: v1.0  
**更新时间**: 2026-03-12  
**服务器**: 43.134.89.158
