# 网站部署指南

## 服务器环境

- **服务器 IP**: 43.134.89.158
- **服务器位置**: 新加坡
- **宝塔面板**: https://43.134.89.158:18788/590183d8
- **用户名**: x21hz9de
- **密码**: 8e2863e3
- **Web 服务器**: 宝塔 Nginx 1.28
- **PHP 版本**: 8.2
- **MySQL 版本**: 5.7
- **域名**: niming.cyou

---

## 已部署服务

### Xray 代理服务

| 项目 | 内容 |
|------|------|
| **WebSocket 端口** | 8443 |
| **XTLS-Vision 端口** | 8444 |
| **域名** | niming.cyou |
| **协议** | VLESS |
| **启用** | ✅ 正常运行 |

### RustDesk 远程桌面

| 项目 | 内容 |
|------|------|
| **ID 服务器** | 43.134.89.158:21116 |
| **中继服务器** | 43.134.89.158:21117 |
| **公钥** | FiL7iOeuVYYO8gcVl9fJ7S3gDWRfC7ABcLXOryprTWE= |
| **状态** | ✅ 正常运行 |

### 服务管理命令

```bash
# Xray 服务
sudo systemctl status xray
sudo systemctl restart xray

# RustDesk 服务
sudo systemctl status rustdesk-hbbs rustdesk-hbbr
sudo systemctl restart rustdesk-hbbs rustdesk-hbbr

# 查看 Xray 日志
sudo journalctl -u xray -n 50

# 查看 RustDesk 日志
sudo journalctl -u rustdesk-hbbs -n 50
sudo journalctl -u rustdesk-hbbr -n 50
```

---

## 服务器端口汇总

### 对外服务端口

| 端口 | 协议 | 服务 | 说明 |
|------|------|------|------|
| 22 | TCP | SSH | 服务器远程管理 |
| 80 | TCP | HTTP | 网站 HTTP 访问 |
| 443 | TCP | HTTPS | 网站 HTTPS 访问 |
| 18788 | TCP | 宝塔面板 | Web 管理面板 |
| 21115-21119 | TCP/UDP | RustDesk | 远程桌面服务 |
| 8443 | TCP | Xray WebSocket | 代理 WebSocket |
| 8444 | TCP | Xray XTLS | 代理直连 |

### 内部服务端口

| 端口 | 协议 | 服务 | 说明 |
|------|------|------|------|
| 3306 | TCP | MySQL | 数据库（仅本地） |
| 888 | TCP | PHPMyAdmin | 数据库管理 |
| 8888 | TCP | 宝塔面板 | 面板备用端口 |

---

## SSH 密钥配置

### 本地密钥位置

| 项目 | 路径 |
|------|------|
| **私钥文件** | `C:\Users\Lenovo、\.ssh\niming.pem` |
| **公钥文件** | `C:\Users\Lenovo、\.ssh\niming.pem.pub` |

### SSH 连接命令

```powershell
# 连接服务器
ssh -i "C:\Users\Lenovo、\.ssh\niming.pem" -o StrictHostKeyChecking=no ubuntu@43.134.89.158

# 使用 sudo 执行命令
ssh -i C:\Users\Lenovo、\.ssh\niming.pem ubuntu@43.134.89.158 "sudo 命令"

# 上传文件
scp -i C:\Users\Lenovo、\.ssh\niming.pem local-file.zip ubuntu@43.134.89.158:/www/wwwroot/

# 下载文件
scp -i C:\Users\Lenovo、\.ssh\niming.pem ubuntu@43.134.89.158:/www/wwwroot/file.txt ./
```

### 注意事项

1. **路径中的中文**：用户名 `Lenovo、` 包含中文顿号 `、` 和符号 `,`，需要用引号包裹路径
2. **密钥权限**：Windows 上密钥文件需要适当权限
3. **首次连接**：使用 `-o StrictHostKeyChecking=no` 跳过主机密钥确认
4. **安全建议**：
   - 不要泄露私钥文件
   - 不要将私钥上传到任何公开仓库
   - 定期更换密钥对

---

## 部署方式一：静态网站（HTML/CSS/JS）

### 适用场景
- 个人博客（Hexo/Hugo/VuePress）
- 企业官网
- 单页应用（SPA）

### 部署步骤

1. **准备网站文件**
   - 本地构建好静态网站
   - 打包成 zip 或 tar.gz 格式

2. **上传文件到服务器**
   - 方式 A：宝塔面板 → 文件 → 上传
   - 方式 B：SFTP 连接上传

3. **创建站点**
   - 宝塔面板 → 网站 → 添加站点
   - 填写域名（如：www.niming.cyou）
   - 根目录：/www/wwwroot/www.niming.cyou
   - PHP 版本：纯静态

4. **部署文件**
   ```bash
   # 解压上传的文件
   cd /www/wwwroot/www.niming.cyou
   unzip website.zip
   ```

5. **配置 SSL（可选）**
   - 网站设置 → SSL → 申请 Let's Encrypt
   - 开启强制 HTTPS
   
   > **注意**：如果域名使用 Cloudflare CDN，需要：
   > - 方式一：在 Cloudflare 中暂停代理（灰色云朵），申请证书后再开启
   > - 方式二：使用 Cloudflare 源证书（推荐），在 SSL → 其他证书中导入

---

## 部署方式二：PHP 网站（WordPress/ThinkPHP/Laravel）

### 适用场景
- WordPress 博客
- 企业 CMS 系统
- PHP 框架项目

### 一键部署（推荐新手）

宝塔面板提供一键部署功能，快速安装常用网站程序：

1. **宝塔面板 → 软件商店 → 一键部署**
2. 选择要安装的程序：
   - WordPress（博客）
   - 苹果 CMS（影视网站）
   - Joomla（CMS）
   - 其他开源程序
3. 填写域名和数据库信息
4. 点击部署，自动完成安装

### 手动部署步骤

1. **创建数据库**
   - 宝塔面板 → 数据库 → 添加数据库
   - 记录数据库名、用户名、密码

2. **创建站点**
   - 宝塔面板 → 网站 → 添加站点
   - 填写域名
   - 选择 PHP 8.2
   - 创建 FTP（可选）

3. **上传代码**
   - 上传 PHP 项目文件到网站根目录
   - 确保入口文件（index.php）在根目录

4. **配置伪静态**
   - 网站设置 → 伪静态
   - WordPress 选择 `wordpress`
   - Laravel 选择 `laravel5`
   - ThinkPHP 选择 `thinkphp`

5. **修改配置文件**
   - 配置数据库连接信息
   - 设置正确的网站 URL

6. **设置权限**
   ```bash
   chown -R www:www /www/wwwroot/your-site
   chmod -R 755 /www/wwwroot/your-site
   chmod -R 777 /www/wwwroot/your-site/uploads  # 上传目录
   ```

---

## 部署方式三：反向代理（Node.js/Python/Go）

### 适用场景
- Node.js 应用（Express/Nest.js）
- Python 应用（Django/Flask/FastAPI）
- Go 应用（Gin/Echo）

### 部署步骤

1. **上传代码**
   - 将项目上传到服务器（如：/www/wwwroot/myapp）

2. **安装依赖并启动**
   ```bash
   cd /www/wwwroot/myapp
   # Node.js
   npm install
   npm start
   
   # Python
   pip install -r requirements.txt
   python app.py
   
   # Go
   go build
   ./myapp
   ```

3. **使用 PM2 管理进程（推荐）**
   ```bash
   # 安装 PM2
   npm install -g pm2
   
   # 启动应用
   pm2 start app.js --name "myapp"
   
   # 设置开机自启
   pm2 startup
   pm2 save
   ```

4. **创建反向代理站点**
   - 宝塔面板 → 网站 → 添加站点
   - 填写域名
   - PHP 版本：纯静态

5. **配置反向代理**
   - 网站设置 → 反向代理
   - 添加反向代理：
     - 代理名称：app
     - 目标 URL：http://127.0.0.1:3000（你的应用端口）
     - 发送域名：$host

6. **配置 SSL**
   - 申请 SSL 证书
   - 开启强制 HTTPS

---

## 部署方式四：Docker 容器

### 适用场景
- 微服务架构
- 复杂依赖环境
- 需要隔离的应用

### 部署步骤

1. **安装 Docker**
   - 宝塔面板 → 软件商店 → Docker

2. **编写 Dockerfile**
   ```dockerfile
   FROM node:18-alpine
   WORKDIR /app
   COPY package*.json ./
   RUN npm install
   COPY . .
   EXPOSE 3000
   CMD ["npm", "start"]
   ```

3. **构建并运行容器**
   ```bash
   cd /www/wwwroot/myapp
   docker build -t myapp .
   docker run -d -p 3000:3000 --name myapp myapp
   ```

4. **配置反向代理**
   - 同方式三，配置 Nginx 反向代理到容器端口

---

## 常用操作

### 文件管理

**方式一：宝塔面板文件管理器**
- 宝塔面板 → 文件
- 可视化操作：上传、下载、编辑、解压
- 支持在线编辑代码

**方式二：SFTP 连接**
```bash
# 使用 FileZilla 或 WinSCP
# 主机：43.134.89.158
# 端口：22
# 协议：SFTP
# 用户名：ubuntu
# 私钥：niming.pem
```

**方式三：命令行**
```bash
# 上传文件
scp -i ~/.ssh/niming.pem local-file.zip ubuntu@43.134.89.158:/www/wwwroot/

# 下载文件
scp -i ~/.ssh/niming.pem ubuntu@43.134.89.158:/www/wwwroot/file.txt ./
```

### 备份网站

**手动备份：**
```bash
# 创建备份目录
mkdir -p /backup

# 备份网站文件
cd /www/wwwroot
tar -czvf /backup/site-backup-$(date +%Y%m%d).tar.gz your-site/

# 备份数据库
mysqldump -u root -p database_name > /backup/db-backup-$(date +%Y%m%d).sql

# 备份 Nginx 配置
cp -r /www/server/nginx/conf /backup/nginx-conf-backup
```

**自动备份（宝塔计划任务）：**
1. 宝塔面板 → 计划任务
2. 添加任务 → 选择「备份网站」或「备份数据库」
3. 设置执行周期：每天/每周
4. 设置备份保留份数

### 查看日志

**网站访问日志：**
- 宝塔面板 → 网站 → 设置 → 日志
- 查看访问统计、错误请求

**错误日志位置：**
```bash
# Nginx 错误日志
tail -f /www/server/nginx/logs/error.log

# PHP 错误日志
tail -f /www/server/php/82/var/log/php-fpm.log

# MySQL 错误日志
tail -f /www/server/mysql/mysql-error.log

# 网站独立错误日志
tail -f /www/wwwroot/your-site/error.log
```

### 重启服务

```bash
# 重启 Nginx
sudo /www/server/nginx/sbin/nginx -s reload

# 重启 PHP
sudo /etc/init.d/php-fpm-82 reload

# 重启 MySQL
sudo /etc/init.d/mysqld restart

# 重启宝塔面板
sudo /etc/init.d/bt restart
```

### 性能优化

**1. 开启 Nginx Gzip 压缩**
```nginx
# 在 Nginx 配置中添加
gzip on;
gzip_vary on;
gzip_min_length 1k;
gzip_types text/plain text/css application/json application/javascript;
```

**2. 配置浏览器缓存**
```nginx
# 静态文件缓存
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

**3. PHP 优化**
- 宝塔面板 → 软件商店 → PHP 8.2 → 设置
- 调整 `memory_limit`、`max_execution_time`
- 开启 OPcache 加速

**4. MySQL 优化**
- 宝塔面板 → 数据库 → MySQL → 性能配置
- 根据服务器内存选择合适的配置方案

---

## 安全建议

### 1. 定期备份
- **网站文件**：每周备份一次
- **数据库**：每日自动备份
- **配置文件**：修改后备份

宝塔面板提供计划任务功能，可设置自动备份：
- 宝塔面板 → 计划任务 → 添加任务
- 选择「备份网站」或「备份数据库」
- 设置执行周期（每天/每周）

### 2. 更新软件
- 及时更新宝塔面板到最新版
- 更新 Nginx、PHP、MySQL 到最新版本
- 更新系统安全补丁

### 3. 防火墙配置
```bash
# 查看当前防火墙规则
sudo ufw status

# 开放必要端口
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 18788/tcp # 宝塔面板

# 开放 RustDesk 端口
sudo ufw allow 21115:21119/tcp
sudo ufw allow 21116/udp
```

### 4. SSL 证书
- 所有网站必须使用 HTTPS
- 开启 HSTS 增强安全性
- 定期更新证书（Let's Encrypt 有效期 90 天）

### 5. 其他安全措施
- 修改宝塔面板默认端口（8888）
- 设置复杂的宝塔登录密码
- 开启宝塔面板双因素认证
- 定期修改 SSH 密钥
- 禁用 root 远程登录

---

## 故障排查

### 网站无法访问

**排查步骤：**
1. **检查 Nginx 是否运行**
   ```bash
   ps aux | grep nginx
   sudo /www/server/nginx/sbin/nginx -t
   ```

2. **检查防火墙端口**
   ```bash
   sudo ufw status
   sudo ss -tlnp | grep 80
   sudo ss -tlnp | grep 443
   ```

3. **检查域名解析**
   ```bash
   nslookup your-domain.com
   ping your-domain.com
   ```

4. **查看错误日志**
   ```bash
   tail -f /www/server/nginx/logs/error.log
   tail -f /www/wwwroot/your-site/error.log
   ```

**常见原因：**
- 防火墙未开放 80/443 端口
- 域名未解析到服务器 IP
- Nginx 配置语法错误
- 网站目录权限错误

### 502 Bad Gateway

**排查步骤：**
1. **PHP 服务是否运行**
   ```bash
   ps aux | grep php
   sudo /etc/init.d/php-fpm-82 status
   ```

2. **反向代理目标是否正确**
   - 检查反向代理配置的端口是否正确
   - 确保后端应用已启动

3. **端口是否被占用**
   ```bash
   sudo ss -tlnp | grep 端口号
   ```

**常见原因：**
- PHP-FPM 未启动
- 反向代理目标端口错误
- 后端应用崩溃

### 数据库连接失败

**排查步骤：**
1. **MySQL 是否运行**
   ```bash
   sudo /etc/init.d/mysqld status
   ps aux | grep mysql
   ```

2. **数据库用户名密码是否正确**
   ```bash
   mysql -u 用户名 -p -h localhost
   ```

3. **数据库用户权限是否正确**
   ```sql
   SHOW GRANTS FOR '用户名'@'localhost';
   ```

**常见原因：**
- MySQL 服务未启动
- 数据库用户名/密码错误
- 用户没有数据库访问权限
- 数据库主机配置错误（应为 localhost 或 127.0.0.1）

### SSL/HTTPS 问题

**排查步骤：**
1. **检查证书是否过期**
   ```bash
   openssl x509 -in /www/server/panel/vhost/ssl/your-domain.crt -noout -dates
   ```

2. **检查证书配置**
   - 宝塔面板 → 网站 → 设置 → SSL
   - 确认证书和私钥匹配

3. **强制 HTTPS 问题**
   - 检查是否有循环重定向
   - 确认 Cloudflare 加密模式设置正确

**常见原因：**
- 证书过期
- 证书链不完整
- 强制 HTTPS 配置错误
- Cloudflare 加密模式不正确

---

## 快速命令参考

### 日常维护

```bash
# 查看所有服务状态
sudo systemctl status nginx xray mysql rustdesk-hbbs rustdesk-hbbr

# 重启所有服务
sudo systemctl restart nginx xray
sudo systemctl restart rustdesk-hbbs rustdesk-hbbr

# 查看实时日志
sudo journalctl -u xray -f
sudo journalctl -u rustdesk-hbbs -f

# 检查端口占用
sudo ss -tlnp | grep -E '80|443|8443|8444|2111'
```

### 故障快速排查

```bash
# 1. 检查服务状态
systemctl status nginx xray

# 2. 检查端口监听
ss -tlnp | grep -E '80|443'

# 3. 检查防火墙
sudo ufw status

# 4. 检查域名解析
nslookup niming.cyou

# 5. 测试本地连接
curl -I http://127.0.0.1
curl -k https://127.0.0.1

# 6. 测试代理端口
nc -zv 127.0.0.1 8443
nc -zv 127.0.0.1 8444
```

---

## 参考链接

- [宝塔面板官方文档](https://www.bt.cn/doc.html)
- [Nginx 配置文档](https://nginx.org/en/docs/)
- [PHP 官方文档](https://www.php.net/docs.php)
- [RustDesk 官方文档](https://rustdesk.com/docs/)
- [Xray 官方文档](https://xtls.github.io/)

---

**文档生成时间**: 2026-03-12  
**适用服务器**: 43.134.89.158  
**最后更新**: 2026-03-12
