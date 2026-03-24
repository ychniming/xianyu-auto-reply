@echo off
chcp 65001 >nul
echo ==========================================
echo  闲鱼自动回复系统 - 端到端测试运行脚本
echo ==========================================
echo.

:: 检查参数
if "%~1"=="" goto :menu
if "%~1"=="all" goto :run_all
if "%~1"=="login" goto :run_login
if "%~1"=="navigation" goto :run_navigation
if "%~1"=="accounts" goto :run_accounts
if "%~1"=="keywords" goto :run_keywords
if "%~1"=="headed" goto :run_headed
if "%~1"=="ui" goto :run_ui
if "%~1"=="debug" goto :run_debug
if "%~1"=="report" goto :show_report
if "%~1"=="install" goto :install_deps
goto :menu

:menu
echo 请选择测试类型:
echo.
echo  [1] 运行所有测试
echo  [2] 运行登录测试
echo  [3] 运行导航测试
echo  [4] 运行账号管理测试
echo  [5] 运行关键词管理测试
echo  [6] 带界面运行所有测试
echo  [7] UI模式运行测试
echo  [8] 调试模式运行测试
echo  [9] 查看测试报告
echo  [10] 安装依赖
echo  [0] 退出
echo.
set /p choice="请输入选项 (0-10): "

if "%choice%"=="1" goto :run_all
if "%choice%"=="2" goto :run_login
if "%choice%"=="3" goto :run_navigation
if "%choice%"=="4" goto :run_accounts
if "%choice%"=="5" goto :run_keywords
if "%choice%"=="6" goto :run_headed
if "%choice%"=="7" goto :run_ui
if "%choice%"=="8" goto :run_debug
if "%choice%"=="9" goto :show_report
if "%choice%"=="10" goto :install_deps
if "%choice%"=="0" goto :exit
goto :menu

:run_all
echo.
echo [INFO] 正在运行所有测试...
npx playwright test
goto :end

:run_login
echo.
echo [INFO] 正在运行登录测试...
npx playwright test specs/login.spec.ts
goto :end

:run_navigation
echo.
echo [INFO] 正在运行导航测试...
npx playwright test specs/navigation.spec.ts
goto :end

:run_accounts
echo.
echo [INFO] 正在运行账号管理测试...
npx playwright test specs/accounts.spec.ts
goto :end

:run_keywords
echo.
echo [INFO] 正在运行关键词管理测试...
npx playwright test specs/keywords.spec.ts
goto :end

:run_headed
echo.
echo [INFO] 正在带界面运行测试...
npx playwright test --headed
goto :end

:run_ui
echo.
echo [INFO] 正在启动UI模式...
npx playwright test --ui
goto :end

:run_debug
echo.
echo [INFO] 正在启动调试模式...
npx playwright test --debug
goto :end

:show_report
echo.
echo [INFO] 正在打开测试报告...
npx playwright show-report playwright-report
goto :end

:install_deps
echo.
echo [INFO] 正在安装依赖...
npm install
echo.
echo [INFO] 正在安装浏览器...
npx playwright install
goto :end

:end
echo.
echo ==========================================
echo  测试执行完成
echo ==========================================
echo.
pause
goto :exit

:exit
echo 感谢使用！
exit /b 0
