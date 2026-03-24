import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/login-page';
import { DashboardPage } from '../pages/dashboard-page';
import { KeywordsPage } from '../pages/keywords-page';
import { TestUsers, TestKeywords, Timeouts } from '../fixtures/test-data';

/**
 * 关键词管理页面点击操作测试套件
 * 测试所有关键词管理相关的点击操作
 */
test.describe('关键词管理页面点击操作测试', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;
  let keywordsPage: KeywordsPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    keywordsPage = new KeywordsPage(page);

    // 登录并导航到自动回复页面
    await loginPage.goto();
    await loginPage.fill('#username', TestUsers.admin.username);
    await loginPage.fill('#password', TestUsers.admin.password);
    await loginPage.click('button[type="submit"]');
    await loginPage.waitForPageLoad();

    // 导航到自动回复页面
    await dashboardPage.clickAutoReply();
    await dashboardPage.expectAutoReplySectionVisible();
  });

  test.describe('账号选择', () => {
    test('点击账号下拉框', async () => {
      await keywordsPage.click('#accountSelect');
      await expect(keywordsPage.page.locator('#accountSelect')).toBeFocused();
    });

    test('选择账号', async () => {
      // 获取第一个可用选项
      const options = await keywordsPage.page.locator('#accountSelect option').all();
      if (options.length > 1) {
        const firstValue = await options[1].getAttribute('value');
        if (firstValue) {
          await keywordsPage.selectAccount(firstValue);
          await keywordsPage.expectKeywordManagementVisible();
        }
      }
    });

    test('点击刷新账号列表按钮', async () => {
      await keywordsPage.refreshAccountList();
      // 验证下拉框刷新
      await keywordsPage.expectToBeVisible('#accountSelect');
    });
  });

  test.describe('关键词添加', () => {
    test('点击添加文本关键词按钮 - 空表单', async () => {
      // 先选择一个账号
      const options = await keywordsPage.page.locator('#accountSelect option').all();
      if (options.length > 1) {
        const firstValue = await options[1].getAttribute('value');
        if (firstValue) {
          await keywordsPage.selectAccount(firstValue);
        }
      }

      // 点击添加按钮（不填写内容）
      await keywordsPage.clickAddTextKeyword();

      // 验证验证提示
      await expect(keywordsPage.page.locator('.alert, .invalid-feedback, .toast')).toBeVisible();
    });

    test('填写关键词并添加', async () => {
      // 选择账号
      const options = await keywordsPage.page.locator('#accountSelect option').all();
      if (options.length > 1) {
        const firstValue = await options[1].getAttribute('value');
        if (firstValue) {
          await keywordsPage.selectAccount(firstValue);
        }
      }

      // 填写关键词信息
      await keywordsPage.fillKeyword(TestKeywords.text.keyword);
      await keywordsPage.fillReply(TestKeywords.text.reply);
      await keywordsPage.selectMatchType(TestKeywords.text.matchType);
      await keywordsPage.fillPriority(TestKeywords.text.priority);

      // 点击添加
      await keywordsPage.clickAddTextKeyword();
      await keywordsPage.wait(Timeouts.medium);
    });

    test('点击添加图片关键词按钮', async () => {
      // 选择账号
      const options = await keywordsPage.page.locator('#accountSelect option').all();
      if (options.length > 1) {
        const firstValue = await options[1].getAttribute('value');
        if (firstValue) {
          await keywordsPage.selectAccount(firstValue);
        }
      }

      await keywordsPage.clickAddImageKeyword();
      // 验证图片关键词模态框显示
      await keywordsPage.expectToBeVisible('.modal:has-text("图片")');
    });
  });

  test.describe('匹配类型选择', () => {
    test('选择包含匹配', async () => {
      await keywordsPage.selectMatchType('contains');
      const value = await keywordsPage.page.locator('#newMatchType').inputValue();
      expect(value).toBe('contains');
    });

    test('选择精确匹配', async () => {
      await keywordsPage.selectMatchType('exact');
      const value = await keywordsPage.page.locator('#newMatchType').inputValue();
      expect(value).toBe('exact');
    });

    test('选择正则表达式匹配', async () => {
      await keywordsPage.selectMatchType('regex');
      const value = await keywordsPage.page.locator('#newMatchType').inputValue();
      expect(value).toBe('regex');
    });

    test('选择模糊匹配', async () => {
      await keywordsPage.selectMatchType('fuzzy');
      const value = await keywordsPage.page.locator('#newMatchType').inputValue();
      expect(value).toBe('fuzzy');
    });
  });

  test.describe('回复模式选择', () => {
    test('选择单条回复', async () => {
      await keywordsPage.selectReplyMode('single');
      const value = await keywordsPage.page.locator('#newReplyMode').inputValue();
      expect(value).toBe('single');
    });

    test('选择随机回复', async () => {
      await keywordsPage.selectReplyMode('random');
      const value = await keywordsPage.page.locator('#newReplyMode').inputValue();
      expect(value).toBe('random');
    });

    test('选择顺序回复', async () => {
      await keywordsPage.selectReplyMode('sequence');
      const value = await keywordsPage.page.locator('#newReplyMode').inputValue();
      expect(value).toBe('sequence');
    });
  });

  test.describe('高级条件设置', () => {
    test('点击展开高级条件', async () => {
      // 选择账号
      const options = await keywordsPage.page.locator('#accountSelect option').all();
      if (options.length > 1) {
        const firstValue = await options[1].getAttribute('value');
        if (firstValue) {
          await keywordsPage.selectAccount(firstValue);
        }
      }

      await keywordsPage.toggleAdvancedConditions();
      await keywordsPage.expectAdvancedConditionsExpanded();
    });

    test('点击收起高级条件', async () => {
      // 选择账号
      const options = await keywordsPage.page.locator('#accountSelect option').all();
      if (options.length > 1) {
        const firstValue = await options[1].getAttribute('value');
        if (firstValue) {
          await keywordsPage.selectAccount(firstValue);
        }
      }

      // 展开
      await keywordsPage.toggleAdvancedConditions();
      await keywordsPage.expectAdvancedConditionsExpanded();

      // 收起
      await keywordsPage.toggleAdvancedConditions();
      await keywordsPage.expectAdvancedConditionsCollapsed();
    });

    test('设置时间范围', async () => {
      // 选择账号并展开高级条件
      const options = await keywordsPage.page.locator('#accountSelect option').all();
      if (options.length > 1) {
        const firstValue = await options[1].getAttribute('value');
        if (firstValue) {
          await keywordsPage.selectAccount(firstValue);
        }
      }

      await keywordsPage.toggleAdvancedConditions();
      await keywordsPage.setTimeRange(9, 18);

      const startValue = await keywordsPage.page.locator('#timeStartHour').inputValue();
      const endValue = await keywordsPage.page.locator('#timeEndHour').inputValue();

      expect(startValue).toBe('9');
      expect(endValue).toBe('18');
    });

    test('设置排除关键词', async () => {
      const options = await keywordsPage.page.locator('#accountSelect option').all();
      if (options.length > 1) {
        const firstValue = await options[1].getAttribute('value');
        if (firstValue) {
          await keywordsPage.selectAccount(firstValue);
        }
      }

      await keywordsPage.toggleAdvancedConditions();
      await keywordsPage.setExcludeKeywords('已购买,不想要');

      const value = await keywordsPage.page.locator('#excludeKeywords').inputValue();
      expect(value).toBe('已购买,不想要');
    });

    test('设置触发次数限制', async () => {
      const options = await keywordsPage.page.locator('#accountSelect option').all();
      if (options.length > 1) {
        const firstValue = await options[1].getAttribute('value');
        if (firstValue) {
          await keywordsPage.selectAccount(firstValue);
        }
      }

      await keywordsPage.toggleAdvancedConditions();
      await keywordsPage.setMaxTriggerCount(3);

      const value = await keywordsPage.page.locator('#maxTriggerCount').inputValue();
      expect(value).toBe('3');
    });

    test('选择用户类型', async () => {
      const options = await keywordsPage.page.locator('#accountSelect option').all();
      if (options.length > 1) {
        const firstValue = await options[1].getAttribute('value');
        if (firstValue) {
          await keywordsPage.selectAccount(firstValue);
        }
      }

      await keywordsPage.toggleAdvancedConditions();
      await keywordsPage.selectUserType('new');

      const value = await keywordsPage.page.locator('#userType').inputValue();
      expect(value).toBe('new');
    });
  });

  test.describe('关键词测试工具', () => {
    test('点击测试按钮 - 空消息', async () => {
      // 选择账号
      const options = await keywordsPage.page.locator('#accountSelect option').all();
      if (options.length > 1) {
        const firstValue = await options[1].getAttribute('value');
        if (firstValue) {
          await keywordsPage.selectAccount(firstValue);
        }
      }

      await keywordsPage.clickTestButton();
      // 验证提示
      await expect(keywordsPage.page.locator('.alert, .toast')).toBeVisible();
    });

    test('填写测试消息并测试', async () => {
      // 选择账号
      const options = await keywordsPage.page.locator('#accountSelect option').all();
      if (options.length > 1) {
        const firstValue = await options[1].getAttribute('value');
        if (firstValue) {
          await keywordsPage.selectAccount(firstValue);
        }
      }

      await keywordsPage.fillTestMessage('你好，这个多少钱？');
      await keywordsPage.clickTestButton();
      await keywordsPage.wait(Timeouts.medium);

      // 验证测试结果
      const result = await keywordsPage.getTestResult();
      expect(result).toBeTruthy();
    });
  });

  test.describe('导入导出功能', () => {
    test('点击导出按钮', async () => {
      // 选择账号
      const options = await keywordsPage.page.locator('#accountSelect option').all();
      if (options.length > 1) {
        const firstValue = await options[1].getAttribute('value');
        if (firstValue) {
          await keywordsPage.selectAccount(firstValue);
        }
      }

      await keywordsPage.clickExport();
      // 验证导出操作（可能有下载或提示）
      await keywordsPage.wait(Timeouts.medium);
    });

    test('点击导入按钮', async () => {
      // 选择账号
      const options = await keywordsPage.page.locator('#accountSelect option').all();
      if (options.length > 1) {
        const firstValue = await options[1].getAttribute('value');
        if (firstValue) {
          await keywordsPage.selectAccount(firstValue);
        }
      }

      await keywordsPage.clickImport();
      // 验证导入模态框显示
      await keywordsPage.expectToBeVisible('.modal:has-text("导入")');
    });
  });

  test.describe('关键词列表操作', () => {
    test('验证关键词列表显示', async () => {
      // 选择账号
      const options = await keywordsPage.page.locator('#accountSelect option').all();
      if (options.length > 1) {
        const firstValue = await options[1].getAttribute('value');
        if (firstValue) {
          await keywordsPage.selectAccount(firstValue);
        }
      }

      await keywordsPage.expectKeywordsListVisible();
    });

    test('点击关键词编辑按钮', async () => {
      // 选择账号
      const options = await keywordsPage.page.locator('#accountSelect option').all();
      if (options.length > 1) {
        const firstValue = await options[1].getAttribute('value');
        if (firstValue) {
          await keywordsPage.selectAccount(firstValue);
        }
      }

      // 获取第一个关键词的编辑按钮
      const editButton = keywordsPage.page.locator('.keyword-item .edit-btn, .keyword-card .edit-btn').first();
      if (await editButton.isVisible()) {
        await editButton.click();
        await keywordsPage.expectToBeVisible('.modal:has-text("编辑")');
      }
    });

    test('点击关键词删除按钮', async () => {
      // 选择账号
      const options = await keywordsPage.page.locator('#accountSelect option').all();
      if (options.length > 1) {
        const firstValue = await options[1].getAttribute('value');
        if (firstValue) {
          await keywordsPage.selectAccount(firstValue);
        }
      }

      // 获取第一个关键词的删除按钮
      const deleteButton = keywordsPage.page.locator('.keyword-item .delete-btn, .keyword-card .delete-btn').first();
      if (await deleteButton.isVisible()) {
        await deleteButton.click();
        await keywordsPage.expectToBeVisible('.modal:has-text("确认")');
      }
    });
  });

  test.describe('响应式布局', () => {
    test('移动端关键词管理页面', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.reload();
      await keywordsPage.waitForPageLoad();

      // 验证关键元素仍然可见
      await keywordsPage.expectToBeVisible('#auto-reply-section');
      await keywordsPage.expectToBeVisible('#accountSelect');
    });
  });

  test.describe('性能测试', () => {
    test('账号选择响应时间', async () => {
      const options = await keywordsPage.page.locator('#accountSelect option').all();
      if (options.length > 1) {
        const firstValue = await options[1].getAttribute('value');
        if (firstValue) {
          const startTime = Date.now();
          await keywordsPage.selectAccount(firstValue);
          const switchTime = Date.now() - startTime;

          // 账号选择应小于2秒
          expect(switchTime).toBeLessThan(2000);
        }
      }
    });

    test('关键词添加响应时间', async () => {
      // 选择账号
      const options = await keywordsPage.page.locator('#accountSelect option').all();
      if (options.length > 1) {
        const firstValue = await options[1].getAttribute('value');
        if (firstValue) {
          await keywordsPage.selectAccount(firstValue);
        }
      }

      await keywordsPage.fillKeyword('性能测试关键词');
      await keywordsPage.fillReply('性能测试回复');

      const startTime = Date.now();
      await keywordsPage.clickAddTextKeyword();
      const addTime = Date.now() - startTime;

      // 关键词添加应小于3秒
      expect(addTime).toBeLessThan(3000);
    });
  });
});

/**
 * 关键词管理端到端流程测试
 */
test.describe('关键词管理端到端流程测试', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;
  let keywordsPage: KeywordsPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    keywordsPage = new KeywordsPage(page);

    await loginPage.goto();
    await loginPage.fill('#username', TestUsers.admin.username);
    await loginPage.fill('#password', TestUsers.admin.password);
    await loginPage.click('button[type="submit"]');
    await loginPage.waitForPageLoad();

    await dashboardPage.clickAutoReply();
  });

  test('完整添加关键词流程', async () => {
    const testKeyword = `测试关键词_${Date.now()}`;

    // 选择账号
    const options = await keywordsPage.page.locator('#accountSelect option').all();
    if (options.length > 1) {
      const firstValue = await options[1].getAttribute('value');
      if (firstValue) {
        await keywordsPage.selectAccount(firstValue);
      }
    }

    // 填写关键词信息
    await keywordsPage.fillKeyword(testKeyword);
    await keywordsPage.fillReply('这是测试回复内容');
    await keywordsPage.selectMatchType('contains');
    await keywordsPage.fillPriority(50);

    // 添加关键词
    await keywordsPage.clickAddTextKeyword();
    await keywordsPage.wait(Timeouts.medium);

    // 验证关键词添加到列表
    await keywordsPage.expectKeywordExists(testKeyword);
  });

  test('完整关键词测试流程', async () => {
    // 选择账号
    const options = await keywordsPage.page.locator('#accountSelect option').all();
    if (options.length > 1) {
      const firstValue = await options[1].getAttribute('value');
      if (firstValue) {
        await keywordsPage.selectAccount(firstValue);
      }
    }

    // 填写测试消息
    await keywordsPage.fillTestMessage('你好，请问这个多少钱？');
    await keywordsPage.clickTestButton();
    await keywordsPage.wait(Timeouts.medium);

    // 验证有测试结果
    const result = await keywordsPage.getTestResult();
    expect(result).toBeTruthy();
  });
});
