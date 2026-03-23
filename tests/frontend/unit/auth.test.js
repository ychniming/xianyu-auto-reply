/**
 * auth.js 模块测试
 * 测试认证模块导出
 */
import { describe, it, expect } from 'vitest';

describe('Auth 模块 - 导出验证', () => {
  it('应该导出 checkAuth', async () => {
    const auth = await import('../../../static/js/modules/auth.js');
    expect(typeof auth.checkAuth).toBe('function');
  });

  it('应该导出 logout', async () => {
    const auth = await import('../../../static/js/modules/auth.js');
    expect(typeof auth.logout).toBe('function');
  });

  it('应该导出 showQRCodeLogin', async () => {
    const auth = await import('../../../static/js/modules/auth.js');
    expect(typeof auth.showQRCodeLogin).toBe('function');
  });

  it('应该导出 toggleManualInput', async () => {
    const auth = await import('../../../static/js/modules/auth.js');
    expect(typeof auth.toggleManualInput).toBe('function');
  });

  it('应该导出 refreshQRCode', async () => {
    const auth = await import('../../../static/js/modules/auth.js');
    expect(typeof auth.refreshQRCode).toBe('function');
  });

  it('应该导出 generateQRCode', async () => {
    const auth = await import('../../../static/js/modules/auth.js');
    expect(typeof auth.generateQRCode).toBe('function');
  });

  it('应该导出 showQRCodeLoading', async () => {
    const auth = await import('../../../static/js/modules/auth.js');
    expect(typeof auth.showQRCodeLoading).toBe('function');
  });

  it('应该导出 showQRCodeImage', async () => {
    const auth = await import('../../../static/js/modules/auth.js');
    expect(typeof auth.showQRCodeImage).toBe('function');
  });

  it('应该导出 showQRCodeError', async () => {
    const auth = await import('../../../static/js/modules/auth.js');
    expect(typeof auth.showQRCodeError).toBe('function');
  });

  it('应该导出 startQRCodeCheck', async () => {
    const auth = await import('../../../static/js/modules/auth.js');
    expect(typeof auth.startQRCodeCheck).toBe('function');
  });

  it('应该导出 checkQRCodeStatus', async () => {
    const auth = await import('../../../static/js/modules/auth.js');
    expect(typeof auth.checkQRCodeStatus).toBe('function');
  });

  it('应该导出 showVerificationRequired', async () => {
    const auth = await import('../../../static/js/modules/auth.js');
    expect(typeof auth.showVerificationRequired).toBe('function');
  });

  it('应该导出 continueAfterVerification', async () => {
    const auth = await import('../../../static/js/modules/auth.js');
    expect(typeof auth.continueAfterVerification).toBe('function');
  });

  it('应该导出 handleQRCodeSuccess', async () => {
    const auth = await import('../../../static/js/modules/auth.js');
    expect(typeof auth.handleQRCodeSuccess).toBe('function');
  });

  it('应该导出 clearQRCodeCheck', async () => {
    const auth = await import('../../../static/js/modules/auth.js');
    expect(typeof auth.clearQRCodeCheck).toBe('function');
  });
});

describe('Auth 模块 - 函数签名验证', () => {
  it('checkAuth 应该是异步函数', async () => {
    const { checkAuth } = await import('../../../static/js/modules/auth.js');
    expect(checkAuth.constructor.name).toBe('AsyncFunction');
  });

  it('logout 应该是异步函数', async () => {
    const { logout } = await import('../../../static/js/modules/auth.js');
    expect(logout.constructor.name).toBe('AsyncFunction');
  });

  it('checkQRCodeStatus 应该是异步函数', async () => {
    const { checkQRCodeStatus } = await import('../../../static/js/modules/auth.js');
    expect(checkQRCodeStatus.constructor.name).toBe('AsyncFunction');
  });

  it('refreshQRCode 应该是异步函数', async () => {
    const { refreshQRCode } = await import('../../../static/js/modules/auth.js');
    expect(refreshQRCode.constructor.name).toBe('AsyncFunction');
  });
});
