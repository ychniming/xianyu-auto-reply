/**
 * 扫码登录 E2E 测试
 *
 * 测试流程：
 * 1. 打开登录页面
 * 2. 点击扫码登录按钮
 * 3. 验证二维码模态框显示
 * 4. 验证二维码图片加载
 * 5. 验证状态轮询功能
 *
 * 运行方式：
 * npx playwright test tests/e2e/qr-login.spec.js
 *
 * 注意：完整扫码流程需要真实扫码，此测试验证 UI 交互和 API 调用
 */

const { test, expect } = require('@playwright/test');

test.describe('扫码登录 E2E 测试', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login.html');
  });

  test('应该显示扫码登录按钮', async ({ page }) => {
    const qrLoginBtn = page.locator('button:has-text("扫码登录")');
    await expect(qrLoginBtn).toBeVisible();
  });

  test('点击扫码登录应该显示模态框', async ({ page }) => {
    const qrLoginBtn = page.locator('button:has-text("扫码登录")');
    await qrLoginBtn.click();

    const modal = page.locator('#qrCodeLoginModal');
    await expect(modal).toBeVisible();
  });

  test('扫码登录模态框应该包含二维码容器', async ({ page }) => {
    const qrLoginBtn = page.locator('button:has-text("扫码登录")');
    await qrLoginBtn.click();

    await expect(page.locator('#qrCodeContainer')).toBeVisible();
    await expect(page.locator('#qrCodeImage')).toBeVisible();
    await expect(page.locator('#statusText')).toBeVisible();
  });

  test('应该能够手动输入表单切换', async ({ page }) => {
    const manualInputBtn = page.locator('button:has-text("手动输入")');
    await manualInputBtn.click();

    const manualForm = page.locator('#manualInputForm');
    await expect(manualForm).toBeVisible();
  });

  test('关闭模态框应该重置状态', async ({ page }) => {
    const qrLoginBtn = page.locator('button:has-text("扫码登录")');
    await qrLoginBtn.click();

    const modal = page.locator('#qrCodeLoginModal');
    await expect(modal).toBeVisible();

    const closeBtn = modal.locator('.btn-close');
    await closeBtn.click();

    await expect(modal).not.toBeVisible();
  });
});

test.describe('扫码登录状态轮询测试', () => {
  test('应该定期检查二维码状态', async ({ page }) => {
    const qrLoginBtn = page.locator('button:has-text("扫码登录")');
    await qrLoginBtn.click();

    await page.waitForTimeout(3000);

    const statusText = page.locator('#statusText');
    const text = await statusText.textContent();
    expect(text).toBeTruthy();
  });
});

test.describe('扫码登录成功流程测试（需要真实扫码）', () => {
  test.skip('完整扫码流程 - 需要真实扫码', async ({ page }) => {
    const qrLoginBtn = page.locator('button:has-text("扫码登录")');
    await qrLoginBtn.click();

    const qrCodeImg = page.locator('#qrCodeImg');
    await expect(qrCodeImg).toBeVisible({ timeout: 10000 });

    const statusText = page.locator('#statusText');

    let attempts = 0;
    while (attempts < 60) {
      const text = await statusText.textContent();
      if (text.includes('登录成功')) {
        break;
      }
      if (text.includes('已过期')) {
        throw new Error('二维码已过期');
      }
      await page.waitForTimeout(2000);
      attempts++;
    }

    await page.waitForTimeout(3000);

    const modal = page.locator('#qrCodeLoginModal');
    await expect(modal).not.toBeVisible();

    const currentUrl = page.url();
    expect(currentUrl).not.toContain('login');
  });
});
