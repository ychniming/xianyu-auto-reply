---
title: 运维指南
description: 闲鱼自动回复系统的日常运维和故障处理
lastUpdated: 2026-03-25
maintainer: Doc Keeper Agent
---

# 运维指南

[返回索引](../INDEX.md)

## 日常监控

### 服务状态检查

```bash
# Docker 容器状态
docker ps | grep xianyu

# 服务健康检查
curl http://localhost:8080/health

# 查看实时日志
docker logs -f xianyu-auto-reply --tail 100
```

### 关键指标

| 指标 | 正常范围 | 检查方式 |
|------|---------|---------|
| CPU 使用率 | < 50% | `docker stats` |
| 内存使用 | < 80% | `docker stats` |
| 磁盘空间 | > 20% 可用 | `df -h` |
| WebSocket 连接 | 稳定 | 查看日志 |

### 日志查看

```bash
# 今日日志
tail -f logs/xianyu_$(date +%Y-%m-%d).log

# 搜索错误
grep -i error logs/*.log

# 查看最近 100 行
docker logs xianyu-auto-reply --tail 100
```

## 数据备份

### 自动备份脚本

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
cp /www/wwwroot/data/xianyu_data.db $BACKUP_DIR/xianyu_data_$DATE.db

# 备份配置
cp -r /www/wwwroot/xianyu-auto-reply/configs $BACKUP_DIR/configs_$DATE

# 清理 7 天前的备份
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "configs_*" -mtime +7 -exec rm -rf {} \;

echo "Backup completed: $DATE"
```

### 定时备份

```bash
# 添加到 crontab
crontab -e

# 每天凌晨 2 点备份
0 2 * * * /root/scripts/backup.sh >> /root/logs/backup.log 2>&1
```

## 故障排查

### 服务无法启动

```bash
# 1. 检查日志
docker logs xianyu-auto-reply --tail 50

# 2. 检查端口
lsof -i :8080

# 3. 检查配置
cat configs/.env

# 4. 重建容器
docker-compose down
docker-compose up -d
```

### WebSocket 断开

```bash
# 1. 检查 Cookie 是否过期
# 登录 Web 界面查看账号状态

# 2. 检查网络连接
ping xianyu.com

# 3. 查看错误日志
grep "WebSocket" logs/*.log | tail -20

# 4. 重启服务
docker restart xianyu-auto-reply
```

### AI 回复异常

```bash
# 1. 检查 API Key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# 2. 检查余额
# 登录 OpenAI 控制台

# 3. 查看错误日志
grep "OpenAI" logs/*.log | tail -20
```

### 数据库问题

```bash
# 1. 检查数据库文件
ls -la data/xianyu_data.db

# 2. 检查数据库完整性
sqlite3 data/xianyu_data.db "PRAGMA integrity_check;"

# 3. 从备份恢复
cp /root/backups/xianyu_data_latest.db data/xianyu_data.db
```

## 性能优化

### 内存优化

```yaml
# docker-compose.yml
services:
  xianyu-auto-reply:
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
```

### 日志轮转

```python
# config.py
LOG_ROTATION = "00:00"  # 每天轮转
LOG_RETENTION = "7 days"  # 保留 7 天
LOG_COMPRESSION = "zip"  # 压缩
```

### 数据库优化

```sql
-- 定期清理旧日志
DELETE FROM operation_logs WHERE created_at < datetime('now', '-30 days');

-- 重建索引
REINDEX;

-- 分析统计
ANALYZE;
```

## 安全维护

### 定期更新

```bash
# 更新系统包
apt update && apt upgrade -y

# 更新 Docker 镜像
docker-compose pull
docker-compose up -d
```

### 安全检查

```bash
# 检查开放端口
ss -tlnp

# 检查防火墙
ufw status

# 检查登录日志
last -n 20
```

### 密钥轮换

```bash
# 生成新的 JWT 密钥
openssl rand -hex 32

# 更新配置
# 编辑 configs/.env 中的 JWT_SECRET_KEY

# 重启服务
docker restart xianyu-auto-reply
```

## 相关文档

- [部署指南](./deployment.md)
- [开发指南](./development.md)
- [归档文档](../archive/v1/OPERATIONS_GUIDE.md)

---

**维护者：** Doc Keeper Agent  
**最后更新：** 2026-03-25
