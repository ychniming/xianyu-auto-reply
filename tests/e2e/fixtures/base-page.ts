import { Page, Locator, expect } from '@playwright/test';
import { Selectors, Timeouts } from './test-data';

/**
 * 基础页面对象类
 * 所有页面类的基类，提供通用方法
 */
export class BasePage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * 导航到指定URL
   */
  async goto(url: string) {
    await this.page.goto(url, { waitUntil: 'networkidle' });
  }

  /**
   * 等待页面加载完成
   */
  async waitForPageLoad() {
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * 点击元素
   */
  async click(selector: string, options?: { timeout?: number; force?: boolean }) {
    const element = this.page.locator(selector);
    await element.waitFor({ state: 'visible', timeout: options?.timeout || Timeouts.medium });
    await element.click({ force: options?.force });
  }

  /**
   * 安全点击（处理可能的拦截）
   */
  async safeClick(selector: string, options?: { timeout?: number }) {
    try {
      await this.click(selector, options);
    } catch (error) {
      // 如果被拦截，尝试强制点击
      await this.page.locator(selector).click({ force: true });
    }
  }

  /**
   * 双击元素
   */
  async doubleClick(selector: string) {
    const element = this.page.locator(selector);
    await element.waitFor({ state: 'visible' });
    await element.dblclick();
  }

  /**
   * 右键点击
   */
  async rightClick(selector: string) {
    const element = this.page.locator(selector);
    await element.waitFor({ state: 'visible' });
    await element.click({ button: 'right' });
  }

  /**
   * 填写输入框
   */
  async fill(selector: string, value: string, options?: { clear?: boolean }) {
    const element = this.page.locator(selector);
    await element.waitFor({ state: 'visible' });
    
    if (options?.clear !== false) {
      await element.clear();
    }
    
    await element.fill(value);
  }

  /**
   * 清空输入框
   */
  async clear(selector: string) {
    const element = this.page.locator(selector);
    await element.waitFor({ state: 'visible' });
    await element.clear();
  }

  /**
   * 获取元素文本
   */
  async getText(selector: string): Promise<string> {
    const element = this.page.locator(selector);
    await element.waitFor({ state: 'visible' });
    return await element.textContent() || '';
  }

  /**
   * 获取输入框值
   */
  async getValue(selector: string): Promise<string> {
    const element = this.page.locator(selector);
    await element.waitFor({ state: 'visible' });
    return await element.inputValue();
  }

  /**
   * 选择下拉框选项
   */
  async selectOption(selector: string, value: string) {
    const element = this.page.locator(selector);
    await element.waitFor({ state: 'visible' });
    await element.selectOption(value);
  }

  /**
   * 勾选复选框
   */
  async check(selector: string) {
    const element = this.page.locator(selector);
    await element.waitFor({ state: 'visible' });
    await element.check();
  }

  /**
   * 取消勾选复选框
   */
  async uncheck(selector: string) {
    const element = this.page.locator(selector);
    await element.waitFor({ state: 'visible' });
    await element.uncheck();
  }

  /**
   * 切换复选框状态
   */
  async toggleCheckbox(selector: string) {
    const element = this.page.locator(selector);
    await element.waitFor({ state: 'visible' });
    await element.click();
  }

  /**
   * 悬停在元素上
   */
  async hover(selector: string) {
    const element = this.page.locator(selector);
    await element.waitFor({ state: 'visible' });
    await element.hover();
  }

  /**
   * 等待元素可见
   */
  async waitForVisible(selector: string, timeout?: number) {
    await this.page.locator(selector).waitFor({ 
      state: 'visible', 
      timeout: timeout || Timeouts.medium 
    });
  }

  /**
   * 等待元素隐藏
   */
  async waitForHidden(selector: string, timeout?: number) {
    await this.page.locator(selector).waitFor({ 
      state: 'hidden', 
      timeout: timeout || Timeouts.medium 
    });
  }

  /**
   * 等待元素存在
   */
  async waitForExist(selector: string, timeout?: number) {
    await this.page.locator(selector).waitFor({ 
      state: 'attached', 
      timeout: timeout || Timeouts.medium 
    });
  }

  /**
   * 检查元素是否存在
   */
  async isExisting(selector: string): Promise<boolean> {
    const count = await this.page.locator(selector).count();
    return count > 0;
  }

  /**
   * 检查元素是否可见
   */
  async isVisible(selector: string): Promise<boolean> {
    return await this.page.locator(selector).isVisible();
  }

  /**
   * 检查元素是否启用
   */
  async isEnabled(selector: string): Promise<boolean> {
    return await this.page.locator(selector).isEnabled();
  }

  /**
   * 检查元素是否禁用
   */
  async isDisabled(selector: string): Promise<boolean> {
    return await this.page.locator(selector).isDisabled();
  }

  /**
   * 检查复选框是否被选中
   */
  async isChecked(selector: string): Promise<boolean> {
    return await this.page.locator(selector).isChecked();
  }

  /**
   * 等待指定时间
   */
  async wait(ms: number) {
    await this.page.waitForTimeout(ms);
  }

  /**
   * 等待网络请求完成
   */
  async waitForRequest(urlPattern: string | RegExp) {
    await this.page.waitForRequest(urlPattern);
  }

  /**
   * 等待网络响应
   */
  async waitForResponse(urlPattern: string | RegExp) {
    await this.page.waitForResponse(urlPattern);
  }

  /**
   * 等待加载状态消失
   */
  async waitForLoadingToFinish() {
    await this.page.waitForFunction(() => {
      const loadingElements = document.querySelectorAll('.loading, .spinner-border, .spinner-grow');
      return loadingElements.length === 0 || 
             Array.from(loadingElements).every(el => !el.isConnected || el.classList.contains('d-none'));
    }, { timeout: Timeouts.long });
  }

  /**
   * 等待Toast消息出现并获取文本
   */
  async waitForToast(): Promise<string> {
    const toast = this.page.locator(Selectors.common.toast);
    await toast.waitFor({ state: 'visible', timeout: Timeouts.medium });
    const message = await this.page.locator(Selectors.common.toastMessage).textContent();
    return message || '';
  }

  /**
   * 等待模态框出现
   */
  async waitForModal() {
    const modal = this.page.locator(Selectors.common.modal);
    await modal.waitFor({ state: 'visible', timeout: Timeouts.medium });
  }

  /**
   * 关闭模态框
   */
  async closeModal() {
    const closeButton = this.page.locator(Selectors.common.modalClose).first();
    if (await closeButton.isVisible()) {
      await closeButton.click();
    }
    await this.waitForHidden(Selectors.common.modal);
  }

  /**
   * 点击确认按钮（模态框中）
   */
  async clickConfirm() {
    await this.click(Selectors.common.confirmButton);
  }

  /**
   * 点击取消按钮（模态框中）
   */
  async clickCancel() {
    await this.click(Selectors.common.cancelButton);
  }

  /**
   * 截图
   */
  async screenshot(name: string) {
    await this.page.screenshot({ 
      path: `playwright-report/screenshots/${name}.png`,
      fullPage: true 
    });
  }

  /**
   * 获取元素数量
   */
  async getElementCount(selector: string): Promise<number> {
    return await this.page.locator(selector).count();
  }

  /**
   * 滚动到元素
   */
  async scrollTo(selector: string) {
    const element = this.page.locator(selector);
    await element.scrollIntoViewIfNeeded();
  }

  /**
   * 执行键盘按键
   */
  async pressKey(key: string) {
    await this.page.keyboard.press(key);
  }

  /**
   * 刷新页面
   */
  async refresh() {
    await this.page.reload({ waitUntil: 'networkidle' });
  }

  /**
   * 返回上一页
   */
  async goBack() {
    await this.page.goBack({ waitUntil: 'networkidle' });
  }

  /**
   * 获取当前URL
   */
  async getCurrentUrl(): Promise<string> {
    return this.page.url();
  }

  /**
   * 获取页面标题
   */
  async getTitle(): Promise<string> {
    return await this.page.title();
  }

  /**
   * 验证元素包含文本
   */
  async expectToContainText(selector: string, text: string) {
    await expect(this.page.locator(selector)).toContainText(text);
  }

  /**
   * 验证元素文本完全匹配
   */
  async expectToHaveText(selector: string, text: string) {
    await expect(this.page.locator(selector)).toHaveText(text);
  }

  /**
   * 验证元素可见
   */
  async expectToBeVisible(selector: string) {
    await expect(this.page.locator(selector)).toBeVisible();
  }

  /**
   * 验证元素隐藏
   */
  async expectToBeHidden(selector: string) {
    await expect(this.page.locator(selector)).toBeHidden();
  }

  /**
   * 验证元素启用
   */
  async expectToBeEnabled(selector: string) {
    await expect(this.page.locator(selector)).toBeEnabled();
  }

  /**
   * 验证元素禁用
   */
  async expectToBeDisabled(selector: string) {
    await expect(this.page.locator(selector)).toBeDisabled();
  }

  /**
   * 验证URL包含指定路径
   */
  async expectUrlToContain(path: string) {
    await expect(this.page).toHaveURL(new RegExp(path));
  }

  /**
   * 验证页面标题
   */
  async expectTitleToContain(title: string) {
    await expect(this.page).toHaveTitle(new RegExp(title));
  }
}
