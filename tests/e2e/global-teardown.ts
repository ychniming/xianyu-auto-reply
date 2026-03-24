import { FullConfig } from '@playwright/test';
import fs from 'fs';
import path from 'path';

/**
 * 全局清理 - 测试结束后执行
 * 生成测试摘要、清理临时文件等
 */
async function globalTeardown(config: FullConfig) {
  console.log('\n🧹 开始全局清理...');
  
  // 生成测试摘要
  const reportDir = path.join(__dirname, 'playwright-report');
  const resultsPath = path.join(reportDir, 'results.json');
  
  if (fs.existsSync(resultsPath)) {
    try {
      const results = JSON.parse(fs.readFileSync(resultsPath, 'utf-8'));
      
      // 统计测试结果
      const stats = {
        total: results.suites?.reduce((acc, suite) => acc + (suite.specs?.length || 0), 0) || 0,
        passed: 0,
        failed: 0,
        skipped: 0,
        flaky: 0
      };
      
      results.suites?.forEach(suite => {
        suite.specs?.forEach(spec => {
          spec.tests?.forEach(test => {
            const status = test.results?.[0]?.status;
            if (status === 'passed') stats.passed++;
            else if (status === 'failed') stats.failed++;
            else if (status === 'skipped') stats.skipped++;
            else if (status === 'flaky') stats.flaky++;
          });
        });
      });
      
      // 输出摘要
      console.log('\n📊 测试摘要:');
      console.log(`   总计: ${stats.total}`);
      console.log(`   ✅ 通过: ${stats.passed}`);
      console.log(`   ❌ 失败: ${stats.failed}`);
      console.log(`   ⏭️ 跳过: ${stats.skipped}`);
      console.log(`   🔄 不稳定: ${stats.flaky}`);
      
      // 保存摘要到文件
      const summaryPath = path.join(reportDir, 'summary.txt');
      const summary = `
测试执行摘要
============
执行时间: ${new Date().toLocaleString()}
总计: ${stats.total}
通过: ${stats.passed}
失败: ${stats.failed}
跳过: ${stats.skipped}
不稳定: ${stats.flaky}

通过率: ${stats.total > 0 ? ((stats.passed / stats.total) * 100).toFixed(2) : 0}%
`;
      fs.writeFileSync(summaryPath, summary);
      console.log(`\n📝 摘要已保存: ${summaryPath}`);
      
    } catch (error) {
      console.warn('⚠️ 解析测试结果失败:', error.message);
    }
  }
  
  console.log('✅ 全局清理完成');
}

export default globalTeardown;
