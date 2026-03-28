/**
 * 卡券管理 - 添加卡券功能测试
 * 测试目标：验证点击"添加卡券"按钮后模态框的正确行为
 * 
 * 测试步骤：
 * 1. 导航到卡券管理页面
 * 2. 点击"添加卡券"按钮
 * 3. 检查模态框是否正确显示
 * 4. 检查表单元素是否存在
 * 5. 检查是否有 JavaScript 错误
 */

const puppeteer = require('puppeteer');

// 测试配置
const TEST_CONFIG = {
  baseUrl: 'http://localhost:8080',
  headless: false, // 设置为 true 在无头模式下运行
  slowMo: 50, // 放慢操作速度以便观察
  timeout: 30000
};

// 测试结果存储
const testResults = {
  testName: '添加卡券模态框功能测试',
  testTime: new Date().toISOString(),
  passed: true,
  steps: [],
  errors: [],
  screenshots: []
};

// 记录测试步骤
function logStep(stepName, passed, details = '') {
  testResults.steps.push({
    step: stepName,
    passed: passed,
    details: details,
    timestamp: new Date().toISOString()
  });
  
  if (!passed) {
    testResults.passed = false;
  }
  
  const status = passed ? '✓' : '✗';
  console.log(`  ${status} ${stepName}${details ? ': ' + details : ''}`);
}

// 截图保存
async function takeScreenshot(page, name) {
  const filename = `tests/e2e/screenshots/add-card-${name}-${Date.now()}.png`;
  try {
    await page.screenshot({ path: filename, fullPage: false });
    testResults.screenshots.push({ name, filename });
    console.log(`    📸 截图已保存：${filename}`);
    return filename;
  } catch (error) {
    console.error(`    ❌ 截图失败：${error.message}`);
    return null;
  }
}

// 主测试函数
async function testAddCardModal() {
  console.log('\n========================================');
  console.log('🧪 开始测试：添加卡券模态框功能');
  console.log('========================================\n');
  
  let browser = null;
  let page = null;
  
  try {
    // 启动浏览器
    console.log('🚀 启动 Puppeteer 浏览器...');
    browser = await puppeteer.launch({
      headless: TEST_CONFIG.headless,
      slowMo: TEST_CONFIG.slowMo,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--window-size=1920,1080'
      ]
    });
    
    logStep('启动浏览器', true, 'Puppeteer 浏览器初始化成功');
    
    // 创建新页面
    page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080 });
    
    // 设置页面错误监听
    const jsErrors = [];
    page.on('pageerror', (error) => {
      jsErrors.push(error.message);
      console.error('  ❌ 页面 JavaScript 错误:', error.message);
    });
    
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.error('  控制台错误:', msg.text());
      }
    });
    
    // 步骤 1: 导航到卡券管理页面
    console.log('\n📍 步骤 1: 导航到卡券管理页面');
    const startTime = Date.now();
    
    try {
      await page.goto(TEST_CONFIG.baseUrl, { 
        waitUntil: 'networkidle0',
        timeout: TEST_CONFIG.timeout 
      });
      
      const loadTime = Date.now() - startTime;
      logStep('导航到主页', true, `加载时间：${loadTime}ms`);
      
      // 等待页面加载完成
      await page.waitForSelector('.sidebar', { timeout: 5000 });
      logStep('侧边栏加载', true, '主界面元素已加载');
      
      // 检查是否已登录（通过检查 token）
      const token = await page.evaluate(() => localStorage.getItem('authToken'));
      if (!token) {
        logStep('登录状态', false, '未检测到登录 token，可能需要先登录');
        console.log('  ⚠️  提示：请先登录系统后再运行此测试');
        
        // 尝试导航到登录页面
        await page.goto(`${TEST_CONFIG.baseUrl}/login.html`, { 
          waitUntil: 'networkidle0',
          timeout: TEST_CONFIG.timeout 
        });
        
        logStep('导航到登录页', true, '已导航到登录页面');
        await takeScreenshot(page, 'login-page');
        
        testResults.passed = false;
        testResults.errors.push('用户未登录，无法继续测试');
        
        // 生成测试报告
        await generateTestReport(testResults);
        return testResults;
      }
      
      logStep('登录状态', true, '已检测到有效的登录 token');
      
      // 点击卡券管理菜单
      console.log('\n  点击卡券管理菜单...');
      const cardsMenuSelector = 'a.nav-link[onclick*="cards"]';
      
      try {
        await page.waitForSelector(cardsMenuSelector, { timeout: 5000 });
        await page.click(cardsMenuSelector);
        logStep('点击卡券管理菜单', true, '菜单点击成功');
        
        // 等待卡券页面加载
        await page.waitForSelector('#cards-section', { timeout: 5000 });
        logStep('卡券页面加载', true, '卡券管理区域已显示');
        
        // 等待一小段时间确保页面完全渲染
        await page.waitForTimeout(1000);
        
        // 截图
        await takeScreenshot(page, 'cards-page');
        
      } catch (error) {
        logStep('导航到卡券管理', false, `错误：${error.message}`);
        testResults.errors.push(`导航失败：${error.message}`);
        await takeScreenshot(page, 'navigation-error');
      }
      
      // 步骤 2: 点击"添加卡券"按钮
      console.log('\n📍 步骤 2: 点击"添加卡券"按钮');
      
      const addCardButtonSelector = 'button[onclick="showAddCardModal()"]';
      
      try {
        // 等待按钮出现
        await page.waitForSelector(addCardButtonSelector, { timeout: 5000 });
        logStep('查找添加卡券按钮', true, '按钮已找到');
        
        // 检查按钮是否可点击
        const buttonEnabled = await page.$eval(addCardButtonSelector, 
          el => !el.disabled && el.offsetParent !== null);
        
        if (buttonEnabled) {
          logStep('按钮状态检查', true, '按钮可用且可见');
        } else {
          logStep('按钮状态检查', false, '按钮不可用或隐藏');
          testResults.errors.push('添加卡券按钮不可用');
        }
        
        // 点击按钮
        await page.click(addCardButtonSelector);
        logStep('点击添加卡券按钮', true, '按钮点击成功');
        
        // 等待一小段时间让模态框动画完成
        await page.waitForTimeout(500);
        
        // 截图
        await takeScreenshot(page, 'after-click-button');
        
      } catch (error) {
        logStep('查找并点击添加卡券按钮', false, `错误：${error.message}`);
        testResults.errors.push(`按钮点击失败：${error.message}`);
        await takeScreenshot(page, 'button-click-error');
      }
      
      // 步骤 3: 检查模态框是否正确显示
      console.log('\n📍 步骤 3: 检查模态框显示状态');
      
      try {
        // 等待模态框出现
        const modalSelector = '#addCardModal';
        await page.waitForSelector(modalSelector, { timeout: 5000 });
        
        // 检查模态框是否可见
        const modalVisible = await page.$eval(modalSelector, el => {
          const style = window.getComputedStyle(el);
          return style.display !== 'none' && style.visibility !== 'hidden';
        });
        
        if (modalVisible) {
          logStep('模态框显示', true, '添加卡券模态框已正确显示');
        } else {
          logStep('模态框显示', false, '模态框存在但不可见');
          testResults.errors.push('模态框不可见');
        }
        
        // 检查模态框的 backdrop 是否显示
        const backdropVisible = await page.evaluate(() => {
          const backdrop = document.querySelector('.modal-backdrop');
          return backdrop && backdrop.offsetParent !== null;
        });
        
        if (backdropVisible) {
          logStep('模态框背景遮罩', true, '背景遮罩已显示');
        } else {
          logStep('模态框背景遮罩', false, '背景遮罩未显示');
        }
        
        // 截图
        await takeScreenshot(page, 'modal-displayed');
        
      } catch (error) {
        logStep('模态框显示检查', false, `错误：${error.message}`);
        testResults.errors.push(`模态框检查失败：${error.message}`);
        await takeScreenshot(page, 'modal-check-error');
      }
      
      // 步骤 4: 检查表单元素是否存在
      console.log('\n📍 步骤 4: 检查表单元素');
      
      const requiredFields = [
        { selector: '#cardName', name: '卡券名称', type: 'input' },
        { selector: '#cardType', name: '卡券类型', type: 'select' },
        { selector: '#cardDescription', name: '描述', type: 'input' },
        { selector: '#cardDelaySeconds', name: '延时时间', type: 'input' },
        { selector: '#isMultiSpec', name: '多规格开关', type: 'checkbox' },
        { selector: '#textContent', name: '文本内容区域', type: 'textarea' },
        { selector: '#addCardForm', name: '表单容器', type: 'form' }
      ];
      
      for (const field of requiredFields) {
        try {
          await page.waitForSelector(field.selector, { timeout: 3000 });
          
          const fieldVisible = await page.$eval(field.selector, el => {
            const style = window.getComputedStyle(el);
            return style.display !== 'none';
          });
          
          if (fieldVisible) {
            logStep(`表单元素：${field.name}`, true, `${field.selector} 存在且可见`);
          } else {
            logStep(`表单元素：${field.name}`, false, `${field.selector} 存在但隐藏`);
          }
          
        } catch (error) {
          logStep(`表单元素：${field.name}`, false, `${field.selector} 未找到`);
        }
      }
      
      // 检查模态框标题
      try {
        const modalTitle = await page.$eval('#addCardModal .modal-title', el => el.textContent);
        if (modalTitle.includes('添加卡券') || modalTitle.includes('卡券')) {
          logStep('模态框标题', true, `标题正确："${modalTitle.trim()}"`);
        } else {
          logStep('模态框标题', false, `标题不匹配："${modalTitle.trim()}"`);
        }
      } catch (error) {
        logStep('模态框标题', false, `未找到标题元素：${error.message}`);
      }
      
      // 检查关闭按钮
      try {
        await page.waitForSelector('#addCardModal .btn-close, #addCardModal [data-bs-dismiss="modal"]', { timeout: 3000 });
        logStep('关闭按钮', true, '模态框关闭按钮存在');
      } catch (error) {
        logStep('关闭按钮', false, '未找到关闭按钮');
      }
      
      // 步骤 5: 检查 JavaScript 错误
      console.log('\n📍 步骤 5: 检查 JavaScript 错误');
      
      if (jsErrors.length === 0) {
        logStep('JavaScript 错误检查', true, '未检测到 JavaScript 错误');
      } else {
        logStep('JavaScript 错误检查', false, `检测到 ${jsErrors.length} 个错误`);
        jsErrors.forEach(err => {
          testResults.errors.push(`JS 错误：${err}`);
        });
      }
      
      // 额外测试：尝试填写表单
      console.log('\n📍 额外测试：表单交互测试');
      
      try {
        // 填写卡券名称
        await page.type('#cardName', '测试卡券');
        logStep('填写卡券名称', true, '成功输入卡券名称');
        
        // 选择卡券类型
        await page.select('#cardType', 'text');
        logStep('选择卡券类型', true, '成功选择文本类型');
        
        // 等待字段切换
        await page.waitForTimeout(300);
        
        // 填写文本内容
        await page.type('#textContent', '这是一条测试卡券内容');
        logStep('填写文本内容', true, '成功输入文本内容');
        
        // 截图
        await takeScreenshot(page, 'form-filled');
        
        // 测试取消按钮
        const cancelBtn = await page.$('#addCardModal .btn-secondary');
        if (cancelBtn) {
          await cancelBtn.click();
          await page.waitForTimeout(500);
          
          const modalClosed = await page.evaluate(() => {
            const modal = document.getElementById('addCardModal');
            return !modal.classList.contains('show');
          });
          
          if (modalClosed) {
            logStep('取消按钮功能', true, '点击取消后模态框正确关闭');
          } else {
            logStep('取消按钮功能', false, '模态框未正确关闭');
          }
        } else {
          logStep('取消按钮功能', false, '未找到取消按钮');
        }
        
      } catch (error) {
        logStep('表单交互测试', false, `错误：${error.message}`);
        await takeScreenshot(page, 'form-interaction-error');
      }
      
    } catch (error) {
      logStep('测试执行', false, `致命错误：${error.message}`);
      testResults.errors.push(`测试执行失败：${error.message}`);
      await takeScreenshot(page, 'fatal-error');
    }
    
  } catch (error) {
    console.error('\n❌ 测试初始化失败:', error.message);
    testResults.passed = false;
    testResults.errors.push(`初始化失败：${error.message}`);
  } finally {
    // 关闭浏览器
    if (browser) {
      console.log('\n🔒 关闭浏览器...');
      await browser.close();
      logStep('关闭浏览器', true, '浏览器已安全关闭');
    }
    
    // 生成测试报告
    await generateTestReport(testResults);
  }
  
  return testResults;
}

// 生成测试报告
async function generateTestReport(results) {
  console.log('\n========================================');
  console.log('📊 测试结果报告');
  console.log('========================================\n');
  
  const fs = require('fs');
  const path = require('path');
  
  // 创建 screenshots 目录
  const screenshotsDir = path.join(__dirname, 'screenshots');
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  }
  
  // 生成 HTML 报告
  const htmlReport = `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>添加卡券功能测试报告</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }
        .header h1 { margin: 0 0 10px 0; }
        .status-pass { background: #28a745; color: white; padding: 5px 15px; border-radius: 20px; display: inline-block; }
        .status-fail { background: #dc3545; color: white; padding: 5px 15px; border-radius: 20px; display: inline-block; }
        .section { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .step { padding: 10px; margin: 5px 0; border-left: 4px solid #28a745; background: #f8f9fa; }
        .step.fail { border-left-color: #dc3545; background: #fff5f5; }
        .step-icon { margin-right: 10px; }
        .error { background: #fff5f5; border: 1px solid #feb2b2; padding: 10px; border-radius: 5px; margin: 5px 0; color: #c53030; }
        .screenshot { max-width: 100%; border: 1px solid #ddd; border-radius: 5px; margin: 10px 0; }
        .meta { color: #666; font-size: 0.9em; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f8f9fa; font-weight: 600; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 添加卡券模态框功能测试报告</h1>
        <p>测试时间：${new Date(results.testTime).toLocaleString('zh-CN')}</p>
        <p class="${results.passed ? 'status-pass' : 'status-fail'}">
            ${results.passed ? '✓ 测试通过' : '✗ 测试失败'}
        </p>
    </div>
    
    <div class="section">
        <h2>📋 测试概览</h2>
        <table>
            <tr><th>测试名称</th><td>${results.testName}</td></tr>
            <tr><th>测试时间</th><td>${new Date(results.testTime).toLocaleString('zh-CN')}</td></tr>
            <tr><th>测试结果</th><td class="${results.passed ? 'status-pass' : 'status-fail'}">${results.passed ? '通过' : '失败'}</td></tr>
            <tr><th>步骤总数</th><td>${results.steps.length}</td></tr>
            <tr><th>通过步骤</th><td>${results.steps.filter(s => s.passed).length}</td></tr>
            <tr><th>失败步骤</th><td>${results.steps.filter(s => !s.passed).length}</td></tr>
            <tr><th>错误数量</th><td>${results.errors.length}</td></tr>
            <tr><th>截图数量</th><td>${results.screenshots.length}</td></tr>
        </table>
    </div>
    
    <div class="section">
        <h2>📝 测试步骤详情</h2>
        ${results.steps.map(step => `
            <div class="step ${step.passed ? '' : 'fail'}">
                <span class="step-icon">${step.passed ? '✓' : '✗'}</span>
                <strong>${step.step}</strong>
                ${step.details ? `<br><span class="meta">${step.details}</span>` : ''}
                <br><span class="meta">时间：${new Date(step.timestamp).toLocaleTimeString('zh-CN')}</span>
            </div>
        `).join('')}
    </div>
    
    ${results.errors.length > 0 ? `
    <div class="section">
        <h2>❌ 错误列表</h2>
        ${results.errors.map(err => `<div class="error">⚠️ ${err}</div>`).join('')}
    </div>
    ` : ''}
    
    ${results.screenshots.length > 0 ? `
    <div class="section">
        <h2>📸 测试截图</h2>
        <table>
            ${results.screenshots.map(ss => `
                <tr>
                    <th>${ss.name}</th>
                    <td><img src="${ss.filename}" class="screenshot" alt="${ss.name}"></td>
                </tr>
            `).join('')}
        </table>
    </div>
    ` : ''}
    
    <div class="section">
        <h2>💡 测试建议</h2>
        <ul>
            ${results.passed 
                ? '<li>✓ 所有测试步骤通过，功能正常</li>'
                : `
                    <li>请检查错误列表中列出的问题</li>
                    <li>确保服务正在运行：${TEST_CONFIG.baseUrl}</li>
                    <li>确保已使用有效账号登录</li>
                    <li>查看截图了解测试执行过程中的页面状态</li>
                `
            }
        </ul>
    </div>
</body>
</html>
  `.trim();
  
  // 保存 HTML 报告
  const reportPath = path.join(__dirname, 'ADD_CARD_MODAL_TEST_REPORT.html');
  fs.writeFileSync(reportPath, htmlReport, 'utf-8');
  console.log(`📄 HTML 报告已保存：${reportPath}`);
  
  // 保存 JSON 结果
  const jsonPath = path.join(__dirname, 'add-card-modal-results.json');
  fs.writeFileSync(jsonPath, JSON.stringify(results, null, 2), 'utf-8');
  console.log(`📄 JSON 结果已保存：${jsonPath}`);
  
  // 打印摘要
  console.log('\n📊 测试摘要:');
  console.log(`  总步骤：${results.steps.length}`);
  console.log(`  通过：${results.steps.filter(s => s.passed).length}`);
  console.log(`  失败：${results.steps.filter(s => !s.passed).length}`);
  console.log(`  截图：${results.screenshots.length}`);
  console.log(`  结果：${results.passed ? '✓ 通过' : '✗ 失败'}`);
  console.log('\n========================================\n');
}

// 运行测试
(async () => {
  try {
    const results = await testAddCardModal();
    process.exit(results.passed ? 0 : 1);
  } catch (error) {
    console.error('测试执行异常:', error);
    process.exit(1);
  }
})();
