import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/login-page';
import { DashboardPage } from '../pages/dashboard-page';
import { TestUsers, Timeouts } from '../fixtures/test-data';

/**
 * 导航菜单点击操作测试套件
 * 测试所有导航相关的点击操作
 */
test.describe('导航菜单点击操作测试', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    
    // 登录并导航到首页
    await loginPage.goto();
    await loginPage.fill('#username', TestUsers.admin.username);
    await loginPage.fill('#password', TestUsers.admin.password);
    await loginPage.click('button[type="submit"]');
    await loginPage.waitForPageLoad();
  });

  test.describe('主导航菜单点击', () => {
    test('点击仪表盘菜单', async () => {
      await dashboardPage.clickDashboard();
      await dashboardPage.expectDashboardSectionVisible();
    });

    test('点击账号管理菜单', async () => {
      await dashboardPage.clickAccounts();
      await dashboardPage.expectAccountsSectionVisible();
    });

    test('点击商品管理菜单', async () => {
      await dashboardPage.clickItems();
      await dashboardPage.expectItemsSectionVisible();
    });

    test('点击自动回复菜单', async () => {
      await dashboardPage.clickAutoReply();
      await dashboardPage.expectAutoReplySectionVisible();
    });

    test('点击卡券管理菜单', async () => {
      await dashboardPage.clickCards();
      await dashboardPage.expectCardsSectionVisible();
    });

    test('点击自动发货菜单', async () => {
      await dashboardPage.clickAutoDelivery();
      await dashboardPage.expectAutoDeliverySectionVisible();
    });

    test('点击通知渠道菜单', async () => {
      await dashboardPage.clickNotifications();
      await dashboardPage.expectNotificationsSectionVisible();
    });

    test('点击消息通知菜单', async () => {
      await dashboardPage.clickMessages();
      await dashboardPage.expectMessagesSectionVisible();
    });

    test('点击系统设置菜单', async () => {
      await dashboardPage.clickSettings();
      await dashboardPage.expectSettingsSectionVisible();
    });
  });

  test.describe('导航菜单切换', () => {
    test('连续切换多个菜单', async () => {
      // 仪表盘 -> 账号管理
      await dashboardPage.clickAccounts();
      await dashboardPage.expectAccountsSectionVisible();

      // 账号管理 -> 商品管理
      await dashboardPage.clickItems();
      await dashboardPage.expectItemsSectionVisible();

      // 商品管理 -> 自动回复
      await dashboardPage.clickAutoReply();
      await dashboardPage.expectAutoReplySectionVisible();

      // 自动回复 -> 仪表盘
      await dashboardPage.clickDashboard();
      await dashboardPage.expectDashboardSectionVisible();
    });

    test('快速切换菜单', async () => {
      const menus = ['accounts', 'items', 'auto-reply', 'cards', 'settings'];
      
      for (const menu of menus) {
        await dashboardPage.clickNavMenu(menu as any);
        await dashboardPage.wait(200);
      }
      
      // 最后验证当前显示的是最后一个菜单
      await dashboardPage.expectSettingsSectionVisible();
    });
  });

  test.describe('移动端导航', () => {
    test('移动端菜单切换按钮', async ({ page }) => {
      // 设置移动端视口
      await page.setViewportSize({ width: 375, height: 667 });
      await page.reload();
      await dashboardPage.waitForPageLoad();

      // 点击移动端菜单切换
      await dashboardPage.toggleMobileMenu();
      
      // 验证侧边栏状态变化
      const sidebar = page.locator('#sidebar');
      const hasCollapsedClass = await sidebar.evaluate(el => el.classList.contains('collapsed'));
      expect(hasCollapsedClass).toBeTruthy();
    });

    test('移动端导航菜单点击', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.reload();
      await dashboardPage.waitForPageLoad();

      // 展开菜单
      await dashboardPage.toggleMobileMenu();
      
      // 点击账号管理
      await dashboardPage.clickAccounts();
      await dashboardPage.expectAccountsSectionVisible();
    });
  });

  test.describe('登出功能', () => {
    test('点击登出按钮', async () => {
      await dashboardPage.clickLogout();
      await dashboardPage.expectRedirectToLogin();
    });

    test('登出后访问受保护页面', async () => {
      // 先登出
      await dashboardPage.clickLogout();
      await dashboardPage.expectRedirectToLogin();
      
      // 尝试直接访问首页
      await dashboardPage.goto();
      
      // 应该被重定向到登录页
      await dashboardPage.expectUrlToContain('login.html');
    });
  });

  test.describe('外部链接', () => {
    test('点击商品搜索链接', async ({ page, context }) => {
      // 监听新页面打开
      const [newPage] = await Promise.all([
        context.waitForEvent('page'),
        page.click('a[href="/item_search.html"]')
      ]);
      
      await newPage.waitForLoadState();
      expect(newPage.url()).toContain('item_search.html');
      await newPage.close();
    });

    test('点击用户管理链接（管理员）', async ({ page, context }) => {
      // 管理员应该能看到用户管理链接
      const userManagementLink = page.locator('a[href="/user_management.html"]');
      
      if (await userManagementLink.isVisible()) {
        const [newPage] = await Promise.all([
          context.waitForEvent('page'),
          userManagementLink.click()
        ]);
        
        await newPage.waitForLoadState();
        expect(newPage.url()).toContain('user_management.html');
        await newPage.close();
      }
    });
  });

  test.describe('导航状态保持', () => {
    test('刷新页面后保持当前菜单', async ({ page }) => {
      // 切换到账号管理
      await dashboardPage.clickAccounts();
      await dashboardPage.expectAccountsSectionVisible();
      
      // 刷新页面
      await page.reload();
      await dashboardPage.waitForPageLoad();
      
      // 验证仍然在账号管理页面
      await dashboardPage.expectAccountsSectionVisible();
    });
  });

  test.describe('导航性能', () => {
    test('菜单切换响应时间', async () => {
      const startTime = Date.now();
      await dashboardPage.clickAccounts();
      const switchTime = Date.now() - startTime;
      
      // 菜单切换应小于1秒
      expect(switchTime).toBeLessThan(1000);
    });

    test('页面加载时间', async ({ page }) => {
      const startTime = Date.now();
      await page.goto('/index.html');
      await page.waitForLoadState('networkidle');
      const loadTime = Date.now() - startTime;
      
      // 页面加载应小于3秒
      expect(loadTime).toBeLessThan(3000);
    });
  });

  test.describe('侧边栏交互', () => {
    test('侧边栏显示状态', async () => {
      await dashboardPage.expectSidebarVisible();
    });

    test('活动菜单项高亮', async ({ page }) => {
      // 点击账号管理
      await dashboardPage.clickAccounts();
      
      // 验证菜单项有活动状态
      const activeLink = page.locator('.nav-link.active');
      await expect(activeLink).toBeVisible();
      
      // 验证文本包含"账号"
      const linkText = await activeLink.textContent();
      expect(linkText).toContain('账号');
    });
  });
});
