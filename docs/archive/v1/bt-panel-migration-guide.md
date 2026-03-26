# 宝塔面板 Nginx 迁移部署指南

## 项目概述

本文档记录了将现有系统 Nginx 完美迁移到宝塔面板 Nginx 的完整过程，实现统一管理的同时确保 Xray 代理和 RustDesk 服务不受影响。

---

## 服务器信息

| 项目 | 内容 |
|------|------|
| **服务器 IP** | 43.134.89.158 |
| **服务器位置** | 新加坡 |
| **操作系统** | Ubuntu 20.04 |
| **域名** | niming.cyou |
| **宝塔面板地址** | https://43.134.89.158:18788/590183d8 |
| **宝塔用户名** | x21hz9de |
| **宝塔密码** | 8e2863e3 |

---

## 原有服务

迁移前服务器已运行以下服务：

| 服务 | 用途 | 端口 |
|------|------|------|
| Nginx | Web 服务器 / Xray 反向代理 | 80, 443 |
| Xray | VLESS + WebSocket 代理 | 8443, 8444 |
| RustDesk | 远程桌面中继 | 21115-21119 |

---

## 迁移步骤

### 阶段一：备份与准备

#### 1.1 备份现有配置

```bash
# 备份 Nginx 配置
sudo cp -r /etc/nginx /etc/nginx.backup.$(date +%Y%m%d)

# 备份 Xray 配置
sudo cp -r /usr/local/etc/xray /usr/local/etc/xray.backup.$(date +%Y%m%d)

# 导出完整 Nginx 配置
sudo nginx -T > ~/nginx-full-config.txt
```

#### 1.2 记录服务状态

```bash
# 记录运行的服务
systemctl list-units --type=service --state=running > ~/services-status.txt

# 记录端口占用
sudo ss -tlnp > ~/ports-usage.txt

# 记录防火墙规则
sudo ufw status > ~/firewall-rules.txt
```

#### 1.3 创建回滚脚本

创建 `~/rollback-nginx.sh`：

```bash
#!/bin/bash
# Nginx 回滚脚本

echo "=== 停止宝塔 Nginx ==="
sudo pkill -f "/www/server/nginx/sbin/nginx"

echo "=== 恢复系统 Nginx 配置 ==="
LATEST_BACKUP=$(ls -td /etc/nginx.backup.* | head -1)
if [ -d "$LATEST_BACKUP" ]; then
    sudo rm -rf /etc/nginx
    sudo cp -r "$LATEST_BACKUP" /etc/nginx
    echo "已恢复: $LATEST_BACKUP"
fi

echo "=== 启动系统 Nginx ==="
sudo systemctl enable nginx
sudo systemctl start nginx

echo "=== 验证状态 ==="
sudo systemctl status nginx --no-pager
sudo ss -tlnp | grep 443

echo "=== 回滚完成 ==="
```

赋予执行权限：
```bash
chmod +x ~/rollback-nginx.sh
```

---

### 阶段二：安装宝塔面板

#### 2.1 安装宝塔

```bash
# 下载安装脚本
wget -O install.sh http://download.bt.cn/install/install-ubuntu_6.0.sh

# 执行安装
sudo bash install.sh ed8484bec
```

#### 2.2 开放宝塔端口

在云服务器控制台安全组中添加：
- 端口：18788
- 协议：TCP
- 来源：0.0.0.0/0

#### 2.3 登录宝塔

访问：`https://43.134.89.158:18788/590183d8`
- 用户名：x21hz9de
- 密码：8e2863e3

---

### 阶段三：安装宝塔 Nginx

#### 3.1 安装 Nginx

1. 宝塔面板 → 软件商店 → 运行环境
2. 找到 Nginx 1.28
3. 点击「安装」→「极速安装」
4. 等待安装完成（约 5-10 分钟）

#### 3.2 处理 Nginx 接管提示

安装完成后，宝塔会提示接管现有 Nginx：
- 点击「关闭接管服务」（因为现有 Nginx 配置复杂，手动迁移更安全）

---

### 阶段四：配置网站和 SSL

#### 4.1 添加站点

1. 宝塔 → 网站 → 添加站点
2. 填写信息：
   - **域名**：niming.cyou
   - **根目录**：/www/wwwroot/niming.cyou
   - **PHP 版本**：纯静态
   - **数据库**：不创建
   - **FTP**：不创建

#### 4.2 配置反向代理

1. 网站列表 → niming.cyou → 设置
2. 点击「反向代理」标签
3. 点击「添加反向代理」：
   - **代理名称**：xray-ws
   - **目标 URL**：http://127.0.0.1:8443
   - **发送域名**：$host
4. 点击「保存」

#### 4.3 配置 SSL 证书

由于使用 Cloudflare CDN，需要手动上传证书：

1. 登录 Cloudflare 控制台
2. 选择域名 → SSL/TLS → 源服务器
3. 创建证书（RSA 2048，有效期 15 年）
4. 复制证书和私钥

在宝塔中：
1. 网站 → niming.cyou → SSL
2. 选择「其他证书」
3. 粘贴证书（PEM 格式）和私钥（KEY）
4. 点击「保存」
5. 开启「强制 HTTPS」

---

### 阶段五：切换 Nginx

#### 5.1 停止系统 Nginx

```bash
sudo systemctl stop nginx
sudo systemctl disable nginx
```

#### 5.2 启动宝塔 Nginx

```bash
sudo /www/server/nginx/sbin/nginx
```

#### 5.3 验证切换

```bash
# 检查 Nginx 进程
ps aux | grep nginx

# 检查端口监听
sudo ss -tlnp | grep 443

# 测试配置
sudo /www/server/nginx/sbin/nginx -t
```

---

### 阶段六：开放 RustDesk 端口

宝塔安装后防火墙重置，需要重新开放 RustDesk 端口：

```bash
sudo ufw allow 21115/tcp
sudo ufw allow 21116/tcp
sudo ufw allow 21116/udp
sudo ufw allow 21117/tcp
sudo ufw allow 21118/tcp
sudo ufw allow 21119/tcp
```

---

## 验证清单

- [ ] 宝塔面板可正常访问
- [ ] Nginx 已切换到宝塔版本
- [ ] Xray 代理正常工作
- [ ] RustDesk 连接正常
- [ ] HTTPS 网站访问正常
- [ ] SSL 证书有效

---

## 常见问题

### 1. SSL 证书申请失败

**原因**：使用 Cloudflare CDN 时，Let's Encrypt 无法直接验证服务器。

**解决**：使用 Cloudflare 源证书，手动上传到宝塔。

### 2. RustDesk 连接失败

**原因**：宝塔安装后重置了防火墙规则。

**解决**：重新开放 RustDesk 端口 21115-21119。

### 3. Nginx 接管失败

**原因**：系统 Nginx 和宝塔 Nginx 模块不兼容。

**解决**：关闭接管，手动配置反向代理。

---

## 回滚方案

如果迁移后出现问题，执行回滚：

```bash
bash ~/rollback-nginx.sh
```

---

## 后续维护

### 重启宝塔 Nginx

```bash
sudo /www/server/nginx/sbin/nginx -s reload
```

### 查看 Nginx 日志

```bash
# 错误日志
tail -f /www/server/nginx/logs/error.log

# 访问日志
tail -f /www/server/nginx/logs/access.log
```

### 备份宝塔配置

```bash
# 备份网站配置
sudo cp -r /www/server/panel/vhost /www/server/panel/vhost.backup.$(date +%Y%m%d)
```

---

## 相关文档

- [宝塔面板官方文档](https://www.bt.cn/docs/)
- [RustDesk 官方文档](https://rustdesk.com/docs/)
- [Xray 官方文档](https://xtls.github.io/)

---

**文档生成时间**: 2026-03-12  
**文档版本**: v1.0
