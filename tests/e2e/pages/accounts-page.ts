import { Page } from '@playwright/test';
import { BasePage } from '../fixtures/base-page';
import { Selectors, TestCookies, Timeouts } from '../fixtures/test-data';

/**
 * 账号管理页面对象
 * 封装账号管理页面的所有操作
 */
export class AccountsPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  /**
   * 点击扫码登录按钮
   */
  async clickQRCodeLogin() {
    await this.click(Selectors.accounts.qrLoginButton);
    await this.wait(Timeouts.short);
  }

  /**
   * 点击手动输入按钮
   */
  async clickManualInput() {
    await this.click(Selectors.accounts.manualInputButton);
    await this.wait(Timeouts.short);
  }

  /**
   * 切换手动输入表单显示/隐藏
   */
  async toggleManualInput() {
    await this.click(Selectors.accounts.manualInputButton);
    await this.wait(Timeouts.short);
  }

  /**
   * 填写账号ID
   */
  async fillCookieId(cookieId: string) {
    await this.fill(Selectors.accounts.cookieIdInput, cookieId);
  }

  /**
   * 填写Cookie值
   */
  async fillCookieValue(cookieValue: string) {
    await this.fill(Selectors.accounts.cookieValueInput, cookieValue);
  }

  /**
   * 添加新账号
   */
  async addCookie(cookieId: string, cookieValue: string) {
    // 确保手动输入表单显示
    if (!await this.isVisible(Selectors.accounts.manualInputForm)) {
      await this.clickManualInput();
    }
    
    await this.fillCookieId(cookieId);
    await this.fillCookieValue(cookieValue);
    await this.click(Selectors.accounts.addButton);
    await this.wait(Timeouts.medium);
  }

  /**
   * 点击添加按钮
   */
  async clickAddButton() {
    await this.click(Selectors.accounts.addButton);
    await this.wait(Timeouts.medium);
  }

  /**
   * 点击取消按钮
   */
  async clickCancelButton() {
    await this.click(Selectors.accounts.cancelButton);
    await this.wait(Timeouts.short);
  }

  /**
   * 点击刷新按钮
   */
  async clickRefreshButton() {
    await this.click(Selectors.accounts.refreshButton);
    await this.wait(Timeouts.medium);
  }

  /**
   * 点击默认回复管理按钮
   */
  async clickDefaultReplyButton() {
    await this.click(Selectors.accounts.defaultReplyButton);
    await this.wait(Timeouts.short);
  }

  /**
   * 获取账号列表行数
   */
  async getCookieRowCount(): Promise<number> {
    return await this.getElementCount(Selectors.accounts.tableRows);
  }

  /**
   * 验证手动输入表单是否显示
   */
  async expectManualFormVisible() {
    await this.expectToBeVisible(Selectors.accounts.manualInputForm);
  }

  /**
   * 验证手动输入表单是否隐藏
   */
  async expectManualFormHidden() {
    await this.expectToBeHidden(Selectors.accounts.manualInputForm);
  }

  /**
   * 验证账号表格是否显示
   */
  async expectCookieTableVisible() {
    await this.expectToBeVisible(Selectors.accounts.cookieTable);
  }

  /**
   * 点击指定账号的操作按钮
   */
  async clickCookieAction(cookieId: string, action: 'edit' | 'delete' | 'toggle' | 'keywords' | 'items') {
    const row = this.page.locator(`${Selectors.accounts.tableRows}:has-text("${cookieId}")`);
    await row.waitFor({ state: 'visible' });
    
    let buttonSelector: string;
    switch (action) {
      case 'edit':
        buttonSelector = 'button[title="编辑"], button:has(.bi-pencil)';
        break;
      case 'delete':
        buttonSelector = 'button[title="删除"], button:has(.bi-trash)';
        break;
      case 'toggle':
        buttonSelector = '.form-check-input';
        break;
      case 'keywords':
        buttonSelector = 'button:has-text("关键词"), button:has(.bi-chat-left-text)';
        break;
      case 'items':
        buttonSelector = 'button:has-text("商品"), button:has(.bi-box-seam)';
        break;
      default:
        throw new Error(`未知的操作类型: ${action}`);
    }
    
    const button = row.locator(buttonSelector).first();
    await button.click();
    await this.wait(Timeouts.short);
  }

  /**
   * 切换账号启用状态
   */
  async toggleAccountStatus(cookieId: string) {
    await this.clickCookieAction(cookieId, 'toggle');
    await this.wait(Timeouts.medium);
  }

  /**
   * 删除账号
   */
  async deleteCookie(cookieId: string) {
    await this.clickCookieAction(cookieId, 'delete');
    // 等待确认对话框
    await this.waitForModal();
    await this.clickConfirm();
    await this.wait(Timeouts.medium);
  }

  /**
   * 编辑账号
   */
  async editCookie(cookieId: string) {
    await this.clickCookieAction(cookieId, 'edit');
    await this.wait(Timeouts.short);
  }

  /**
   * 管理账号关键词
   */
  async manageKeywords(cookieId: string) {
    await this.clickCookieAction(cookieId, 'keywords');
    await this.wait(Timeouts.short);
  }

  /**
   * 管理账号商品
   */
  async manageItems(cookieId: string) {
    await this.clickCookieAction(cookieId, 'items');
    await this.wait(Timeouts.short);
  }

  /**
   * 验证账号是否存在
   */
  async expectCookieExists(cookieId: string) {
    const row = this.page.locator(`${Selectors.accounts.tableRows}:has-text("${cookieId}")`);
    await expect(row).toBeVisible();
  }

  /**
   * 验证账号不存在
   */
  async expectCookieNotExists(cookieId: string) {
    const row = this.page.locator(`${Selectors.accounts.tableRows}:has-text("${cookieId}")`);
    await expect(row).toHaveCount(0);
  }

  /**
   * 获取指定账号的状态
   */
  async getCookieStatus(cookieId: string): Promise<string> {
    const row = this.page.locator(`${Selectors.accounts.tableRows}:has-text("${cookieId}")`);
    const statusCell = row.locator('td:nth-child(4)');
    return await statusCell.textContent() || '';
  }

  /**
   * 验证扫码登录模态框是否显示
   */
  async expectQRCodeModalVisible() {
    // 扫码登录通常会显示二维码模态框
    await this.waitForModal();
    await this.expectToBeVisible('.modal:has(.qr-code), .modal:has(img[alt*="二维码"])');
  }

  /**
   * 关闭扫码登录模态框
   */
  async closeQRCodeModal() {
    await this.closeModal();
  }
}

import { expect } from '@playwright/test';
