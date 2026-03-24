import { defineConfig, devices } from '@playwright/test';
import path from 'path';

/**
 * Playwright 端到端测试配置
 * 闲鱼自动回复系统 - 点击操作测试
 */
export default defineConfig({
  testDir: './specs',

  /* 测试文件匹配模式 */
  testMatch: '**/*.spec.ts',

  /* 完全并行运行测试 */
  fullyParallel: true,

  /* 失败时禁止并行 */
  forbidOnly: !!process.env.CI,

  /* 重试次数 */
  retries: process.env.CI ? 2 : 1,

  /* 并行工作进程数 */
  workers: process.env.CI ? 1 : undefined,

  /* 报告器配置 */
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'playwright-report/results.json' }],
    ['list'],
  ],

  /* 全局共享配置 */
  use: {
    /* 基础URL */
    baseURL: process.env.TEST_BASE_URL || 'http://localhost:8081',

    /* 截图配置 */
    screenshot: 'only-on-failure',

    /* 视频录制 */
    video: 'retain-on-failure',

    /* 追踪录制 */
    trace: 'on-first-retry',

    /* 视口大小 */
    viewport: { width: 1280, height: 720 },

    /* 动作超时 */
    actionTimeout: 15000,

    /* 导航超时 */
    navigationTimeout: 30000,
  },

  /* 项目配置 - 多浏览器测试 */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    /* 移动设备测试 */
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],

  /* 本地开发服务器配置 - 使用已运行的服务器 */
  // webServer: {
  //   command: 'python ../../scripts/Start.py',
  //   url: 'http://localhost:8000',
  //   reuseExistingServer: !process.env.CI,
  //   timeout: 120000,
  // },

  /* 全局设置 */
  globalSetup: require.resolve('./global-setup'),
  globalTeardown: require.resolve('./global-teardown'),

  /* 输出目录 */
  outputDir: 'test-results/',
});
