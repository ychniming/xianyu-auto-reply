#!/bin/bash

# 闲鱼自动回复系统 - 新服务器快速部署脚本
# 服务器：122.51.107.43
# 用法：bash quick-deploy.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
PROJECT_DIR="/www/wwwroot/xianyu-auto-reply"
BACKUP_DIR="/root/backups"

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查是否以 root 运行
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "请使用 sudo 运行此脚本"
        exit 1
    fi
}

# 检查系统依赖
check_dependencies() {
    print_info "检查系统依赖..."
    
    if ! command -v docker &> /dev/null; then
        print_warning "Docker 未安装，将自动安装"
        install_docker
    else
        print_success "Docker 已安装: $(docker --version)"
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_warning "Docker Compose 未安装，将自动安装"
        install_docker_compose
    else
        print_success "Docker Compose 已安装: $(docker-compose --version)"
    fi
}

# 安装 Docker
install_docker() {
    print_info "安装 Docker..."
    curl -fsSL https://get.docker.com | bash
    systemctl enable docker
    systemctl start docker
    print_success "Docker 安装完成"
}

# 安装 Docker Compose
install_docker_compose() {
    print_info "安装 Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose 安装完成"
}

# 创建项目目录
create_project_dir() {
    print_info "创建项目目录..."
    mkdir -p "$PROJECT_DIR"
    mkdir -p "$BACKUP_DIR"
    print_success "项目目录已创建：$PROJECT_DIR"
}

# 检查项目文件
check_project_files() {
    print_info "检查项目文件..."
    
    if [ ! -f "$PROJECT_DIR/deploy/docker-compose.yml" ]; then
        print_error "项目文件不完整，请先上传项目文件到 $PROJECT_DIR"
        print_info "可以使用以下命令上传："
        echo "scp -i \"C:\\Users\\Lenovo、\\.ssh\\niming.pem\" -r ./* ubuntu@122.51.107.43:$PROJECT_DIR/"
        exit 1
    fi
    
    print_success "项目文件检查通过"
}

# 初始化配置
init_config() {
    print_info "初始化配置文件..."
    
    cd "$PROJECT_DIR"
    
    if [ ! -f "configs/.env" ]; then
        print_warning "配置文件不存在，将创建示例配置"
        
        if [ -f "configs/.env.example" ]; then
            cp configs/.env.example configs/.env
            print_success "已复制配置模板"
        else
            print_warning "未找到配置模板，请手动创建 configs/.env"
        fi
        
        print_warning "请编辑 configs/.env 文件，配置以下变量："
        echo "  - JWT_SECRET_KEY"
        echo "  - INITIAL_ADMIN_PASSWORD"
        echo "  - OPENAI_API_KEY (可选)"
        echo ""
        read -p "按回车键继续..."
    else
        print_success "配置文件已存在"
    fi
}

# 构建镜像
build_image() {
    print_info "构建 Docker 镜像..."
    cd "$PROJECT_DIR/deploy"
    docker-compose build --no-cache
    print_success "镜像构建完成"
}

# 启动服务
start_services() {
    print_info "启动服务..."
    cd "$PROJECT_DIR/deploy"
    docker-compose up -d
    
    print_info "等待服务启动..."
    sleep 10
    
    if docker-compose ps | grep -q "Up"; then
        print_success "服务启动成功"
    else
        print_error "服务启动失败，请查看日志"
        docker-compose logs
        exit 1
    fi
}

# 显示访问信息
show_access_info() {
    echo ""
    print_success "🎉 部署完成！"
    echo ""
    echo "📱 访问地址:"
    echo "   http://122.51.107.43:8080"
    echo "   http://localhost:8080"
    echo ""
    echo "🔐 默认登录信息:"
    echo "   用户名：admin"
    echo "   密码：admin123 (或你在 .env 中设置的密码)"
    echo ""
    echo "📊 管理命令:"
    echo "   查看状态：cd $PROJECT_DIR/deploy && docker-compose ps"
    echo "   查看日志：cd $PROJECT_DIR/deploy && docker-compose logs -f"
    echo "   重启服务：cd $PROJECT_DIR/deploy && docker-compose restart"
    echo "   停止服务：cd $PROJECT_DIR/deploy && docker-compose down"
    echo ""
}

# 配置防火墙
setup_firewall() {
    print_info "配置防火墙..."
    
    if command -v ufw &> /dev/null; then
        ufw allow 8080/tcp 2>/dev/null || true
        ufw allow 80/tcp 2>/dev/null || true
        ufw allow 443/tcp 2>/dev/null || true
        print_success "UFW 防火墙配置完成"
    else
        print_warning "未检测到 UFW，请手动配置防火墙或云安全组"
        print_info "需要开放的端口：8080, 80, 443"
    fi
}

# 备份数据
backup_data() {
    print_info "备份数据..."
    
    mkdir -p "$BACKUP_DIR"
    
    if [ -f "$PROJECT_DIR/data/xianyu_data.db" ]; then
        cp "$PROJECT_DIR/data/xianyu_data.db" "$BACKUP_DIR/xianyu_$(date +%Y%m%d_%H%M%S).db"
        print_success "数据库已备份到：$BACKUP_DIR"
    fi
}

# 主函数
main() {
    check_root
    
    echo "========================================="
    echo "  闲鱼自动回复系统 - 快速部署脚本"
    echo "  服务器：122.51.107.43"
    echo "========================================="
    echo ""
    
    case "$1" in
        "install")
            check_dependencies
            create_project_dir
            ;;
        "deploy")
            check_dependencies
            create_project_dir
            check_project_files
            init_config
            build_image
            start_services
            setup_firewall
            show_access_info
            ;;
        "backup")
            backup_data
            ;;
        "clean")
            print_warning "这将删除所有容器和镜像，确定要继续吗？(y/N)"
            read -r response
            if [[ "$response" =~ ^[Yy]$ ]]; then
                cd "$PROJECT_DIR/deploy"
                docker-compose down -v --rmi all
                print_success "环境已清理"
            fi
            ;;
        "help")
            echo "用法：$0 [命令]"
            echo ""
            echo "命令:"
            echo "  install   安装 Docker 和 Docker Compose"
            echo "  deploy    完整部署（推荐）"
            echo "  backup    备份数据"
            echo "  clean     清理环境"
            echo "  help      显示帮助"
            echo ""
            ;;
        *)
            # 默认执行完整部署
            check_dependencies
            create_project_dir
            check_project_files
            init_config
            build_image
            start_services
            setup_firewall
            show_access_info
            ;;
    esac
}

# 执行
main "$@"
