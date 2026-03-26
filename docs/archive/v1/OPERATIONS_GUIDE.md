# 闲鱼自动回复系统 - 运维工作流程指南

## 目录

1. [环境部署](#1-环境部署)
2. [日常监控](#2-日常监控)
3. [故障排查](#3-故障排查)
4. [性能优化](#4-性能优化)
5. [安全维护](#5-安全维护)
6. [版本更新](#6-版本更新)
7. [数据备份与恢复](#7-数据备份与恢复)
8. [应急响应](#8-应急响应)

---

## 服务器信息

| 项目 | 内容 |
|------|------|
| **服务器 IP** | 43.134.89.158 |
| **服务器位置** | 新加坡 |
| **操作系统** | Ubuntu 20.04 |
| **宝塔面板** | https://43.134.89.158:18788/590183d8 |
| **域名** | xianyu.niming.cyou |
| **主要服务** | Docker (闲鱼自动回复)、Xray、RustDesk、Nginx |

---

## 1. 环境部署

### 1.1 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|---------|---------|
| 操作系统 | Ubuntu 18.04+ / CentOS 7+ / Windows Server 2016+ | Ubuntu 20.04 LTS |
| CPU | 2核 | 4核+ |
| 内存 | 2GB | 4GB+ |
| 存储 | 10GB | 20GB+ SSD |
| Python | 3.11+ | 3.11+ |
| Docker | 20.10+ | 24.0+ |
| Docker Compose | 2.0+ | 2.20+ |

### 1.2 部署方式

#### 方式一：Docker 预构建镜像部署（推荐）

```bash
# 1. 创建数据目录
mkdir -p /www/wwwroot/data

# 2. 一键启动容器
docker run -d \
  -p 8080:8080 \
  -v /www/wwwroot/data/:/app/data/ \
  --name xianyu-auto-reply \
  --restart always \
  registry.cn-shanghai.aliyuncs.com/zhinian-software/xianyu-auto-reply:1.0

# 3. 验证部署
docker ps
docker logs xianyu-auto-reply --tail 50
```

#### 方式二：Docker Compose 部署

```bash
# 1. 克隆项目
git clone https://github.com/zhinianboke/xianyu-auto-reply.git
cd xianyu-auto-reply

# 2. 配置环境变量
cp configs/.env.example configs/.env
# 编辑 .env 文件，修改 JWT_SECRET_KEY 和 INITIAL_ADMIN_PASSWORD

# 3. 启动服务
cd deploy
docker-compose up -d

# 4. 查看状态
docker-compose ps
docker-compose logs -f
```

#### 方式三：本地开发部署

```bash
# 1. 克隆项目
git clone https://github.com/zhinianboke/xianyu-auto-reply.git
cd xianyu-auto-reply

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 4. 安装 Playwright 浏览器
playwright install chromium
playwright install-deps chromium  # Linux需要

# 5. 启动服务
python scripts/Start.py
```

### 1.3 宝塔面板部署（当前生产环境）

```bash
# 1. SSH 连接服务器
ssh -i ~/.ssh/niming.pem ubuntu@43.134.89.158

# 2. 上传项目到服务器
scp -i ~/.ssh/niming.pem -r xianyu-auto-reply ubuntu@43.134.89.158:/www/wwwroot/

# 3. 执行部署脚本
cd /www/wwwroot/xianyu-auto-reply
sudo bash deploy/deploy-to-bt-panel.sh

# 4. 配置 Nginx 反向代理
# 宝塔面板 -> 网站 -> 添加站点 -> 域名: xianyu.niming.cyou
# 网站设置 -> 反向代理 -> 添加反向代理 -> 目标URL: http://127.0.0.1:8080

# 5. 配置 SSL 证书
# 网站设置 -> SSL -> 使用 Cloudflare 源证书
```

### 1.4 部署验证清单

- [ ] 容器/服务正常运行
- [ ] Web 界面可访问 (https://xianyu.niming.cyou 或 http://43.134.89.158:8080)
- [ ] 默认管理员账号可登录 (admin/admin123)
- [ ] 数据库文件创建成功 (/www/wwwroot/data/xianyu_data.db)
- [ ] 日志正常输出 (/www/wwwroot/xianyu-auto-reply/logs/xianyu_*.log)
- [ ] 健康检查接口正常 (/health)

---

## 2. 日常监控

### 2.1 服务状态监控

#### Docker 容器监控

```bash
# 查看容器状态
docker ps -a

# 查看容器资源使用
docker stats xianyu-auto-reply

# 查看容器日志
docker logs xianyu-auto-reply --tail 100 -f

# 查看容器详细信息
docker inspect xianyu-auto-reply
```

#### 系统资源监控

```bash
# CPU和内存使用
top -p $(pgrep -f "Start.py")

# 磁盘使用
df -h

# 网络连接
ss -tlnp | grep 8080

# 系统负载
uptime
```

#### SSH 连接服务器

```bash
# Windows PowerShell 连接
ssh -i "C:\Users\Lenovo、\.ssh\niming.pem" -o StrictHostKeyChecking=no ubuntu@43.134.89.158

# Linux/macOS 连接
ssh -i ~/.ssh/niming.pem ubuntu@43.134.89.158
```

### 2.2 应用日志监控

#### 日志文件位置

```
logs/
├── xianyu_2026-03-12.log    # 按日期分割的日志
├── xianyu_2026-03-13.log
└── ...
```

#### 日志级别说明

| 级别 | 说明 | 关注度 |
|------|------|--------|
| DEBUG | 调试信息 | 开发环境 |
| INFO | 正常运行信息 | 日常监控 |
| WARNING | 警告信息 | 需要关注 |
| ERROR | 错误信息 | 需要处理 |
| CRITICAL | 严重错误 | 紧急处理 |

#### 关键日志监控命令

```bash
# 实时监控日志
tail -f logs/xianyu_$(date +%Y-%m-%d).log

# 监控错误日志
grep -E "ERROR|CRITICAL" logs/xianyu_*.log | tail -50

# 监控WebSocket连接
grep "WebSocket" logs/xianyu_*.log | tail -20

# 监控账号状态
grep "Cookie" logs/xianyu_*.log | tail -20

# 监控自动发货
grep "发货" logs/xianyu_*.log | tail -20
```

### 2.3 健康检查

#### HTTP 健康检查

```bash
# 基础健康检查
curl -s http://localhost:8080/health

# 检查API响应
curl -s http://localhost:8080/docs | head -20

# 检查登录接口
curl -s -X POST http://localhost:8080/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 外部访问检查
curl -s https://xianyu.niming.cyou/health
curl -s http://43.134.89.158:8080/health
```

#### 定时健康检查脚本

```bash
#!/bin/bash
# health_check.sh

URL="http://localhost:8080/health"
ALERT_WEBHOOK="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"

response=$(curl -s -o /dev/null -w "%{http_code}" $URL)

if [ "$response" != "200" ]; then
    echo "服务异常！HTTP状态码: $response"
    # 发送告警通知
    curl -s -X POST "$ALERT_WEBHOOK" \
        -H 'Content-Type: application/json' \
        -d "{\"msgtype\":\"text\",\"text\":{\"content\":\"闲鱼系统服务异常！状态码: $response\"}}"
    exit 1
fi

echo "服务正常"
exit 0
```

### 2.4 监控指标

#### 关键指标

| 指标 | 正常范围 | 告警阈值 |
|------|---------|---------|
| CPU使用率 | < 50% | > 80% |
| 内存使用率 | < 70% | > 90% |
| 磁盘使用率 | < 70% | > 85% |
| WebSocket连接数 | 根据账号数 | 连续断开 |
| API响应时间 | < 500ms | > 2s |
| 错误日志数/小时 | < 10 | > 50 |

#### 监控仪表盘

访问 Web 管理界面查看：
- 账号连接状态
- 消息处理统计
- 自动发货统计
- 系统资源使用

---

## 3. 故障排查

### 3.1 常见问题诊断流程

```
问题发生
    │
    ├─→ 检查服务状态 (docker ps / systemctl status)
    │       └─→ 服务未运行 → 重启服务
    │
    ├─→ 检查日志 (docker logs / tail -f logs/)
    │       └─→ 发现错误 → 根据错误类型处理
    │
    ├─→ 检查网络连接 (netstat / curl)
    │       └─→ 网络问题 → 检查防火墙/端口
    │
    ├─→ 检查资源使用 (top / df -h)
    │       └─→ 资源不足 → 扩容或清理
    │
    └─→ 检查配置文件 (.env / global_config.yml)
            └─→ 配置错误 → 修正配置
```

### 3.2 常见故障及解决方案

#### 故障1：服务无法启动

**症状**：容器启动失败或立即退出

**排查步骤**：
```bash
# 1. 查看容器日志
docker logs xianyu-auto-reply

# 2. 检查端口占用
netstat -tlnp | grep 8080

# 3. 检查数据目录权限
ls -la data/

# 4. 检查配置文件
cat configs/.env
```

**解决方案**：
- 端口占用：修改端口或停止占用进程
- 权限问题：`chmod -R 755 data/`
- 配置错误：检查 `.env` 文件格式

#### 故障2：WebSocket 连接断开

**症状**：账号显示离线，无法接收消息

**排查步骤**：
```bash
# 1. 检查Cookie是否过期
grep "Cookie" logs/xianyu_*.log | tail -20

# 2. 检查网络连接
ping wss-goofish.dingtalk.com

# 3. 检查Token刷新
grep "token" logs/xianyu_*.log | tail -20
```

**解决方案**：
- Cookie过期：更新账号Cookie
- 网络问题：检查防火墙设置
- Token失效：手动刷新Token

#### 故障3：自动发货失败

**症状**：订单付款后未自动发货

**排查步骤**：
```bash
# 1. 检查发货日志
grep "发货" logs/xianyu_*.log | tail -50

# 2. 检查发货规则配置
sqlite3 data/xianyu_data.db "SELECT * FROM delivery_rules;"

# 3. 检查卡密库存
sqlite3 data/xianyu_data.db "SELECT * FROM card_inventory;"
```

**解决方案**：
- 规则未配置：添加发货规则
- 卡密不足：补充卡密库存
- 匹配失败：检查商品关键词设置

#### 故障4：数据库错误

**症状**：数据读写失败，界面显示异常

**排查步骤**：
```bash
# 1. 检查数据库文件
ls -la data/xianyu_data.db

# 2. 检查数据库完整性
sqlite3 data/xianyu_data.db "PRAGMA integrity_check;"

# 3. 检查数据库大小
du -h data/xianyu_data.db
```

**解决方案**：
- 文件损坏：从备份恢复
- 权限问题：修正文件权限
- 空间不足：清理磁盘空间

### 3.3 日志分析技巧

```bash
# 按时间范围过滤日志
awk '/2026-03-12 10:00/,/2026-03-12 11:00/' logs/xianyu_2026-03-12.log

# 统计错误类型
grep "ERROR" logs/xianyu_*.log | awk -F'|' '{print $3}' | sort | uniq -c | sort -rn

# 查找特定账号的日志
grep "账号ID" logs/xianyu_*.log | tail -100

# 导出最近一小时日志
find logs/ -name "*.log" -mmin -60 -exec cat {} \; > recent_logs.txt
```

---

## 4. 性能优化

### 4.1 系统级优化

#### Docker 资源限制

```yaml
# docker-compose.yml
services:
  xianyu-auto-reply:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

#### 系统参数调优

```bash
# 增加文件描述符限制
echo "* soft nofile 65535" >> /etc/security/limits.conf
echo "* hard nofile 65535" >> /etc/security/limits.conf

# 优化TCP参数
echo "net.core.somaxconn = 65535" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65535" >> /etc/sysctl.conf
sysctl -p
```

### 4.2 应用级优化

#### 数据库优化

```sql
-- 定期清理旧日志
DELETE FROM operation_logs WHERE created_at < datetime('now', '-30 days');

-- 重建索引
REINDEX;

-- 分析数据库
ANALYZE;

-- 检查数据库大小
SELECT name, SUM(pgsize) / 1024.0 / 1024.0 AS size_mb 
FROM dbstat GROUP BY name ORDER BY size_mb DESC;
```

#### 日志配置优化

```yaml
# global_config.yml
LOG_CONFIG:
  level: INFO          # 生产环境使用INFO
  rotation: 1 day      # 每天轮转
  retention: 7 days    # 保留7天
  compression: zip     # 压缩旧日志
```

### 4.3 性能监控

```bash
# 实时监控进程资源
top -p $(pgrep -f "Start.py")

# 监控内存使用详情
pmap -x $(pgrep -f "Start.py")

# 分析进程打开的文件
lsof -p $(pgrep -f "Start.py")

# 网络连接统计
ss -s
```

---

## 5. 安全维护

### 5.1 账号安全

#### 密码策略

```bash
# 修改管理员密码（首次登录后必须执行）
# Web界面 -> 用户管理 -> 修改密码

# 或通过SQL修改
sqlite3 data/xianyu_data.db "UPDATE users SET password='新密码哈希' WHERE username='admin';"
```

#### JWT 密钥管理

```bash
# 生成安全的JWT密钥
openssl rand -base64 32

# 更新 .env 文件
JWT_SECRET_KEY=生成的密钥

# 重启服务生效
docker restart xianyu-auto-reply
```

### 5.2 网络安全

#### 防火墙配置

```bash
# UFW 防火墙配置
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8080/tcp  # 仅内网访问时注释此行
ufw enable

# 限制特定IP访问
ufw allow from 192.168.1.0/24 to any port 8080
```

#### Nginx 安全配置

```nginx
# 禁止访问敏感文件
location ~ /\.(env|git|htaccess) {
    deny all;
}

# 限制请求大小
client_max_body_size 10M;

# 安全头
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
```

### 5.3 数据安全

#### 敏感信息保护

- Cookie 加密存储
- JWT Token 安全传输
- 数据库文件权限限制
- 日志脱敏处理

#### 定期安全审计

```bash
# 检查异常登录
grep "登录失败" logs/xianyu_*.log | tail -50

# 检查权限变更
grep "权限" logs/xianyu_*.log | tail -20

# 检查敏感操作
grep -E "删除|修改|导出" logs/xianyu_*.log | tail -50
```

### 5.4 SSL/HTTPS 配置

```bash
# 使用 Let's Encrypt 免费证书
certbot --nginx -d your-domain.com

# 自动续期
certbot renew --dry-run

# 强制 HTTPS
# Nginx 配置
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## 6. 版本更新

### 6.1 更新前准备

#### 完整备份

```bash
# 1. 备份Docker镜像
sudo docker save xianyu-auto-reply | gzip > /root/xianyu-backup-$(date +%Y%m%d).tar.gz

# 2. 备份数据目录
sudo tar -czvf /root/xianyu-data-backup-$(date +%Y%m%d).tar.gz /www/wwwroot/data/

# 3. 备份数据库
sudo cp /www/wwwroot/data/xianyu_data.db /root/xianyu-db-backup-$(date +%Y%m%d).db

# 4. 备份配置文件
sudo tar -czvf /root/xianyu-config-backup-$(date +%Y%m%d).tar.gz /www/wwwroot/xianyu-auto-reply/configs/

# 5. 备份 Nginx 配置
sudo cp -r /www/server/panel/vhost/nginx /root/nginx-conf-backup-$(date +%Y%m%d)
```

### 6.2 更新方式

#### 方式一：拉取新镜像更新

```bash
# 1. 拉取最新镜像
sudo docker pull registry.cn-shanghai.aliyuncs.com/zhinian-software/xianyu-auto-reply:latest

# 2. 停止旧容器
sudo docker stop xianyu-auto-reply

# 3. 重命名旧容器（备份）
sudo docker rename xianyu-auto-reply xianyu-auto-reply-old

# 4. 启动新容器
sudo docker run -d \
  -p 8080:8080 \
  -v /www/wwwroot/data/:/app/data/ \
  --name xianyu-auto-reply \
  --restart always \
  registry.cn-shanghai.aliyuncs.com/zhinian-software/xianyu-auto-reply:latest

# 5. 验证更新
sudo docker logs xianyu-auto-reply --tail 50

# 6. 确认无误后删除旧容器
sudo docker rm xianyu-auto-reply-old
```

#### 方式二：源码更新

```bash
# 1. SSH 连接服务器
ssh -i ~/.ssh/niming.pem ubuntu@43.134.89.158

# 2. 进入项目目录
cd /www/wwwroot/xianyu-auto-reply

# 3. 拉取最新代码
git pull origin main

# 4. 更新依赖
pip install -r requirements.txt --upgrade

# 5. 数据库迁移（如有）
python -c "from db_manager import db_manager; db_manager.migrate()"

# 6. 重启服务
sudo docker-compose down
sudo docker-compose up -d --build
```

### 6.3 更新验证

```bash
# 1. 检查服务状态
sudo docker ps
sudo docker logs xianyu-auto-reply --tail 50

# 2. 检查版本号
curl -s http://localhost:8080/api/version

# 3. 功能测试
# - 登录测试: https://xianyu.niming.cyou/login.html
# - 账号连接测试
# - 消息收发测试
# - 自动发货测试

# 4. 性能对比
# - 响应时间
# - 资源使用
# - 错误率

# 5. 检查外部访问
curl -s https://xianyu.niming.cyou/health
curl -s http://43.134.89.158:8080/health
```

### 6.4 回滚方案

```bash
# 如果更新失败，执行回滚

# 1. 停止新容器
sudo docker stop xianyu-auto-reply

# 2. 恢复旧镜像
sudo docker load < /root/xianyu-backup-$(date +%Y%m%d).tar.gz

# 3. 恢复数据
sudo tar -xzvf /root/xianyu-data-backup-$(date +%Y%m%d).tar.gz -C /

# 4. 恢复 Nginx 配置
sudo rm -rf /www/server/panel/vhost/nginx
sudo cp -r /root/nginx-conf-backup-$(date +%Y%m%d) /www/server/panel/vhost/nginx

# 5. 重启 Nginx
sudo /www/server/nginx/sbin/nginx -s reload

# 6. 启动旧版本容器
sudo docker start xianyu-auto-reply-old
# 或重新运行旧版本容器
sudo docker run -d \
  -p 8080:8080 \
  -v /www/wwwroot/data/:/app/data/ \
  --name xianyu-auto-reply \
  --restart always \
  registry.cn-shanghai.aliyuncs.com/zhinian-software/xianyu-auto-reply:previous-version
```

---

## 7. 数据备份与恢复

### 7.1 自动备份脚本

```bash
#!/bin/bash
# backup.sh - 自动备份脚本

BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
sudo cp /www/wwwroot/data/xianyu_data.db $BACKUP_DIR/xianyu_data_$DATE.db

# 备份配置文件
sudo tar -czvf $BACKUP_DIR/config_$DATE.tar.gz /www/wwwroot/xianyu-auto-reply/configs/

# 备份日志（可选）
sudo tar -czvf $BACKUP_DIR/logs_$DATE.tar.gz /www/wwwroot/xianyu-auto-reply/logs/

# 备份 Nginx 配置
sudo tar -czvf $BACKUP_DIR/nginx_conf_$DATE.tar.gz /www/server/panel/vhost/nginx/

# 清理旧备份
find $BACKUP_DIR -type f -mtime +$RETENTION_DAYS -delete

echo "备份完成: $DATE"
```

### 7.2 定时备份配置

```bash
# 添加到 crontab
crontab -e

# 每天凌晨2点执行备份
0 2 * * * /root/scripts/backup.sh >> /root/logs/backup.log 2>&1

# 每周日凌晨3点执行完整备份
0 3 * * 0 /root/scripts/full_backup.sh >> /root/logs/backup.log 2>&1
```

### 7.3 数据恢复

```bash
# 恢复数据库
# 1. 停止服务
sudo docker stop xianyu-auto-reply

# 2. 恢复数据库文件
sudo cp /root/backups/xianyu_data_20260312.db /www/wwwroot/data/xianyu_data.db

# 3. 恢复配置文件
sudo tar -xzvf /root/backups/config_20260312.tar.gz -C /

# 4. 恢复 Nginx 配置
sudo tar -xzvf /root/backups/nginx_conf_20260312.tar.gz -C /

# 5. 重启 Nginx
sudo /www/server/nginx/sbin/nginx -s reload

# 6. 启动服务
sudo docker start xianyu-auto-reply

# 7. 验证数据
sqlite3 /www/wwwroot/data/xianyu_data.db "SELECT COUNT(*) FROM users;"
```

---

## 8. 应急响应

### 8.1 应急响应流程

```
故障发现
    │
    ├─→ 初步评估 (5分钟内)
    │       ├─→ 影响范围
    │       ├─→ 严重程度
    │       └─→ 是否需要升级
    │
    ├─→ 紧急处理 (15分钟内)
    │       ├─→ 服务恢复
    │       ├─→ 数据保护
    │       └─→ 通知相关人员
    │
    ├─→ 问题定位 (30分钟内)
    │       ├─→ 日志分析
    │       ├─→ 根因分析
    │       └─→ 制定修复方案
    │
    ├─→ 修复实施
    │       ├─→ 执行修复
    │       ├─→ 验证效果
    │       └─→ 监控观察
    │
    └─→ 复盘总结
            ├─→ 故障报告
            ├─→ 改进措施
            └─→ 文档更新
```

### 8.2 故障等级定义

| 等级 | 定义 | 响应时间 | 处理时限 |
|------|------|---------|---------|
| P0 | 服务完全不可用 | 5分钟 | 30分钟 |
| P1 | 核心功能不可用 | 15分钟 | 2小时 |
| P2 | 部分功能异常 | 30分钟 | 4小时 |
| P3 | 非关键问题 | 2小时 | 24小时 |

### 8.3 应急联系人

| 角色 | 联系方式 | 职责 |
|------|---------|------|
| 运维负责人 | [电话/微信] | 故障协调、资源调度 |
| 开发负责人 | [电话/微信] | 代码问题排查、修复 |
| 产品负责人 | [电话/微信] | 业务影响评估、用户沟通 |

### 8.4 应急操作手册

#### 服务完全不可用

```bash
# 1. 检查服务状态
docker ps -a
systemctl status nginx

# 2. 尝试重启服务
docker restart xianyu-auto-reply

# 3. 检查日志
docker logs xianyu-auto-reply --tail 100

# 4. 检查系统资源
df -h
free -m
top

# 5. 必要时回滚
# 参考版本更新章节的回滚方案
```

#### 数据库损坏

```bash
# 1. 停止服务
docker stop xianyu-auto-reply

# 2. 备份当前数据库
cp data/xianyu_data.db data/xianyu_data_broken.db

# 3. 尝试修复
sqlite3 data/xianyu_data.db ".recover" | sqlite3 data/xianyu_data_fixed.db

# 4. 如果修复失败，从备份恢复
cp /root/backups/xianyu_data_latest.db data/xianyu_data.db

# 5. 启动服务验证
docker start xianyu-auto-reply
```

#### 安全事件

```bash
# 1. 立即断开网络（如必要）
iptables -A INPUT -j DROP
iptables -A OUTPUT -j DROP

# 2. 保存现场
tar -czvf /root/incident_$(date +%Y%m%d_%H%M%S).tar.gz logs/ data/

# 3. 修改所有密码
# 通过数据库或Web界面修改

# 4. 检查入侵痕迹
last -n 50
who /var/log/wtmp
grep "Failed password" /var/log/auth.log

# 5. 恢复服务并加强监控
```

---

## 附录

### A. 服务器信息

| 项目 | 内容 |
|------|------|
| **服务器 IP** | 43.134.89.158 |
| **服务器位置** | 新加坡 |
| **操作系统** | Ubuntu 20.04 |
| **宝塔面板** | https://43.134.89.158:18788/590183d8 |
| **域名** | xianyu.niming.cyou |
| **项目路径** | /www/wwwroot/xianyu-auto-reply |
| **数据路径** | /www/wwwroot/data |

### B. SSH 连接信息

```bash
# Windows PowerShell 连接
ssh -i "C:\Users\Lenovo、\.ssh\niming.pem" -o StrictHostKeyChecking=no ubuntu@43.134.89.158

# Linux/macOS 连接
ssh -i ~/.ssh/niming.pem ubuntu@43.134.89.158

# 上传文件
scp -i ~/.ssh/niming.pem local-file.zip ubuntu@43.134.89.158:/www/wwwroot/

# 下载文件
scp -i ~/.ssh/niming.pem ubuntu@43.134.89.158:/www/wwwroot/file.txt ./
```

### C. 常用命令速查

```bash
# Docker 管理
sudo docker ps -a                    # 查看所有容器
sudo docker logs <container> -f      # 实时查看日志
sudo docker exec -it <container> sh  # 进入容器
sudo docker stats <container>        # 查看资源使用

# 服务管理
sudo docker-compose up -d            # 启动服务
sudo docker-compose down             # 停止服务
sudo docker-compose restart          # 重启服务
sudo docker-compose logs -f          # 查看日志

# Nginx 管理
sudo /www/server/nginx/sbin/nginx -t          # 测试配置
sudo /www/server/nginx/sbin/nginx -s reload   # 重载配置
sudo /www/server/nginx/sbin/nginx -s stop     # 停止服务

# 数据库操作
sqlite3 /www/wwwroot/data/xianyu_data.db     # 连接数据库
.tables                                       # 查看表
.schema <table>                               # 查看表结构
.quit                                         # 退出

# 日志查看
tail -f /www/wwwroot/xianyu-auto-reply/logs/xianyu_$(date +%Y-%m-%d).log  # 实时日志
grep "ERROR" /www/wwwroot/xianyu-auto-reply/logs/*.log                     # 搜索错误

# 宝塔面板
sudo /etc/init.d/bt restart         # 重启宝塔面板
bt default                          # 查看默认登录信息
```

### D. 配置文件位置

| 文件 | 路径 | 用途 |
|------|------|------|
| 环境变量 | /www/wwwroot/xianyu-auto-reply/configs/.env | 敏感配置 |
| 全局配置 | /www/wwwroot/xianyu-auto-reply/configs/global_config.yml | 系统配置 |
| Docker配置 | /www/wwwroot/xianyu-auto-reply/deploy/docker-compose.yml | 容器配置 |
| Nginx配置 | /www/server/panel/vhost/nginx/xianyu.niming.cyou.conf | 反向代理 |
| 数据库 | /www/wwwroot/data/xianyu_data.db | SQLite数据库 |
| 日志目录 | /www/wwwroot/xianyu-auto-reply/logs/ | 应用日志 |

### E. 端口说明

| 端口 | 协议 | 服务 | 说明 |
|------|------|------|------|
| 22 | TCP | SSH | 服务器远程管理 |
| 80 | TCP | HTTP | 网站 HTTP 访问 |
| 443 | TCP | HTTPS | 网站 HTTPS 访问 |
| 8080 | TCP | FastAPI | 闲鱼系统内部端口 |
| 18788 | TCP | 宝塔面板 | Web 管理面板 |
| 8443 | TCP | Xray WebSocket | 代理 WebSocket |
| 8444 | TCP | Xray XTLS | 代理直连 |
| 21115-21119 | TCP/UDP | RustDesk | 远程桌面服务 |

### F. 相关链接

- **系统访问**: https://xianyu.niming.cyou
- **宝塔面板**: https://43.134.89.158:18788/590183d8
- **API文档**: https://xianyu.niming.cyou/docs
- **健康检查**: https://xianyu.niming.cyou/health
- **项目仓库**: https://github.com/zhinianboke/xianyu-auto-reply

---

**文档版本**: v1.1  
**更新时间**: 2026-03-16  
**适用服务器**: 43.134.89.158 (新加坡)  
**维护人员**: 运维团队
