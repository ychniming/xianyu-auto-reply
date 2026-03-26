# 附录

[返回主目录](./project_rules.md)

---

## A. 常用命令

```bash
# SSH 连接（新服务器）
ssh -i ~/.ssh/niming2.pem ubuntu@122.51.107.43

# Docker 管理
sudo docker ps -a                    # 查看所有容器
sudo docker logs xianyu-auto-reply -f  # 实时查看日志
sudo docker exec -it xianyu-auto-reply sh  # 进入容器
sudo docker stats xianyu-auto-reply  # 查看资源使用

# 服务管理
sudo docker-compose -f deploy/docker-compose.yml up -d      # 启动服务
sudo docker-compose -f deploy/docker-compose.yml down       # 停止服务
sudo docker-compose -f deploy/docker-compose.yml restart    # 重启服务
sudo docker-compose -f deploy/docker-compose.yml logs -f    # 查看日志

# 数据库操作
sqlite3 /www/wwwroot/xianyu-auto-reply/data/xianyu_data.db  # 连接数据库
.tables                                     # 查看表
.schema users                               # 查看表结构
SELECT * FROM users LIMIT 10;              # 查询数据
.quit                                       # 退出

# 日志查看
tail -f /www/wwwroot/xianyu-auto-reply/logs/xianyu_$(date +%Y-%m-%d).log
grep "ERROR" /www/wwwroot/xianyu-auto-reply/logs/*.log | tail -50

# Nginx 管理
sudo /www/server/nginx/sbin/nginx -t          # 测试配置
sudo /www/server/nginx/sbin/nginx -s reload   # 重载配置
sudo systemctl status nginx                    # 查看状态

# 宝塔面板（旧服务器）
sudo /etc/init.d/bt restart     # 重启宝塔面板
bt default                      # 查看默认登录信息

# 文件传输
scp -i ~/.ssh/niming2.pem local-file.zip ubuntu@122.51.107.43:/www/wwwroot/
scp -i ~/.ssh/niming2.pem ubuntu@122.51.107.43:/www/wwwroot/file.txt ./
```

---

## B. 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DB_PATH | 数据库路径 | /app/data/xianyu_data.db |
| JWT_SECRET_KEY | JWT密钥 | - |
| INITIAL_ADMIN_PASSWORD | 初始管理员密码 | admin123 |
| LOG_LEVEL | 日志级别 | INFO |
| TZ | 时区 | Asia/Shanghai |

---

## D. 相关链接

- **系统访问**: http://122.51.107.43:8080
- **API 文档**: http://122.51.107.43:8080/docs
- **健康检查**: http://122.51.107.43:8080/health
- **项目仓库**: https://github.com/zhinianboke/xianyu-auto-reply
- **问题反馈**: https://github.com/zhinianboke/xianyu-auto-reply/issues

**旧服务器（宝塔面板）**:
- **宝塔面板**: http://43.134.89.158:18788/login

---

## E. 服务器端口说明

### 新服务器（122.51.107.43）

| 端口 | 协议 | 服务 | 说明 |
|------|------|------|------|
| 22 | TCP | SSH | 服务器远程管理 |
| 80 | TCP | HTTP | 网站 HTTP 访问 |
| 443 | TCP | HTTPS | 网站 HTTPS 访问 |
| 8080 | TCP | FastAPI | 闲鱼系统内部端口 |

### 旧服务器（43.134.89.158）

| 端口 | 协议 | 服务 | 说明 |
|------|------|------|------|
| 22 | TCP | SSH | 服务器远程管理 |
| 80 | TCP | HTTP | 网站 HTTP 访问 |
| 443 | TCP | HTTPS | 网站 HTTPS 访问 |
| 18788 | TCP | 宝塔面板 | Web 管理面板 |
| 8443 | TCP | Xray WebSocket | 代理 WebSocket |
| 8444 | TCP | Xray XTLS | 代理直连 |
| 21115-21119 | TCP/UDP | RustDesk | 远程桌面服务 |
