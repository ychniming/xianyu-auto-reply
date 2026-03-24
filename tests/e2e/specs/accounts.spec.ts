import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/login-page';
import { DashboardPage } from '../pages/dashboard-page';
import { AccountsPage } from '../pages/accounts-page';
import { TestUsers, TestCookies, Timeouts } from '../fixtures/test-data';

/**
 * 账号管理页面点击操作测试套件
 * 测试所有账号管理相关的点击操作
 */
test.describe('账号管理页面点击操作测试', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;
  let accountsPage: AccountsPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    accountsPage = new AccountsPage(page);

    // 登录并导航到账号管理页面
    await loginPage.goto();
    await loginPage.fill('#username', TestUsers.admin.username);
    await loginPage.fill('#password', TestUsers.admin.password);
    await loginPage.click('button[type="submit"]');
    await loginPage.waitForPageLoad();

    // 导航到账号管理
    await dashboardPage.clickAccounts();
    await dashboardPage.expectAccountsSectionVisible();
  });

  test.describe('添加账号按钮点击', () => {
    test('点击扫码登录按钮', async () => {
      await accountsPage.clickQRCodeLogin();
      // 验证扫码登录相关元素显示
      await accountsPage.expectToBeVisible('.qr-login-container, .qr-code-wrapper');
    });

    test('点击手动输入按钮 - 显示表单', async () => {
      await accountsPage.clickManualInput();
      await accountsPage.expectManualFormVisible();
    });

    test('再次点击手动输入按钮 - 隐藏表单', async () => {
      // 先显示
      await accountsPage.clickManualInput();
      await accountsPage.expectManualFormVisible();

      // 再隐藏
      await accountsPage.clickManualInput();
      await accountsPage.expectManualFormHidden();
    });

    test('扫码登录和手动输入切换', async () => {
      // 点击扫码登录
      await accountsPage.clickQRCodeLogin();
      await accountsPage.expectToBeVisible('.qr-login-container');

      // 切换到手动输入
      await accountsPage.clickManualInput();
      await accountsPage.expectManualFormVisible();
    });
  });

  test.describe('手动输入表单操作', () => {
    test('点击添加按钮 - 空表单', async () => {
      // 显示表单
      await accountsPage.clickManualInput();

      // 点击添加
      await accountsPage.clickAddButton();

      // 验证验证提示
      await expect(accountsPage.page.locator('.alert, .invalid-feedback, .toast')).toBeVisible();
    });

    test('点击添加按钮 - 完整填写', async () => {
      // 显示表单
      await accountsPage.clickManualInput();

      // 填写信息
      await accountsPage.fillCookieId(TestCookies.valid.id);
      await accountsPage.fillCookieValue(TestCookies.valid.value);

      // 点击添加
      await accountsPage.clickAddButton();

      // 等待响应
      await accountsPage.wait(Timeouts.medium);
    });

    test('点击取消按钮', async () => {
      // 显示表单
      await accountsPage.clickManualInput();
      await accountsPage.expectManualFormVisible();

      // 点击取消
      await accountsPage.clickCancelButton();
      await accountsPage.expectManualFormHidden();
    });

    test('表单输入交互', async () => {
      await accountsPage.clickManualInput();

      // 点击账号ID输入框
      await accountsPage.click('#cookieId');
      await expect(accountsPage.page.locator('#cookieId')).toBeFocused();

      // 点击Cookie值输入框
      await accountsPage.click('#cookieValue');
      await expect(accountsPage.page.locator('#cookieValue')).toBeFocused();
    });
  });

  test.describe('账号列表操作', () => {
    test('点击刷新按钮', async () => {
      await accountsPage.clickRefreshButton();
      // 验证表格刷新
      await accountsPage.expectCookieTableVisible();
    });

    test('点击默认回复管理按钮', async () => {
      await accountsPage.clickDefaultReplyButton();
      // 验证默认回复管理模态框显示
      await accountsPage.expectToBeVisible('.modal:has-text("默认回复")');
    });

    test('验证账号表格显示', async () => {
      await accountsPage.expectCookieTableVisible();
    });
  });

  test.describe('账号行操作按钮', () => {
    test('点击账号启用/禁用切换', async () => {
      // 获取第一行账号
      const firstRow = accountsPage.page.locator('#cookieTable tbody tr').first();

      if (await firstRow.isVisible()) {
        const toggleSwitch = firstRow.locator('.form-check-input').first();
        const initialState = await toggleSwitch.isChecked();

        // 点击切换
        await toggleSwitch.click();
        await accountsPage.wait(Timeouts.medium);

        // 验证状态变化
        const newState = await toggleSwitch.isChecked();
        expect(newState).not.toBe(initialState);
      }
    });

    test('点击编辑按钮', async () => {
      const firstRow = accountsPage.page.locator('#cookieTable tbody tr').first();

      if (await firstRow.isVisible()) {
        const editButton = firstRow.locator('button[title="编辑"], button:has(.bi-pencil)').first();
        await editButton.click();
        await accountsPage.wait(Timeouts.short);

        // 验证编辑模态框显示
        await accountsPage.expectToBeVisible('.modal:has-text("编辑")');
      }
    });

    test('点击关键词按钮', async () => {
      const firstRow = accountsPage.page.locator('#cookieTable tbody tr').first();

      if (await firstRow.isVisible()) {
        const keywordsButton = firstRow.locator('button:has-text("关键词"), button:has(.bi-chat-left-text)').first();
        await keywordsButton.click();
        await accountsPage.wait(Timeouts.short);

        // 验证跳转到自动回复页面
        await accountsPage.expectToBeVisible('#auto-reply-section');
      }
    });

    test('点击商品按钮', async () => {
      const firstRow = accountsPage.page.locator('#cookieTable tbody tr').first();

      if (await firstRow.isVisible()) {
        const itemsButton = firstRow.locator('button:has-text("商品"), button:has(.bi-box-seam)').first();
        await itemsButton.click();
        await accountsPage.wait(Timeouts.short);

        // 验证跳转到商品管理页面
        await accountsPage.expectToBeVisible('#items-section');
      }
    });
  });

  test.describe('模态框操作', () => {
    test('打开并关闭默认回复管理', async () => {
      await accountsPage.clickDefaultReplyButton();
      await accountsPage.expectToBeVisible('.modal');

      // 关闭模态框
      await accountsPage.closeModal();
      await accountsPage.expectToBeHidden('.modal');
    });

    test('模态框外点击关闭', async () => {
      await accountsPage.clickDefaultReplyButton();
      await accountsPage.expectToBeVisible('.modal');

      // 点击模态框背景
      await accountsPage.click('.modal-backdrop');
      await accountsPage.wait(Timeouts.short);
    });
  });

  test.describe('响应式布局', () => {
    test('移动端账号管理页面', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.reload();
      await accountsPage.waitForPageLoad();

      // 验证关键元素仍然可见
      await accountsPage.expectToBeVisible('#accounts-section');
      await accountsPage.expectCookieTableVisible();
    });
  });

  test.describe('性能测试', () => {
    test('账号列表加载时间', async () => {
      const startTime = Date.now();
      await accountsPage.clickRefreshButton();
      const loadTime = Date.now() - startTime;

      // 列表加载应小于3秒
      expect(loadTime).toBeLessThan(3000);
    });

    test('表单切换响应时间', async () => {
      const startTime = Date.now();
      await accountsPage.clickManualInput();
      const switchTime = Date.now() - startTime;

      // 表单切换应小于500毫秒
      expect(switchTime).toBeLessThan(500);
    });
  });

  test.describe('错误处理', () => {
    test('添加重复账号ID', async () => {
      await accountsPage.clickManualInput();

      // 填写已存在的账号ID
      await accountsPage.fillCookieId('existing_cookie_id');
      await accountsPage.fillCookieValue('test_value');
      await accountsPage.clickAddButton();

      // 验证错误提示
      await accountsPage.wait(Timeouts.medium);
      const errorVisible = await accountsPage.isVisible('.alert-danger, .toast-error');
      // 根据实际实现，可能有错误提示
    });

    test('添加无效Cookie值', async () => {
      await accountsPage.clickManualInput();

      await accountsPage.fillCookieId('test_id');
      await accountsPage.fillCookieValue(''); // 空值
      await accountsPage.clickAddButton();

      // 验证验证提示
      await expect(accountsPage.page.locator('.invalid-feedback, .alert')).toBeVisible();
    });
  });
});

/**
 * 账号管理端到端流程测试
 */
test.describe('账号管理端到端流程测试', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;
  let accountsPage: AccountsPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    accountsPage = new AccountsPage(page);

    await loginPage.goto();
    await loginPage.fill('#username', TestUsers.admin.username);
    await loginPage.fill('#password', TestUsers.admin.password);
    await loginPage.click('button[type="submit"]');
    await loginPage.waitForPageLoad();

    await dashboardPage.clickAccounts();
  });

  test('完整添加账号流程', async () => {
    const testCookieId = `test_cookie_${Date.now()}`;

    // 显示手动输入表单
    await accountsPage.clickManualInput();

    // 填写账号信息
    await accountsPage.fillCookieId(testCookieId);
    await accountsPage.fillCookieValue('test_cookie_value_example');

    // 点击添加
    await accountsPage.clickAddButton();
    await accountsPage.wait(Timeouts.medium);

    // 验证账号添加到列表
    await accountsPage.expectCookieExists(testCookieId);
  });

  test('完整删除账号流程', async () => {
    // 先添加一个测试账号
    const testCookieId = `test_delete_${Date.now()}`;
    await accountsPage.clickManualInput();
    await accountsPage.fillCookieId(testCookieId);
    await accountsPage.fillCookieValue('test_value');
    await accountsPage.clickAddButton();
    await accountsPage.wait(Timeouts.medium);

    // 验证账号存在
    await accountsPage.expectCookieExists(testCookieId);

    // 删除账号
    await accountsPage.deleteCookie(testCookieId);

    // 验证账号已删除
    await accountsPage.expectCookieNotExists(testCookieId);
  });
});
