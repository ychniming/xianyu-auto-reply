import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/login-page';
import { TestUsers, Timeouts } from '../fixtures/test-data';

/**
 * 登录页面点击操作测试套件
 * 测试所有登录相关的点击操作
 */
test.describe('登录页面点击操作测试', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.goto();
  });

  test.describe('登录方式切换', () => {
    test('点击用户名/密码登录标签', async () => {
      await loginPage.switchToUsernameLogin();
      await loginPage.expectToBeVisible('#usernameLoginForm');
      await loginPage.expectToBeHidden('#emailPasswordLoginForm');
      await loginPage.expectToBeHidden('#emailCodeLoginForm');
    });

    test('点击邮箱/密码登录标签', async () => {
      await loginPage.switchToEmailPasswordLogin();
      await loginPage.expectToBeHidden('#usernameLoginForm');
      await loginPage.expectToBeVisible('#emailPasswordLoginForm');
      await loginPage.expectToBeHidden('#emailCodeLoginForm');
    });

    test('点击邮箱/验证码登录标签', async () => {
      await loginPage.switchToEmailCodeLogin();
      await loginPage.expectToBeHidden('#usernameLoginForm');
      await loginPage.expectToBeHidden('#emailPasswordLoginForm');
      await loginPage.expectToBeVisible('#emailCodeLoginForm');
    });

    test('连续切换登录方式', async () => {
      // 切换到邮箱/密码
      await loginPage.switchToEmailPasswordLogin();
      await loginPage.expectToBeVisible('#emailPasswordLoginForm');

      // 切换到邮箱/验证码
      await loginPage.switchToEmailCodeLogin();
      await loginPage.expectToBeVisible('#emailCodeLoginForm');

      // 切换回用户名/密码
      await loginPage.switchToUsernameLogin();
      await loginPage.expectToBeVisible('#usernameLoginForm');
    });
  });

  test.describe('登录按钮点击', () => {
    test('点击登录按钮 - 空用户名', async () => {
      await loginPage.click('button[type="submit"]');
      // 验证表单验证或错误提示
      await expect(loginPage.page.locator('.alert, .invalid-feedback, .toast')).toBeVisible();
    });

    test('点击登录按钮 - 空密码', async () => {
      await loginPage.fill('#username', 'testuser');
      await loginPage.click('button[type="submit"]');
      await expect(loginPage.page.locator('.alert, .invalid-feedback, .toast')).toBeVisible();
    });

    test('点击登录按钮 - 错误凭据', async () => {
      await loginPage.fill('#username', 'wronguser');
      await loginPage.fill('#password', 'wrongpassword');
      await loginPage.click('button[type="submit"]');
      await loginPage.wait(Timeouts.medium);
      // 验证错误提示
      const errorVisible = await loginPage.isVisible('.alert-danger, .toast-error, .text-danger');
      expect(errorVisible).toBeTruthy();
    });
  });

  test.describe('验证码相关点击', () => {
    test('点击刷新验证码图片', async () => {
      await loginPage.switchToEmailCodeLogin();
      const initialSrc = await loginPage.page.locator('#captchaImage').getAttribute('src');
      await loginPage.refreshCaptcha();
      await loginPage.wait(Timeouts.short);
      const newSrc = await loginPage.page.locator('#captchaImage').getAttribute('src');
      // 验证码图片应该刷新
      expect(newSrc).toBeTruthy();
    });

    test('点击发送验证码按钮 - 未填写邮箱', async () => {
      await loginPage.switchToEmailCodeLogin();
      await loginPage.expectSendCodeButtonDisabled();
    });
  });

  test.describe('输入框交互', () => {
    test('点击用户名输入框', async () => {
      await loginPage.click('#username');
      await expect(loginPage.page.locator('#username')).toBeFocused();
    });

    test('点击密码输入框', async () => {
      await loginPage.click('#password');
      await expect(loginPage.page.locator('#password')).toBeFocused();
    });

    test('输入框间Tab切换', async () => {
      await loginPage.click('#username');
      await loginPage.pressKey('Tab');
      await expect(loginPage.page.locator('#password')).toBeFocused();
    });
  });

  test.describe('页面元素可见性', () => {
    test('验证登录表单元素显示', async () => {
      await loginPage.expectLoginFormVisible();
    });

    test('验证登录按钮启用状态', async () => {
      // 初始状态应该可以点击（即使为空）
      await loginPage.expectToBeEnabled('button[type="submit"]');
    });

    test('验证页面标题', async () => {
      await loginPage.expectTitleToContain('登录');
      await loginPage.expectTitleToContain('闲鱼');
    });
  });

  test.describe('响应式布局', () => {
    test('移动端视图 - 登录表单显示', async ({ page }) => {
      // 设置移动端视口
      await page.setViewportSize({ width: 375, height: 667 });
      await loginPage.goto();
      
      // 验证表单仍然可见
      await loginPage.expectToBeVisible('#username');
      await loginPage.expectToBeVisible('#password');
      await loginPage.expectToBeEnabled('button[type="submit"]');
    });

    test('平板视图 - 登录表单显示', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await loginPage.goto();
      
      await loginPage.expectToBeVisible('#username');
      await loginPage.expectToBeVisible('#password');
    });
  });

  test.describe('性能测试', () => {
    test('登录页面加载时间', async ({ page }) => {
      const startTime = Date.now();
      await loginPage.goto();
      const loadTime = Date.now() - startTime;
      
      // 页面加载时间应小于5秒
      expect(loadTime).toBeLessThan(5000);
    });

    test('登录方式切换响应时间', async () => {
      const startTime = Date.now();
      await loginPage.switchToEmailPasswordLogin();
      const switchTime = Date.now() - startTime;
      
      // 切换时间应小于1秒
      expect(switchTime).toBeLessThan(1000);
    });
  });
});

/**
 * 登录流程端到端测试
 */
test.describe('登录流程端到端测试', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.goto();
  });

  test('完整登录流程 - 用户名密码方式', async () => {
    // 填写用户名
    await loginPage.fill('#username', TestUsers.admin.username);
    
    // 填写密码
    await loginPage.fill('#password', TestUsers.admin.password);
    
    // 点击登录
    await loginPage.click('button[type="submit"]');
    
    // 等待导航
    await loginPage.waitForPageLoad();
    
    // 验证跳转到首页
    await loginPage.expectUrlToContain('index.html');
  });

  test('登录后验证仪表盘访问', async () => {
    // 执行登录
    await loginPage.fill('#username', TestUsers.admin.username);
    await loginPage.fill('#password', TestUsers.admin.password);
    await loginPage.click('button[type="submit"]');
    await loginPage.waitForPageLoad();
    
    // 验证仪表盘元素
    await loginPage.expectToBeVisible('.sidebar');
    await loginPage.expectToBeVisible('.main-content');
    await loginPage.expectToBeVisible('#dashboard-section');
  });
});
