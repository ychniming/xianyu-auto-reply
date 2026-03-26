# 闲鱼自动回复系统 - Windows 快速部署脚本
# 新服务器：122.51.107.43
# 用法：.\deploy-to-new-server.ps1

$ErrorActionPreference = "Stop"

# 配置
$SSH_KEY = "C:\Users\Lenovo、\.ssh\niming2.pem"
$SSH_USER = "ubuntu"
$SSH_HOST = "122.51.107.43"
$REMOTE_DIR = "/www/wwwroot/xianyu-auto-reply"
$PROJECT_ROOT = $PSScriptRoot

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  闲鱼自动回复系统 - 快速部署" -ForegroundColor Cyan
Write-Host "  目标服务器：$SSH_HOST" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# 函数：执行 SSH 命令
function Invoke-SSHCommand {
    param([string]$Command)
    
    $sshCmd = "ssh -i `"$SSH_KEY`" -o StrictHostKeyChecking=no $SSH_USER@$SSH_HOST `"$Command`""
    Write-Host "📡 $Command" -ForegroundColor Gray
    Invoke-Expression $sshCmd
}

# 函数：SCP 上传文件
function Invoke-SCPUpload {
    param(
        [string]$Source,
        [string]$Destination
    )
    
    $scpCmd = "scp -i `"$SSH_KEY`" -o StrictHostKeyChecking=no -r `"$Source`" $SSH_USER@$SSH_HOST:`"$Destination`""
    Write-Host "📤 上传：$Source -> $Destination" -ForegroundColor Yellow
    Invoke-Expression $scpCmd
}

# 步骤 1：测试 SSH 连接
Write-Host "1️⃣  测试 SSH 连接..." -ForegroundColor Blue
try {
    $testCmd = "ssh -i `"$SSH_KEY`" -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SSH_USER@$SSH_HOST 'echo Connected'"
    $result = Invoke-Expression $testCmd
    Write-Host "✅ SSH 连接成功" -ForegroundColor Green
} catch {
    Write-Host "❌ SSH 连接失败" -ForegroundColor Red
    Write-Host "错误信息：$_" -ForegroundColor Red
    Write-Host ""
    Write-Host "请检查:" -ForegroundColor Yellow
    Write-Host "  1. SSH 密钥文件路径是否正确" -ForegroundColor Yellow
    Write-Host "  2. 服务器是否可访问" -ForegroundColor Yellow
    Write-Host "  3. SSH 密钥权限是否正确" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "修复权限命令：" -ForegroundColor Yellow
    Write-Host "  icacls `"$SSH_KEY`" /grant `"$env:USERNAME`":R" -ForegroundColor Cyan
    exit 1
}

# 步骤 2：创建远程目录
Write-Host ""
Write-Host "2️⃣  创建远程目录..." -ForegroundColor Blue
Invoke-SSHCommand "mkdir -p $REMOTE_DIR"

# 步骤 3：上传项目文件
Write-Host ""
Write-Host "3️⃣  上传项目文件..." -ForegroundColor Blue
Write-Host "这可能需要几分钟..." -ForegroundColor Gray

# 排除不必要的文件
$exclude = @('.git', 'node_modules', '__pycache__', '*.pyc', '.env', 'logs', 'data', 'backups')

Write-Host "上传项目文件到 $REMOTE_DIR ..." -ForegroundColor Yellow

# 使用 rsync（如果有）或 scp
try {
    # 尝试使用 scp 上传整个项目
    $sourcePath = Join-Path $PROJECT_ROOT "*"
    Invoke-SCPUpload -Source $sourcePath -Destination $REMOTE_DIR
    
    Write-Host "✅ 文件上传完成" -ForegroundColor Green
} catch {
    Write-Host "❌ 文件上传失败" -ForegroundColor Red
    Write-Host "错误信息：$_" -ForegroundColor Red
    exit 1
}

# 步骤 4：执行远程部署
Write-Host ""
Write-Host "4️⃣  执行远程部署..." -ForegroundColor Blue

$deployScript = @"
cd $REMOTE_DIR/deploy && \
sudo bash quick-deploy.sh deploy
"@

Write-Host "执行部署脚本..." -ForegroundColor Yellow
try {
    $deployCmd = "ssh -i `"$SSH_KEY`" -o StrictHostKeyChecking=no $SSH_USER@$SSH_HOST `"$deployScript`""
    Invoke-Expression $deployCmd
} catch {
    Write-Host "❌ 部署失败" -ForegroundColor Red
    Write-Host "错误信息：$_" -ForegroundColor Red
    exit 1
}

# 步骤 5：显示访问信息
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  🎉 部署完成！" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📱 访问地址:" -ForegroundColor White
Write-Host "   http://122.51.107.43:8080" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔐 默认登录信息:" -ForegroundColor White
Write-Host "   用户名：admin" -ForegroundColor Cyan
Write-Host "   密码：admin123" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 管理命令:" -ForegroundColor White
Write-Host "   ssh -i `"$SSH_KEY`" $SSH_USER@$SSH_HOST" -ForegroundColor Gray
Write-Host "   cd $REMOTE_DIR/deploy" -ForegroundColor Gray
Write-Host "   sudo docker-compose ps     # 查看状态" -ForegroundColor Gray
Write-Host "   sudo docker-compose logs -f # 查看日志" -ForegroundColor Gray
Write-Host ""
