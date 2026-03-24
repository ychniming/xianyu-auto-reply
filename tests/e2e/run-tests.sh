#!/bin/bash

# 闲鱼自动回复系统 - 端到端测试运行脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示菜单
show_menu() {
    echo ""
    echo "=========================================="
    echo "  闲鱼自动回复系统 - 端到端测试运行脚本"
    echo "=========================================="
    echo ""
    echo "请选择测试类型:"
    echo ""
    echo "  [1] 运行所有测试"
    echo "  [2] 运行登录测试"
    echo "  [3] 运行导航测试"
    echo "  [4] 运行账号管理测试"
    echo "  [5] 运行关键词管理测试"
    echo "  [6] 带界面运行所有测试"
    echo "  [7] UI模式运行测试"
    echo "  [8] 调试模式运行测试"
    echo "  [9] 查看测试报告"
    echo "  [10] 安装依赖"
    echo "  [0] 退出"
    echo ""
}

# 运行所有测试
run_all() {
    print_info "正在运行所有测试..."
    npx playwright test
}

# 运行登录测试
run_login() {
    print_info "正在运行登录测试..."
    npx playwright test specs/login.spec.ts
}

# 运行导航测试
run_navigation() {
    print_info "正在运行导航测试..."
    npx playwright test specs/navigation.spec.ts
}

# 运行账号管理测试
run_accounts() {
    print_info "正在运行账号管理测试..."
    npx playwright test specs/accounts.spec.ts
}

# 运行关键词管理测试
run_keywords() {
    print_info "正在运行关键词管理测试..."
    npx playwright test specs/keywords.spec.ts
}

# 带界面运行测试
run_headed() {
    print_info "正在带界面运行测试..."
    npx playwright test --headed
}

# UI模式运行测试
run_ui() {
    print_info "正在启动UI模式..."
    npx playwright test --ui
}

# 调试模式运行测试
run_debug() {
    print_info "正在启动调试模式..."
    npx playwright test --debug
}

# 显示测试报告
show_report() {
    print_info "正在打开测试报告..."
    npx playwright show-report playwright-report
}

# 安装依赖
install_deps() {
    print_info "正在安装依赖..."
    npm install
    print_info "正在安装浏览器..."
    npx playwright install
}

# 主函数
main() {
    # 检查参数
    if [ $# -eq 0 ]; then
        show_menu
        read -p "请输入选项 (0-10): " choice
    else
        choice=$1
    fi

    case $choice in
        1|all)
            run_all
            ;;
        2|login)
            run_login
            ;;
        3|navigation)
            run_navigation
            ;;
        4|accounts)
            run_accounts
            ;;
        5|keywords)
            run_keywords
            ;;
        6|headed)
            run_headed
            ;;
        7|ui)
            run_ui
            ;;
        8|debug)
            run_debug
            ;;
        9|report)
            show_report
            ;;
        10|install)
            install_deps
            ;;
        0|exit)
            print_success "感谢使用！"
            exit 0
            ;;
        *)
            print_error "无效选项: $choice"
            show_menu
            read -p "请输入选项 (0-10): " choice
            main $choice
            ;;
    esac

    echo ""
    echo "=========================================="
    print_success "测试执行完成"
    echo "=========================================="
}

# 运行主函数
main "$@"
