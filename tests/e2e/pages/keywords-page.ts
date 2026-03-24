import { Page } from '@playwright/test';
import { BasePage } from '../fixtures/base-page';
import { Selectors, TestKeywords, Timeouts } from '../fixtures/test-data';

/**
 * 关键词管理页面对象
 * 封装关键词管理页面的所有操作
 */
export class KeywordsPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  /**
   * 选择账号
   */
  async selectAccount(cookieId: string) {
    await this.selectOption(Selectors.keywords.accountSelect, cookieId);
    await this.wait(Timeouts.medium);
  }

  /**
   * 刷新账号列表
   */
  async refreshAccountList() {
    await this.click(Selectors.keywords.refreshAccountList);
    await this.wait(Timeouts.medium);
  }

  /**
   * 填写关键词
   */
  async fillKeyword(keyword: string) {
    await this.fill(Selectors.keywords.keywordInput, keyword);
  }

  /**
   * 填写回复内容
   */
  async fillReply(reply: string) {
    await this.fill(Selectors.keywords.replyInput, reply);
  }

  /**
   * 选择商品ID
   */
  async selectItemId(itemId: string) {
    await this.selectOption(Selectors.keywords.itemIdSelect, itemId);
  }

  /**
   * 选择匹配类型
   */
  async selectMatchType(matchType: string) {
    await this.selectOption(Selectors.keywords.matchTypeSelect, matchType);
  }

  /**
   * 填写优先级
   */
  async fillPriority(priority: number) {
    await this.fill(Selectors.keywords.priorityInput, priority.toString());
  }

  /**
   * 选择回复模式
   */
  async selectReplyMode(mode: string) {
    await this.selectOption(Selectors.keywords.replyModeSelect, mode);
  }

  /**
   * 添加文本关键词
   */
  async addTextKeyword(keyword: string, reply: string, options?: {
    itemId?: string;
    matchType?: string;
    priority?: number;
    replyMode?: string;
  }) {
    await this.fillKeyword(keyword);
    await this.fillReply(reply);
    
    if (options?.itemId) {
      await this.selectItemId(options.itemId);
    }
    if (options?.matchType) {
      await this.selectMatchType(options.matchType);
    }
    if (options?.priority) {
      await this.fillPriority(options.priority);
    }
    if (options?.replyMode) {
      await this.selectReplyMode(options.replyMode);
    }
    
    await this.click(Selectors.keywords.addTextButton);
    await this.wait(Timeouts.medium);
  }

  /**
   * 点击添加文本关键词按钮
   */
  async clickAddTextKeyword() {
    await this.click(Selectors.keywords.addTextButton);
    await this.wait(Timeouts.medium);
  }

  /**
   * 点击添加图片关键词按钮
   */
  async clickAddImageKeyword() {
    await this.click(Selectors.keywords.addImageButton);
    await this.wait(Timeouts.short);
  }

  /**
   * 展开/收起高级条件设置
   */
  async toggleAdvancedConditions() {
    await this.click(Selectors.keywords.advancedConditions);
    await this.wait(Timeouts.short);
  }

  /**
   * 设置时间范围
   */
  async setTimeRange(startHour: number, endHour: number) {
    await this.fill(Selectors.keywords.timeStartInput, startHour.toString());
    await this.fill(Selectors.keywords.timeEndInput, endHour.toString());
  }

  /**
   * 设置排除关键词
   */
  async setExcludeKeywords(keywords: string) {
    await this.fill(Selectors.keywords.excludeKeywordsInput, keywords);
  }

  /**
   * 设置最大触发次数
   */
  async setMaxTriggerCount(count: number) {
    await this.fill(Selectors.keywords.maxTriggerInput, count.toString());
  }

  /**
   * 选择用户类型
   */
  async selectUserType(userType: string) {
    await this.selectOption(Selectors.keywords.userTypeSelect, userType);
  }

  /**
   * 填写测试消息
   */
  async fillTestMessage(message: string) {
    await this.fill(Selectors.keywords.testMessageInput, message);
  }

  /**
   * 填写测试商品ID
   */
  async fillTestItemId(itemId: string) {
    await this.fill(Selectors.keywords.testItemIdInput, itemId);
  }

  /**
   * 点击测试按钮
   */
  async clickTestButton() {
    await this.click(Selectors.keywords.testButton);
    await this.wait(Timeouts.medium);
  }

  /**
   * 测试关键词匹配
   */
  async testKeywordMatch(message: string, itemId?: string) {
    await this.fillTestMessage(message);
    if (itemId) {
      await this.fillTestItemId(itemId);
    }
    await this.clickTestButton();
  }

  /**
   * 点击导出按钮
   */
  async clickExport() {
    await this.click(Selectors.keywords.exportButton);
    await this.wait(Timeouts.medium);
  }

  /**
   * 点击导入按钮
   */
  async clickImport() {
    await this.click(Selectors.keywords.importButton);
    await this.wait(Timeouts.short);
  }

  /**
   * 获取关键词列表数量
   */
  async getKeywordCount(): Promise<number> {
    return await this.getElementCount(`${Selectors.keywords.keywordsList} .keyword-item, .keyword-card`);
  }

  /**
   * 验证关键词管理容器是否显示
   */
  async expectKeywordManagementVisible() {
    await this.expectToBeVisible('#keywordManagement');
  }

  /**
   * 验证关键词列表是否显示
   */
  async expectKeywordsListVisible() {
    await this.expectToBeVisible(Selectors.keywords.keywordsList);
  }

  /**
   * 删除指定关键词
   */
  async deleteKeyword(keyword: string) {
    const keywordItem = this.page.locator(`${Selectors.keywords.keywordsList}:has-text("${keyword}")`);
    const deleteButton = keywordItem.locator('button[title="删除"], button:has(.bi-trash), .delete-btn').first();
    await deleteButton.click();
    
    // 等待确认对话框
    await this.waitForModal();
    await this.clickConfirm();
    await this.wait(Timeouts.medium);
  }

  /**
   * 编辑指定关键词
   */
  async editKeyword(keyword: string) {
    const keywordItem = this.page.locator(`${Selectors.keywords.keywordsList}:has-text("${keyword}")`);
    const editButton = keywordItem.locator('button[title="编辑"], button:has(.bi-pencil), .edit-btn').first();
    await editButton.click();
    await this.wait(Timeouts.short);
  }

  /**
   * 验证关键词是否存在
   */
  async expectKeywordExists(keyword: string) {
    const keywordItem = this.page.locator(`${Selectors.keywords.keywordsList}:has-text("${keyword}")`);
    await this.expectToBeVisible(`${Selectors.keywords.keywordsList}:has-text("${keyword}")`);
  }

  /**
   * 验证关键词不存在
   */
  async expectKeywordNotExists(keyword: string) {
    const keywordItem = this.page.locator(`${Selectors.keywords.keywordsList}:has-text("${keyword}")`);
    await expect(keywordItem).toHaveCount(0);
  }

  /**
   * 获取测试结果显示
   */
  async getTestResult(): Promise<string> {
    const resultElement = this.page.locator('.test-result, .keyword-test-result, #testResult');
    if (await resultElement.isVisible()) {
      return await resultElement.textContent() || '';
    }
    return '';
  }

  /**
   * 验证高级条件面板是否展开
   */
  async expectAdvancedConditionsExpanded() {
    await this.expectToBeVisible('#advancedConditionsBody');
  }

  /**
   * 验证高级条件面板是否收起
   */
  async expectAdvancedConditionsCollapsed() {
    await this.expectToBeHidden('#advancedConditionsBody');
  }
}

import { expect } from '@playwright/test';
