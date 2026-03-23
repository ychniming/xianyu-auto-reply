/**
 * system.js 模块测试
 * 测试系统设置模块导出
 */
import { describe, it, expect } from 'vitest';

describe('System 模块 - 导出验证', () => {
  it('应该导出 loadTableData', async () => {
    const system = await import('../../../static/js/modules/system.js');
    expect(typeof system.loadTableData).toBe('function');
  });

  it('应该导出 confirmDelete', async () => {
    const system = await import('../../../static/js/modules/system.js');
    expect(typeof system.confirmDelete).toBe('function');
  });

  it('应该导出 downloadDatabaseBackup', async () => {
    const system = await import('../../../static/js/modules/system.js');
    expect(typeof system.downloadDatabaseBackup).toBe('function');
  });

  it('应该导出 uploadDatabaseBackup', async () => {
    const system = await import('../../../static/js/modules/system.js');
    expect(typeof system.uploadDatabaseBackup).toBe('function');
  });

  it('应该导出 reloadSystemCache', async () => {
    const system = await import('../../../static/js/modules/system.js');
    expect(typeof system.reloadSystemCache).toBe('function');
  });

  it('应该导出 refreshQRCode', async () => {
    const system = await import('../../../static/js/modules/system.js');
    expect(typeof system.refreshQRCode).toBe('function');
  });

  it('应该导出 toggleMaintenanceMode', async () => {
    const system = await import('../../../static/js/modules/system.js');
    expect(typeof system.toggleMaintenanceMode).toBe('function');
  });
});

describe('System 模块 - 函数签名验证', () => {
  it('loadTableData 应该是异步函数', async () => {
    const { loadTableData } = await import('../../../static/js/modules/system.js');
    expect(loadTableData.constructor.name).toBe('AsyncFunction');
  });

  it('downloadDatabaseBackup 应该是异步函数', async () => {
    const { downloadDatabaseBackup } = await import('../../../static/js/modules/system.js');
    expect(downloadDatabaseBackup.constructor.name).toBe('AsyncFunction');
  });

  it('uploadDatabaseBackup 应该是异步函数', async () => {
    const { uploadDatabaseBackup } = await import('../../../static/js/modules/system.js');
    expect(uploadDatabaseBackup.constructor.name).toBe('AsyncFunction');
  });

  it('reloadSystemCache 应该是异步函数', async () => {
    const { reloadSystemCache } = await import('../../../static/js/modules/system.js');
    expect(reloadSystemCache.constructor.name).toBe('AsyncFunction');
  });
});
