/**
 * cookies.js 模块测试
 * 测试 Cookie 管理模块导出
 */
import { describe, it, expect } from 'vitest';

describe('Cookies 模块 - 导出验证', () => {
  it('应该导出 loadCookies', async () => {
    const cookies = await import('../../../static/js/modules/cookies.js');
    expect(typeof cookies.loadCookies).toBe('function');
  });

  it('应该导出 copyCookie', async () => {
    const cookies = await import('../../../static/js/modules/cookies.js');
    expect(typeof cookies.copyCookie).toBe('function');
  });

  it('应该导出 delCookie', async () => {
    const cookies = await import('../../../static/js/modules/cookies.js');
    expect(typeof cookies.delCookie).toBe('function');
  });

  it('应该导出 toggleAccountStatus', async () => {
    const cookies = await import('../../../static/js/modules/cookies.js');
    expect(typeof cookies.toggleAccountStatus).toBe('function');
  });

  it('应该导出 toggleAutoConfirm', async () => {
    const cookies = await import('../../../static/js/modules/cookies.js');
    expect(typeof cookies.toggleAutoConfirm).toBe('function');
  });

  it('应该导出 goToAutoReply', async () => {
    const cookies = await import('../../../static/js/modules/cookies.js');
    expect(typeof cookies.goToAutoReply).toBe('function');
  });

  it('应该导出 editCookieInline', async () => {
    const cookies = await import('../../../static/js/modules/cookies.js');
    expect(typeof cookies.editCookieInline).toBe('function');
  });

  it('应该导出 saveCookieInline', async () => {
    const cookies = await import('../../../static/js/modules/cookies.js');
    expect(typeof cookies.saveCookieInline).toBe('function');
  });

  it('应该导出 cancelCookieEdit', async () => {
    const cookies = await import('../../../static/js/modules/cookies.js');
    expect(typeof cookies.cancelCookieEdit).toBe('function');
  });
});

describe('Cookies 模块 - 函数签名验证', () => {
  it('loadCookies 应该是异步函数', async () => {
    const { loadCookies } = await import('../../../static/js/modules/cookies.js');
    expect(loadCookies.constructor.name).toBe('AsyncFunction');
  });

  it('delCookie 应该是异步函数', async () => {
    const { delCookie } = await import('../../../static/js/modules/cookies.js');
    expect(delCookie.constructor.name).toBe('AsyncFunction');
  });

  it('toggleAccountStatus 应该是异步函数', async () => {
    const { toggleAccountStatus } = await import('../../../static/js/modules/cookies.js');
    expect(toggleAccountStatus.constructor.name).toBe('AsyncFunction');
  });

  it('toggleAutoConfirm 应该是异步函数', async () => {
    const { toggleAutoConfirm } = await import('../../../static/js/modules/cookies.js');
    expect(toggleAutoConfirm.constructor.name).toBe('AsyncFunction');
  });
});
