import { Page } from '@playwright/test';
import { BasePage } from '../fixtures/base-page';
import { Selectors, Timeouts } from '../fixtures/test-data';

/**
 * 商品管理页面对象
 * 封装商品管理页面的所有操作
 */
export class ItemsPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  /**
   * 选择账号筛选
   */
  async selectCookieFilter(cookieId: string) {
    await this.selectOption(Selectors.items.cookieFilter, cookieId);
    await this.wait(Timeouts.medium);
  }

  /**
   * 填写页码
   */
  async fillPageNumber(pageNum: number) {
    await this.fill(Selectors.items.pageNumber, pageNum.toString());
  }

  /**
   * 点击获取指定页按钮
   */
  async clickGetPageButton() {
    await this.click(Selectors.items.getPageButton);
    await this.wait(Timeouts.long);
  }

  /**
   * 点击获取所有页按钮
   */
  async clickGetAllButton() {
    await this.click(Selectors.items.getAllButton);
    await this.wait(Timeouts.long);
  }

  /**
   * 点击刷新按钮
   */
  async clickRefreshButton() {
    await this.click(Selectors.items.refreshButton);
    await this.wait(Timeouts.medium);
  }

  /**
   * 点击全选复选框
   */
  async clickSelectAll() {
    await this.click(Selectors.items.selectAllCheckbox);
    await this.wait(Timeouts.short);
  }

  /**
   * 点击批量删除按钮
   */
  async clickBatchDelete() {
    await this.click(Selectors.items.batchDeleteButton);
    await this.wait(Timeouts.short);
    // 等待确认对话框
    await this.waitForModal();
    await this.clickConfirm();
    await this.wait(Timeouts.medium);
  }

  /**
   * 获取商品列表行数
   */
  async getItemRowCount(): Promise<number> {
    return await this.getElementCount(`${Selectors.items.itemsTable} tr`);
  }

  /**
   * 验证商品表格是否显示
   */
  async expectItemsTableVisible() {
    await this.expectToBeVisible(Selectors.items.itemsTable);
  }

  /**
   * 验证批量删除按钮是否启用
   */
  async expectBatchDeleteEnabled() {
    await this.expectToBeEnabled(Selectors.items.batchDeleteButton);
  }

  /**
   * 验证批量删除按钮是否禁用
   */
  async expectBatchDeleteDisabled() {
    await this.expectToBeDisabled(Selectors.items.batchDeleteButton);
  }

  /**
   * 点击指定商品的操作按钮
   */
  async clickItemAction(itemId: string, action: 'edit' | 'delete' | 'view') {
    const row = this.page.locator(`tr:has-text("${itemId}")`);
    await row.waitFor({ state: 'visible' });

    let buttonSelector: string;
    switch (action) {
      case 'edit':
        buttonSelector = 'button[title="编辑"], button:has(.bi-pencil)';
        break;
      case 'delete':
        buttonSelector = 'button[title="删除"], button:has(.bi-trash)';
        break;
      case 'view':
        buttonSelector = 'button[title="查看"], button:has(.bi-eye)';
        break;
      default:
        throw new Error(`未知的操作类型: ${action}`);
    }

    const button = row.locator(buttonSelector).first();
    await button.click();
    await this.wait(Timeouts.short);
  }

  /**
   * 编辑商品
   */
  async editItem(itemId: string) {
    await this.clickItemAction(itemId, 'edit');
    await this.wait(Timeouts.short);
  }

  /**
   * 删除商品
   */
  async deleteItem(itemId: string) {
    await this.clickItemAction(itemId, 'delete');
    await this.waitForModal();
    await this.clickConfirm();
    await this.wait(Timeouts.medium);
  }

  /**
   * 查看商品详情
   */
  async viewItem(itemId: string) {
    await this.clickItemAction(itemId, 'view');
    await this.wait(Timeouts.short);
  }

  /**
   * 切换商品选择状态
   */
  async toggleItemSelection(itemId: string) {
    const row = this.page.locator(`tr:has-text("${itemId}")`);
    const checkbox = row.locator('input[type="checkbox"]').first();
    await checkbox.click();
    await this.wait(Timeouts.short);
  }

  /**
   * 验证商品是否存在
   */
  async expectItemExists(itemId: string) {
    const row = this.page.locator(`tr:has-text("${itemId}")`);
    await this.expectToBeVisible(`tr:has-text("${itemId}")`);
  }

  /**
   * 验证商品不存在
   */
  async expectItemNotExists(itemId: string) {
    const row = this.page.locator(`tr:has-text("${itemId}")`);
    await expect(row).toHaveCount(0);
  }
}

import { expect } from '@playwright/test';
