import { chromium, FullConfig } from '@playwright/test';
import path from 'path';
import fs from 'fs';

/**
 * 全局设置 - 测试开始前执行
 * 创建测试数据目录、初始化环境等
 */
async function globalSetup(config: FullConfig) {
  console.log('🚀 开始全局设置...');
  
  // 创建报告目录
  const reportDir = path.join(__dirname, 'playwright-report');
  const screenshotsDir = path.join(reportDir, 'screenshots');
  const videosDir = path.join(reportDir, 'videos');
  const tracesDir = path.join(reportDir, 'traces');
  
  [reportDir, screenshotsDir, videosDir, tracesDir].forEach(dir => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
      console.log(`📁 创建目录: ${dir}`);
    }
  });
  
  // 验证服务器是否可访问
  const { baseURL } = config.projects[0].use;
  console.log(`🔍 验证服务器: ${baseURL}`);
  
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    // 尝试访问登录页面
    await page.goto(`${baseURL}/login.html`, { timeout: 30000 });
    console.log('✅ 服务器连接成功');
    
    // 保存已认证状态（如果可能）
    // 这里可以预登录并保存存储状态
    
  } catch (error) {
    console.warn('⚠️ 服务器连接失败，测试可能无法正常运行:', error.message);
  } finally {
    await browser.close();
  }
  
  console.log('✅ 全局设置完成');
}

export default globalSetup;
