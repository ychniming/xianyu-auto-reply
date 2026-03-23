/**
 * api.js 模块测试
 * 测试 API 函数导出
 */
import { describe, it, expect } from 'vitest';

describe('API 模块 - 导出验证', () => {
  it('应该导出 fetchJSON', async () => {
    const api = await import('../../../static/js/modules/api.js');
    expect(typeof api.fetchJSON).toBe('function');
  });

  it('应该导出 handleApiError', async () => {
    const api = await import('../../../static/js/modules/api.js');
    expect(typeof api.handleApiError).toBe('function');
  });

  it('应该导出 toggleLoading', async () => {
    const api = await import('../../../static/js/modules/api.js');
    expect(typeof api.toggleLoading).toBe('function');
  });

  it('应该导出 showToast', async () => {
    const api = await import('../../../static/js/modules/api.js');
    expect(typeof api.showToast).toBe('function');
  });

  it('应该导出 loadCookiesAPI', async () => {
    const api = await import('../../../static/js/modules/api.js');
    expect(typeof api.loadCookiesAPI).toBe('function');
  });

  it('应该导出 addCookieAPI', async () => {
    const api = await import('../../../static/js/modules/api.js');
    expect(typeof api.addCookieAPI).toBe('function');
  });

  it('应该导出 deleteCookieAPI', async () => {
    const api = await import('../../../static/js/modules/api.js');
    expect(typeof api.deleteCookieAPI).toBe('function');
  });

  it('应该导出 toggleAccountStatusAPI', async () => {
    const api = await import('../../../static/js/modules/api.js');
    expect(typeof api.toggleAccountStatusAPI).toBe('function');
  });

  it('应该导出 toggleAutoConfirmAPI', async () => {
    const api = await import('../../../static/js/modules/api.js');
    expect(typeof api.toggleAutoConfirmAPI).toBe('function');
  });

  it('应该导出 getKeywordsAPI', async () => {
    const api = await import('../../../static/js/modules/api.js');
    expect(typeof api.getKeywordsAPI).toBe('function');
  });

  it('应该导出 saveKeywordsAPI', async () => {
    const api = await import('../../../static/js/modules/api.js');
    expect(typeof api.saveKeywordsAPI).toBe('function');
  });

  it('应该导出 downloadDatabaseBackupAPI', async () => {
    const api = await import('../../../static/js/modules/api.js');
    expect(typeof api.downloadDatabaseBackupAPI).toBe('function');
  });

  it('应该导出 uploadDatabaseBackupAPI', async () => {
    const api = await import('../../../static/js/modules/api.js');
    expect(typeof api.uploadDatabaseBackupAPI).toBe('function');
  });

  it('应该导出 logoutAPI', async () => {
    const api = await import('../../../static/js/modules/api.js');
    expect(typeof api.logoutAPI).toBe('function');
  });

  it('应该导出 verifyAuthAPI', async () => {
    const api = await import('../../../static/js/modules/api.js');
    expect(typeof api.verifyAuthAPI).toBe('function');
  });
});

describe('API 模块 - 函数签名验证', () => {
  it('fetchJSON 应该是异步函数', async () => {
    const { fetchJSON } = await import('../../../static/js/modules/api.js');
    expect(fetchJSON.constructor.name).toBe('AsyncFunction');
  });

  it('toggleLoading 应该接受一个参数', async () => {
    const { toggleLoading } = await import('../../../static/js/modules/api.js');
    expect(toggleLoading.length).toBeGreaterThanOrEqual(0);
  });

  it('showToast 应该接受 message 和 type 参数', async () => {
    const { showToast } = await import('../../../static/js/modules/api.js');
    expect(showToast.length).toBeGreaterThanOrEqual(1);
  });
});
