# 闲鱼自动回复系统 - 端到端测试

本项目包含闲鱼自动回复系统的全面端到端测试套件，使用 Playwright 测试框架实现。

## 测试覆盖范围

### 核心功能测试
- **登录页面测试** (`login.spec.ts`)
  - 登录方式切换（用户名/密码、邮箱/密码、邮箱/验证码）
  - 登录按钮点击验证
  - 验证码刷新
  - 输入框交互
  - 响应式布局
  - 性能测试

- **导航菜单测试** (`navigation.spec.ts`)
  - 主导航菜单点击
  - 菜单切换
  - 移动端导航
  - 登出功能
  - 外部链接
  - 导航状态保持

- **账号管理测试** (`accounts.spec.ts`)
  - 添加账号按钮点击
  - 手动输入表单操作
  - 账号列表操作
  - 账号行操作按钮
  - 模态框操作
  - 性能测试

- **关键词管理测试** (`keywords.spec.ts`)
  - 账号选择
  - 关键词添加
  - 匹配类型选择
  - 回复模式选择
  - 高级条件设置
  - 关键词测试工具
  - 导入导出功能
  - 关键词列表操作

## 快速开始

### 1. 安装依赖

```bash
cd tests/e2e
npm install
```

### 2. 安装浏览器

```bash
npm run install:browsers
```

### 3. 运行测试

```bash
# 运行所有测试
npm test

# 运行特定浏览器测试
npm run test:chromium
npm run test:firefox
npm run test:webkit

# 运行特定页面测试
npm run test:login
npm run test:navigation
npm run test:accounts
npm run test:keywords

# 带界面运行
npm run test:headed

# UI模式
npm run test:ui

# 调试模式
npm run test:debug
```

## 项目结构

```
tests/e2e/
├── fixtures/
│   ├── base-page.ts      # 基础页面对象
│   └── test-data.ts      # 测试数据和选择器
├── pages/
│   ├── login-page.ts     # 登录页面对象
│   ├── dashboard-page.ts # 仪表盘页面对象
│   ├── accounts-page.ts  # 账号管理页面对象
│   ├── keywords-page.ts  # 关键词管理页面对象
│   └── items-page.ts     # 商品管理页面对象
├── specs/
│   ├── login.spec.ts     # 登录测试
│   ├── navigation.spec.ts # 导航测试
│   ├── accounts.spec.ts  # 账号管理测试
│   └── keywords.spec.ts  # 关键词管理测试
├── playwright.config.ts  # Playwright配置
├── global-setup.ts       # 全局设置
├── global-teardown.ts    # 全局清理
├── package.json          # 项目依赖
└── README.md             # 本文件
```

## 测试报告

测试完成后，报告将生成在 `playwright-report/` 目录：

```bash
# 查看HTML报告
npm run report

# 或使用静态服务器
npm run report:html
```

报告包含：
- 测试结果摘要
- 详细的测试步骤
- 失败截图
- 测试视频（失败时）
- 性能指标
- 浏览器追踪

## 环境变量

创建 `.env` 文件配置测试环境：

```env
TEST_BASE_URL=http://localhost:8000
TEST_ADMIN_USERNAME=admin
TEST_ADMIN_PASSWORD=admin123
TEST_USER_USERNAME=testuser
TEST_USER_PASSWORD=testpass
```

## 编写新测试

### 1. 创建页面对象（如需要）

```typescript
import { Page } from '@playwright/test';
import { BasePage } from '../fixtures/base-page';

export class NewPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  async clickSomeButton() {
    await this.click('#someButton');
  }
}
```

### 2. 创建测试文件

```typescript
import { test } from '@playwright/test';
import { NewPage } from '../pages/new-page';

test.describe('新功能测试', () => {
  test('测试点击操作', async ({ page }) => {
    const newPage = new NewPage(page);
    await newPage.goto();
    await newPage.clickSomeButton();
  });
});
```

## 最佳实践

1. **使用页面对象模式**：将页面操作封装在页面对象中
2. **使用数据驱动测试**：使用 `test-data.ts` 中的测试数据
3. **添加适当的等待**：使用 `waitFor` 和自定义等待方法
4. **捕获截图和视频**：失败时自动捕获
5. **编写可维护的测试**：使用描述性的测试名称

## 持续集成

在 CI/CD 中运行测试：

```bash
# 安装依赖
npm ci

# 安装浏览器
npx playwright install --with-deps

# 运行测试
npm test

# 上传报告
# 根据 CI 平台配置报告上传
```

## 故障排除

### 测试失败

1. 检查应用是否运行在 `http://localhost:8000`
2. 查看 `playwright-report/` 中的截图和视频
3. 使用 `--debug` 模式运行测试

### 浏览器问题

```bash
# 重新安装浏览器
npx playwright install --force

# 安装系统依赖（Linux）
npx playwright install-deps
```

## 贡献指南

1. 为新功能添加对应的页面对象
2. 编写全面的测试用例
3. 确保所有测试通过
4. 更新本文档

## 许可证

MIT
