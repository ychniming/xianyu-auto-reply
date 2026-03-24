import { Page } from '@playwright/test';
import { BasePage } from '../fixtures/base-page';
import { Selectors, URLs, Timeouts } from '../fixtures/test-data';

/**
 * 仪表盘页面对象
 * 封装仪表盘页面的所有操作
 */
export class DashboardPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  /**
   * 导航到仪表盘页面
   */
  async goto() {
    await super.goto(URLs.index);
    await this.waitForPageLoad();
  }

  /**
   * 点击导航菜单项
   */
  async clickNavMenu(menuName: 'dashboard' | 'accounts' | 'items' | 'auto-reply' | 'cards' | 'auto-delivery' | 'notifications' | 'messages' | 'settings') {
    const selector = Selectors.nav[menuName];
    await this.click(selector);
    await this.wait(Timeouts.short);
  }

  /**
   * 点击仪表盘菜单
   */
  async clickDashboard() {
    await this.clickNavMenu('dashboard');
  }

  /**
   * 点击账号管理菜单
   */
  async clickAccounts() {
    await this.clickNavMenu('accounts');
  }

  /**
   * 点击商品管理菜单
   */
  async clickItems() {
    await this.clickNavMenu('items');
  }

  /**
   * 点击自动回复菜单
   */
  async clickAutoReply() {
    await this.clickNavMenu('auto-reply');
  }

  /**
   * 点击卡券管理菜单
   */
  async clickCards() {
    await this.clickNavMenu('cards');
  }

  /**
   * 点击自动发货菜单
   */
  async clickAutoDelivery() {
    await this.clickNavMenu('auto-delivery');
  }

  /**
   * 点击通知渠道菜单
   */
  async clickNotifications() {
    await this.clickNavMenu('notifications');
  }

  /**
   * 点击消息通知菜单
   */
  async clickMessages() {
    await this.clickNavMenu('messages');
  }

  /**
   * 点击系统设置菜单
   */
  async clickSettings() {
    await this.clickNavMenu('settings');
  }

  /**
   * 点击登出
   */
  async clickLogout() {
    await this.click(Selectors.nav.logout);
    await this.wait(Timeouts.medium);
  }

  /**
   * 点击移动端菜单切换按钮
   */
  async toggleMobileMenu() {
    await this.click(Selectors.nav.mobileToggle);
    await this.wait(Timeouts.short);
  }

  /**
   * 验证侧边栏是否显示
   */
  async expectSidebarVisible() {
    await this.expectToBeVisible(Selectors.nav.sidebar);
  }

  /**
   * 验证仪表盘部分是否显示
   */
  async expectDashboardSectionVisible() {
    await this.expectToBeVisible('#dashboard-section');
  }

  /**
   * 验证账号管理部分是否显示
   */
  async expectAccountsSectionVisible() {
    await this.expectToBeVisible('#accounts-section');
  }

  /**
   * 验证商品管理部分是否显示
   */
  async expectItemsSectionVisible() {
    await this.expectToBeVisible('#items-section');
  }

  /**
   * 验证自动回复部分是否显示
   */
  async expectAutoReplySectionVisible() {
    await this.expectToBeVisible('#auto-reply-section');
  }

  /**
   * 验证卡券管理部分是否显示
   */
  async expectCardsSectionVisible() {
    await this.expectToBeVisible('#cards-section');
  }

  /**
   * 验证自动发货部分是否显示
   */
  async expectAutoDeliverySectionVisible() {
    await this.expectToBeVisible('#auto-delivery-section');
  }

  /**
   * 验证通知渠道部分是否显示
   */
  async expectNotificationsSectionVisible() {
    await this.expectToBeVisible('#notification-channels-section');
  }

  /**
   * 验证消息通知部分是否显示
   */
  async expectMessagesSectionVisible() {
    await this.expectToBeVisible('#message-notifications-section');
  }

  /**
   * 验证系统设置部分是否显示
   */
  async expectSettingsSectionVisible() {
    await this.expectToBeVisible('#system-settings-section');
  }

  /**
   * 获取统计卡片数量
   */
  async getStatCardCount(): Promise<number> {
    return await this.getElementCount('.stat-card');
  }

  /**
   * 获取总账号数
   */
  async getTotalAccounts(): Promise<string> {
    return await this.getText('#totalAccounts');
  }

  /**
   * 获取总关键词数
   */
  async getTotalKeywords(): Promise<string> {
    return await this.getText('#totalKeywords');
  }

  /**
   * 获取启用账号数
   */
  async getActiveAccounts(): Promise<string> {
    return await this.getText('#activeAccounts');
  }

  /**
   * 验证登出后跳转到登录页面
   */
  async expectRedirectToLogin() {
    await this.expectUrlToContain('login.html');
  }

  /**
   * 等待仪表盘数据加载完成
   */
  async waitForDashboardData() {
    await this.waitForLoadingToFinish();
    // 等待统计数据加载
    await this.page.waitForFunction(() => {
      const totalAccounts = document.getElementById('totalAccounts');
      return totalAccounts && totalAccounts.textContent !== '0' || totalAccounts?.textContent === '0';
    }, { timeout: Timeouts.long });
  }
}
