# 部署流程

[返回主目录](./project_rules.md)

---

## 6.1 部署环境

| 环境 | 用途 | 访问地址 |
|------|------|---------|
| 生产环境 | 正式服务 | https://xianyu.niming.cyou |
| 宝塔面板 | 服务器管理 | https://43.134.89.158:18788/590183d8 |
| 本地开发 | 本地测试 | http://localhost:8080 |

---

## 6.2 部署检查清单

### 部署前检查

- [ ] 代码已合并到目标分支
- [ ] 所有测试通过
- [ ] 代码审查完成
- [ ] 版本号已更新
- [ ] 变更日志已更新
- [ ] 配置文件已准备

### 部署中监控

- [ ] 服务启动成功
- [ ] 健康检查通过
- [ ] 数据库连接正常
- [ ] 日志输出正常
- [ ] 性能指标正常

### 部署后验证

- [ ] 功能测试通过
- [ ] 性能测试通过
- [ ] 安全扫描通过
- [ ] 监控告警正常
- [ ] 文档已更新

---

## 6.3 部署命令

### 生产环境部署

```bash
# 1. SSH 连接服务器
ssh -i ~/.ssh/niming.pem ubuntu@43.134.89.158

# 2. 进入项目目录
cd /www/wwwroot/xianyu-auto-reply

# 3. 拉取最新代码
git pull origin main

# 4. 备份数据
sudo cp /www/wwwroot/data/xianyu_data.db /root/backups/xianyu_data_$(date +%Y%m%d).db

# 5. 重启服务
sudo docker-compose -f deploy/docker-compose.yml down
sudo docker-compose -f deploy/docker-compose.yml up -d --build

# 6. 验证部署
sudo docker logs xianyu-auto-reply --tail 50
curl -s http://localhost:8080/health

# 7. 检查外部访问
curl -s https://xianyu.niming.cyou/health
```

### 回滚操作

```bash
# 1. 停止当前服务
sudo docker stop xianyu-auto-reply

# 2. 恢复数据
sudo cp /root/backups/xianyu_data_$(date +%Y%m%d).db /www/wwwroot/data/xianyu_data.db

# 3. 启动旧版本
sudo docker start xianyu-auto-reply-old
```

---

## 6.4 CI/CD 流程

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        uses: appleboy/ssh-action@master
        with:
          host: 43.134.89.158
          username: ubuntu
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /www/wwwroot/xianyu-auto-reply
            git pull origin main
            sudo docker-compose -f deploy/docker-compose.yml up -d --build
```
