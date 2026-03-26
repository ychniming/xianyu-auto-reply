# SSH 密钥更新说明

## ⚠️ 重要更新

**更新时间**: 2026-03-25

**问题**: 之前使用的 SSH 密钥文件不正确，导致无法连接新服务器。

---

## 🔑 正确的 SSH 密钥

| 服务器 | IP 地址 | 正确的密钥 | 状态 |
|--------|---------|-----------|------|
| **新服务器** | 122.51.107.43 | `niming2.pem` | ✅ 已验证 |
| 旧服务器 | 43.134.89.158 | `niming.pem` | ✅ 保留 |

---

## 📝 原因说明

新服务器（122.51.107.43）在腾讯云绑定的是 **`niming2.pem`** 密钥对，而不是 `niming.pem`。

**备案问题？** ❌  
不是备案问题。SSH 连接失败是因为密钥不匹配，与备案无关。备案只影响域名访问，不影响 SSH 连接。

---

## ✅ 已更新的文件

以下文件已全部更新为使用正确的密钥 `niming2.pem`：

1. ✅ `deploy/NEW_SERVER_DEPLOY.md` - 新服务器部署指南
2. ✅ `deploy/deploy-to-new-server.ps1` - Windows 一键部署脚本
3. ✅ `DEPLOY_QUICKSTART.md` - 快速入门指南
4. ✅ `DEPLOY_SUMMARY.md` - 部署总结文档
5. ✅ `docs/guides/deployment.md` - 完整部署指南

---

## 🚀 使用方式

### 连接新服务器

```bash
# Windows PowerShell
ssh -i "C:\Users\Lenovo、\.ssh\niming2.pem" ubuntu@122.51.107.43
```

### 上传项目文件

```powershell
# 本地执行
scp -i "C:\Users\Lenovo、\.ssh\niming2.pem" -r ./* ubuntu@122.51.107.43:/www/wwwroot/xianyu-auto-reply/
```

### 执行部署

```bash
# 在服务器上执行
cd /www/wwwroot/xianyu-auto-reply/deploy
sudo bash quick-deploy.sh deploy
```

---

## 🔍 验证连接

```bash
# 测试连接
ssh -i "C:\Users\Lenovo、\.ssh\niming2.pem" -o StrictHostKeyChecking=no ubuntu@122.51.107.43 "echo '连接成功'"
```

**预期输出**:
```
连接成功
```

---

## 📋 新服务器状态

已验证的服务器信息：

- ✅ **SSH 连接**: 正常（使用 niming2.pem）
- ✅ **操作系统**: Ubuntu 5.15.0
- ✅ **磁盘空间**: 59GB（可用 50GB）
- ⚠️ **Docker**: 未安装（部署时会自动安装）
- ⚠️ **Docker Compose**: 未安装（部署时会自动安装）

---

## 🆘 常见问题

### Q1: 为什么之前用 niming.pem 连接不上？

A: 因为新服务器在腾讯云绑定的是 `niming2.pem` 密钥对，`niming.pem` 是旧服务器的密钥。

### Q2: 备案会影响 SSH 连接吗？

A: **不会**。备案只影响域名通过 HTTP/HTTPS 访问，不影响 SSH 连接。SSH 连接使用的是 IP 地址和密钥认证。

### Q3: 两个密钥文件能合并吗？

A: 不建议。每个服务器应该使用独立的密钥对，这样更安全。

### Q4: 如果密钥文件权限不对怎么办？

A: 在 Windows 上执行：
```powershell
icacls "C:\Users\Lenovo、\.ssh\niming2.pem" /grant "$env:USERNAME:R"
```

---

## 📞 需要帮助？

如果还有连接问题，请检查：

1. 密钥文件路径是否正确
2. 密钥文件权限是否设置正确
3. 服务器安全组是否开放了 SSH 端口（22）
4. 使用 `-v` 参数查看详细连接日志

```bash
ssh -i "C:\Users\Lenovo、\.ssh\niming2.pem" -v ubuntu@122.51.107.43
```

---

**更新者**: AI Assistant  
**审核**: 开发团队  
**最后更新**: 2026-03-25
