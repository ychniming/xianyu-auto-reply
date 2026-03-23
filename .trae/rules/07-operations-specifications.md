# 运维规范

[返回主目录](./project_rules.md)

---

## 7.1 日常运维任务

| 任务 | 频率 | 负责人 | 备注 |
|------|------|--------|------|
| 检查服务状态 | 每日 | 运维人员 | Docker容器、进程 |
| 查看错误日志 | 每日 | 运维人员 | 查看 /www/wwwroot/xianyu-auto-reply/logs/ |
| 数据备份 | 每日 | 自动化 | 备份到 /root/backups/ |
| 性能监控 | 每日 | 运维人员 | CPU、内存、磁盘 |
| 安全扫描 | 每周 | 安全人员 | 漏洞扫描 |
| 系统更新 | 每月 | 运维人员 | 安全补丁 |

---

## 7.2 监控告警

### 监控指标

| 指标 | 正常范围 | 告警阈值 | 处理时限 |
|------|---------|---------|---------|
| CPU使用率 | <50% | >80% | 30分钟 |
| 内存使用率 | <70% | >90% | 30分钟 |
| 磁盘使用率 | <70% | >85% | 2小时 |
| API响应时间 | <500ms | >2s | 1小时 |
| 错误率 | <1% | >5% | 30分钟 |
| WebSocket断连 | 0次 | 连续3次 | 15分钟 |

### 监控命令

```bash
# SSH连接服务器
ssh -i ~/.ssh/niming.pem ubuntu@43.134.89.158

# 检查Docker容器状态
sudo docker ps -a
sudo docker stats xianyu-auto-reply

# 检查服务日志
sudo docker logs xianyu-auto-reply --tail 100 -f

# 检查系统资源
df -h
free -m
uptime

# 检查端口监听
ss -tlnp | grep -E '8080|80|443'

# 检查Nginx状态
sudo /www/server/nginx/sbin/nginx -t
sudo systemctl status nginx
```

### 告警通知

```bash
# 告警脚本示例 - 健康检查
#!/bin/bash
ALERT_WEBHOOK="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"

# 检查服务
if ! curl -s http://localhost:8080/health > /dev/null; then
    curl -s -X POST "$ALERT_WEBHOOK" \
        -H 'Content-Type: application/json' \
        -d "{\"msgtype\":\"text\",\"text\":{\"content\":\"【告警】闲鱼系统服务不可用！\"}}"
fi
```

---

## 7.3 日志管理

### 日志位置

| 日志类型 | 位置 | 保留时间 |
|---------|------|---------|
| 应用日志 | /www/wwwroot/xianyu-auto-reply/logs/xianyu_*.log | 7天 |
| Nginx访问日志 | /www/server/nginx/logs/access.log | 30天 |
| Nginx错误日志 | /www/server/nginx/logs/error.log | 30天 |
| Docker日志 | sudo docker logs xianyu-auto-reply | 实时 |

### 日志分析

```bash
# 实时查看应用日志
tail -f /www/wwwroot/xianyu-auto-reply/logs/xianyu_$(date +%Y-%m-%d).log

# 统计错误类型
grep "ERROR" /www/wwwroot/xianyu-auto-reply/logs/*.log | awk -F'|' '{print $3}' | sort | uniq -c

# 分析API响应时间
grep "response_time" /www/wwwroot/xianyu-auto-reply/logs/*.log | awk '{sum+=$NF; count++} END {print "avg:", sum/count}'
```

---

## 7.4 容量规划

| 资源 | 当前使用 | 预警阈值 | 扩容阈值 |
|------|---------|---------|---------|
| CPU | ~30% | 60% | 80% |
| 内存 | 2GB/4GB | 3GB | 3.5GB |
| 磁盘 | 5GB/20GB | 15GB | 18GB |
| Docker容器 | 1个 | - | - |
