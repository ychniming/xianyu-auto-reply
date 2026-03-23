# 服务器系统更新指南

## 服务器信息

| 项目 | 内容 |
|------|------|
| **服务器 IP** | 43.134.89.158 |
| **操作系统** | Ubuntu 20.04 |
| **宝塔面板** | https://43.134.89.158:18788/590183d8 |
| **主要服务** | Docker (闲鱼自动回复)、Xray、RustDesk、Nginx |

---

## ⚠️ 更新前准备

### 1. 创建完整备份

#### 1.1 备份 Docker 容器和数据

```bash
# 停止闲鱼自动回复容器
sudo docker stop xianyu-auto-reply

# 备份 Docker 镜像
sudo docker save xianyu-auto-reply | gzip > /root/xianyu-auto-reply-backup-$(date +%Y%m%d).tar.gz

# 备份数据目录
sudo tar -czvf /root/xianyu-data-backup-$(date +%Y%m%d).tar.gz /www/wwwroot/data/
```

#### 1.2 备份 Nginx 配置

```bash
# 备份 Nginx 配置
sudo cp -r /www/server/panel/vhost/nginx /root/nginx-conf-backup-$(date +%Y%m%d)

# 备份宝塔网站配置
sudo cp -r /www/server/panel/vhost/nginx/xianyu.niming.cyou.conf /root/
```

#### 1.3 备份数据库

```bash
# 导出 SQLite 数据库
sudo cp /www/wwwroot/data/xianyu_data.db /root/xianyu-db-backup-$(date +%Y%m%d).db
```

#### 1.4 备份 Xray 和 RustDesk 配置

```bash
# 备份 Xray 配置
sudo cp -r /etc/xray /root/xray-config-backup-$(date +%Y%m%d)

# 备份 RustDesk 配置
sudo cp -r /etc/rustdesk /root/rustdesk-config-backup-$(date +%Y%m%d)
```

#### 1.5 创建完整系统快照（推荐）

如果在云服务器上，建议先创建系统快照：
- 登录云服务器控制台
- 找到实例 `43.134.89.158`
- 创建系统快照/镜像

---

## 📦 系统更新方式

### 方式一：安全更新（推荐，风险最低）

只更新安全补丁，不升级大版本：

```bash
# 更新软件包列表
sudo apt update

# 只安装安全更新
sudo apt upgrade --only-upgrade -y $(apt list --upgradable | grep security | cut -d'/' -f1)

# 或者使用 unattended-upgrades
sudo apt install unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

**优点**：
- 风险最低
- 不会影响现有服务
- 自动修复安全漏洞

**缺点**：
- 不会获得新功能

---

### 方式二：完整系统更新（中等风险）

更新所有软件包到最新版本：

```bash
# 更新软件包列表
sudo apt update

# 升级所有软件包
sudo apt upgrade -y

# 清理不需要的包
sudo apt autoremove -y
sudo apt autoclean
```

**优点**：
- 获得最新功能和安全补丁
- 系统保持最新状态

**缺点**：
- 可能有兼容性问题
- 需要重启服务

---

### 方式三：系统大版本升级（高风险）

从 Ubuntu 20.04 升级到 22.04：

```bash
# 安装更新管理器
sudo apt update
sudo apt install update-manager-core -y

# 执行升级
sudo do-release-upgrade
```

**⚠️ 警告**：
- 必须先创建系统快照！
- 可能导致服务不兼容
- 升级过程不可逆
- 预计耗时 30-60 分钟

---

## 🔄 更新后恢复服务

### 2.1 重启 Docker 容器

```bash
# 启动闲鱼自动回复容器
sudo docker start xianyu-auto-reply

# 检查容器状态
sudo docker ps

# 查看日志
sudo docker logs xianyu-auto-reply --tail 50
```

### 2.2 重启 Nginx

```bash
# 测试配置
sudo /www/server/nginx/sbin/nginx -t

# 重新加载配置
sudo /www/server/nginx/sbin/nginx -s reload

# 或者重启 Nginx
sudo /etc/init.d/nginx restart
```

### 2.3 重启 Xray

```bash
sudo systemctl restart xray
sudo systemctl status xray
```

### 2.4 重启 RustDesk

```bash
sudo systemctl restart rustdesk-hbbs rustdesk-hbbr
sudo systemctl status rustdesk-hbbs rustdesk-hbbr
```

### 2.5 重启宝塔面板

```bash
sudo /etc/init.d/bt restart
```

---

## ✅ 验证清单

更新完成后，请检查以下项目：

- [ ] Docker 容器运行正常
  ```bash
  sudo docker ps
  sudo docker logs xianyu-auto-reply --tail 20
  ```

- [ ] 闲鱼系统可访问
  - https://xianyu.niming.cyou
  - http://43.134.89.158:8080

- [ ] Nginx 反向代理正常
  ```bash
  curl -I https://xianyu.niming.cyou
  ```

- [ ] Xray 代理正常
  ```bash
  sudo systemctl status xray
  ```

- [ ] RustDesk 远程桌面正常
  ```bash
  sudo systemctl status rustdesk-hbbs rustdesk-hbbr
  ```

- [ ] 宝塔面板可访问
  - https://43.134.89.158:18788/590183d8

---

## 🚨 回滚方案

如果更新后出现问题，执行回滚：

### 回滚步骤

```bash
# 1. 停止所有服务
sudo docker stop xianyu-auto-reply
sudo /etc/init.d/nginx stop
sudo systemctl stop xray
sudo systemctl stop rustdesk-hbbs rustdesk-hbbr

# 2. 恢复 Nginx 配置
sudo rm -rf /www/server/panel/vhost/nginx
sudo cp -r /root/nginx-conf-backup-20260312 /www/server/panel/vhost/nginx

# 3. 恢复数据库
sudo cp /root/xianyu-db-backup-20260312.db /www/wwwroot/data/xianyu_data.db

# 4. 恢复 Docker 容器
sudo docker load < /root/xianyu-auto-reply-backup-20260312.tar.gz
sudo docker start xianyu-auto-reply

# 5. 重启所有服务
sudo /etc/init.d/nginx start
sudo systemctl start xray
sudo systemctl start rustdesk-hbbs rustdesk-hbbr

# 6. 验证服务
sudo docker ps
sudo systemctl status xray
sudo systemctl status rustdesk-hbbs
```

### 使用系统快照回滚（最彻底）

如果在云服务器控制台创建了快照：
1. 登录云服务器控制台
2. 找到实例 `43.134.89.158`
3. 选择"使用快照回滚"
4. 选择更新前创建的快照

---

## 📋 推荐更新计划

### 日常维护（每月一次）

```bash
# 第 1 周：安全更新
sudo apt update
sudo apt upgrade --only-upgrade -y

# 第 2-4 周：监控运行
# 检查日志和服务状态
```

### 季度维护（每 3 个月一次）

```bash
# 完整更新
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y

# 重启服务
sudo docker restart xianyu-auto-reply
sudo /etc/init.d/nginx restart
```

### 年度维护（每年一次）

- 考虑系统大版本升级
- 评估是否需要更换服务器
- 审查安全策略

---

## 🔧 自动化更新脚本

创建自动更新脚本 `/root/update-system.sh`：

```bash
#!/bin/bash
# 系统更新脚本

set -e

echo "=========================================="
echo "  系统更新脚本"
echo "=========================================="

# 创建备份
BACKUP_DATE=$(date +%Y%m%d)
echo "创建备份..."
sudo docker save xianyu-auto-reply | gzip > /root/xianyu-backup-${BACKUP_DATE}.tar.gz
sudo cp -r /www/server/panel/vhost/nginx /root/nginx-backup-${BACKUP_DATE}
sudo cp /www/wwwroot/data/xianyu_data.db /root/db-backup-${BACKUP_DATE}.db

echo "更新软件包..."
sudo apt update
sudo apt upgrade -y

echo "重启服务..."
sudo docker restart xianyu-auto-reply
sudo /etc/init.d/nginx restart
sudo systemctl restart xray
sudo systemctl restart rustdesk-hbbs rustdesk-hbbr

echo "验证服务..."
sudo docker ps
sudo systemctl status xray --no-pager
sudo systemctl status rustdesk-hbbs --no-pager

echo "=========================================="
echo "  更新完成！"
echo "=========================================="
```

使用：
```bash
chmod +x /root/update-system.sh
sudo /root/update-system.sh
```

---

## 📞 紧急联系

如果更新过程中遇到问题：

1. **SSH 连接断开**：
   - 使用云服务器控制台的 VNC/终端功能
   - 检查服务器是否重启完成

2. **服务无法启动**：
   - 查看日志：`sudo journalctl -xe`
   - 检查端口：`sudo ss -tlnp`

3. **Docker 容器异常**：
   - 查看日志：`sudo docker logs xianyu-auto-reply`
   - 重启容器：`sudo docker restart xianyu-auto-reply`

---

**文档版本**: v1.0  
**更新时间**: 2026-03-12  
**适用服务器**: 43.134.89.158
