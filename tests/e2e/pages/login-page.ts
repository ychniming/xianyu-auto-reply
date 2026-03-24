import { Page } from '@playwright/test';
import { BasePage } from '../fixtures/base-page';
import { Selectors, URLs, TestUsers, Timeouts } from '../fixtures/test-data';

/**
 * 登录页面对象
 * 封装登录页面的所有操作
 */
export class LoginPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  /**
   * 导航到登录页面
   */
  async goto() {
    await super.goto(URLs.login);
    await this.waitForPageLoad();
  }

  /**
   * 使用用户名和密码登录
   */
  async loginWithUsername(username: string, password: string) {
    // 确保在用户名/密码登录标签页
    await this.click(Selectors.login.usernameLoginTab);
    
    // 填写用户名
    await this.fill(Selectors.login.usernameInput, username);
    
    // 填写密码
    await this.fill(Selectors.login.passwordInput, password);
    
    // 点击登录按钮
    await this.click(Selectors.login.loginButton);
    
    // 等待导航完成
    await this.waitForPageLoad();
  }

  /**
   * 使用邮箱和密码登录
   */
  async loginWithEmailPassword(email: string, password: string) {
    // 切换到邮箱/密码登录标签页
    await this.click(Selectors.login.emailPasswordTab);
    await this.wait(Timeouts.short);
    
    // 填写邮箱
    await this.fill(Selectors.login.emailInput, email);
    
    // 填写密码
    await this.fill(Selectors.login.passwordInput, password);
    
    // 点击登录按钮
    await this.click(Selectors.login.loginButton);
    
    // 等待导航完成
    await this.waitForPageLoad();
  }

  /**
   * 使用邮箱和验证码登录
   */
  async loginWithEmailCode(email: string, code: string) {
    // 切换到邮箱/验证码登录标签页
    await this.click(Selectors.login.emailCodeTab);
    await this.wait(Timeouts.short);
    
    // 填写邮箱
    await this.fill(Selectors.login.emailInput, email);
    
    // 填写验证码
    await this.fill(Selectors.login.verificationCodeInput, code);
    
    // 点击登录按钮
    await this.click(Selectors.login.loginButton);
    
    // 等待导航完成
    await this.waitForPageLoad();
  }

  /**
   * 管理员登录
   */
  async loginAsAdmin() {
    await this.loginWithUsername(TestUsers.admin.username, TestUsers.admin.password);
  }

  /**
   * 普通用户登录
   */
  async loginAsUser() {
    await this.loginWithUsername(TestUsers.user.username, TestUsers.user.password);
  }

  /**
   * 点击扫码登录按钮
   */
  async clickQRCodeLogin() {
    await this.click(Selectors.login.usernameLoginTab);
    // 扫码登录通常是默认选项的一部分
  }

  /**
   * 刷新验证码图片
   */
  async refreshCaptcha() {
    await this.click(Selectors.login.captchaImage);
    await this.wait(Timeouts.short);
  }

  /**
   * 发送验证码
   */
  async sendVerificationCode() {
    await this.click(Selectors.login.sendCodeButton);
    await this.wait(Timeouts.medium);
  }

  /**
   * 切换到用户名/密码登录
   */
  async switchToUsernameLogin() {
    await this.click(Selectors.login.usernameLoginTab);
    await this.wait(Timeouts.short);
  }

  /**
   * 切换到邮箱/密码登录
   */
  async switchToEmailPasswordLogin() {
    await this.click(Selectors.login.emailPasswordTab);
    await this.wait(Timeouts.short);
  }

  /**
   * 切换到邮箱/验证码登录
   */
  async switchToEmailCodeLogin() {
    await this.click(Selectors.login.emailCodeTab);
    await this.wait(Timeouts.short);
  }

  /**
   * 验证登录表单是否显示
   */
  async expectLoginFormVisible() {
    await this.expectToBeVisible(Selectors.login.usernameInput);
    await this.expectToBeVisible(Selectors.login.passwordInput);
    await this.expectToBeVisible(Selectors.login.loginButton);
  }

  /**
   * 验证是否登录成功（跳转到首页）
   */
  async expectLoginSuccess() {
    await this.expectUrlToContain('index.html');
    await this.expectTitleToContain('闲鱼自动回复');
  }

  /**
   * 验证是否显示错误消息
   */
  async expectErrorMessage() {
    // 等待错误提示出现
    const errorAlert = this.page.locator('.alert-danger, .toast-error, .text-danger');
    await errorAlert.waitFor({ state: 'visible', timeout: Timeouts.medium });
  }

  /**
   * 获取错误消息文本
   */
  async getErrorMessage(): Promise<string> {
    const errorAlert = this.page.locator('.alert-danger, .toast-body');
    if (await errorAlert.isVisible()) {
      return await errorAlert.textContent() || '';
    }
    return '';
  }

  /**
   * 清空所有输入框
   */
  async clearAllInputs() {
    await this.clear(Selectors.login.usernameInput);
    await this.clear(Selectors.login.passwordInput);
    await this.clear(Selectors.login.emailInput);
    await this.clear(Selectors.login.captchaInput);
    await this.clear(Selectors.login.verificationCodeInput);
  }

  /**
   * 验证验证码图片是否显示
   */
  async expectCaptchaVisible() {
    await this.expectToBeVisible(Selectors.login.captchaImage);
  }

  /**
   * 验证发送验证码按钮状态
   */
  async expectSendCodeButtonDisabled() {
    await this.expectToBeDisabled(Selectors.login.sendCodeButton);
  }

  /**
   * 验证发送验证码按钮启用
   */
  async expectSendCodeButtonEnabled() {
    await this.expectToBeEnabled(Selectors.login.sendCodeButton);
  }
}
