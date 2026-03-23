/**
 * dashboard.js 模块测试
 * 测试仪表盘模块导出
 */
import { describe, it, expect } from 'vitest';

describe('Dashboard 模块 - 导出验证', () => {
  it('应该导出 loadDashboard', async () => {
    const dashboard = await import('../../../static/js/modules/dashboard.js');
    expect(typeof dashboard.loadDashboard).toBe('function');
  });

  it('应该导出 updateDashboardStats', async () => {
    const dashboard = await import('../../../static/js/modules/dashboard.js');
    expect(typeof dashboard.updateDashboardStats).toBe('function');
  });

  it('应该导出 refreshLogs', async () => {
    const dashboard = await import('../../../static/js/modules/dashboard.js');
    expect(typeof dashboard.refreshLogs).toBe('function');
  });

  it('应该导出 clearLogsDisplay', async () => {
    const dashboard = await import('../../../static/js/modules/dashboard.js');
    expect(typeof dashboard.clearLogsDisplay).toBe('function');
  });

  it('应该导出 displayLogs', async () => {
    const dashboard = await import('../../../static/js/modules/dashboard.js');
    expect(typeof dashboard.displayLogs).toBe('function');
  });

  it('应该导出 formatLogTimestamp', async () => {
    const dashboard = await import('../../../static/js/modules/dashboard.js');
    expect(typeof dashboard.formatLogTimestamp).toBe('function');
  });

  it('应该导出 toggleAutoRefresh', async () => {
    const dashboard = await import('../../../static/js/modules/dashboard.js');
    expect(typeof dashboard.toggleAutoRefresh).toBe('function');
  });

  it('应该导出 clearLogsServer', async () => {
    const dashboard = await import('../../../static/js/modules/dashboard.js');
    expect(typeof dashboard.clearLogsServer).toBe('function');
  });

  it('应该导出 showLogStats', async () => {
    const dashboard = await import('../../../static/js/modules/dashboard.js');
    expect(typeof dashboard.showLogStats).toBe('function');
  });
});

describe('Dashboard 模块 - 函数签名验证', () => {
  it('loadDashboard 应该是异步函数', async () => {
    const { loadDashboard } = await import('../../../static/js/modules/dashboard.js');
    expect(loadDashboard.constructor.name).toBe('AsyncFunction');
  });

  it('refreshLogs 应该是异步函数', async () => {
    const { refreshLogs } = await import('../../../static/js/modules/dashboard.js');
    expect(refreshLogs.constructor.name).toBe('AsyncFunction');
  });

  it('formatLogTimestamp 应该返回一个字符串', async () => {
    const { formatLogTimestamp } = await import('../../../static/js/modules/dashboard.js');
    const result = formatLogTimestamp('2024-01-15T10:30:00');
    expect(typeof result).toBe('string');
  });
});
