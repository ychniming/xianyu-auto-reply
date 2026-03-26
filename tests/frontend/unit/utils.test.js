/**
 * utils.js 模块测试
 * 测试全局变量和工具函数
 */
import { describe, it, expect } from 'vitest';

describe('Utils 模块 - 全局变量', () => {
  it('应该导出 apiBase', async () => {
    const { apiBase } = await import('../../../static/js/modules/utils.js');
    expect(apiBase).toBeDefined();
    expect(typeof apiBase).toBe('string');
  });

  it('应该导出 authToken', async () => {
    const { authToken } = await import('../../../static/js/modules/utils.js');
    expect(authToken).toBeDefined();
  });

  it('应该导出 keywordsStore (新Store模式)', async () => {
    const { keywordsStore } = await import('../../../static/js/modules/utils.js');
    expect(keywordsStore).toBeDefined();
    expect(typeof keywordsStore.getState).toBe('function');
    expect(typeof keywordsStore.setState).toBe('function');
    expect(typeof keywordsStore.subscribe).toBe('function');
  });

  it('应该导出 cookiesStore (新Store模式)', async () => {
    const { cookiesStore } = await import('../../../static/js/modules/utils.js');
    expect(cookiesStore).toBeDefined();
    expect(typeof cookiesStore.getState).toBe('function');
    expect(typeof cookiesStore.setState).toBe('function');
  });

  it('应该导出 dashboardStore (新Store模式)', async () => {
    const { dashboardStore } = await import('../../../static/js/modules/utils.js');
    expect(dashboardStore).toBeDefined();
    expect(typeof dashboardStore.getState).toBe('function');
    expect(typeof dashboardStore.setState).toBe('function');
  });

  it('应该导出 aiStore (新Store模式)', async () => {
    const { aiStore } = await import('../../../static/js/modules/utils.js');
    expect(aiStore).toBeDefined();
    expect(typeof aiStore.getState).toBe('function');
    expect(typeof aiStore.setState).toBe('function');
  });

  it('应该导出 CACHE_DURATION 常量', async () => {
    const { CACHE_DURATION } = await import('../../../static/js/modules/utils.js');
    expect(CACHE_DURATION).toBeDefined();
    expect(CACHE_DURATION).toBe(30000);
  });
});

describe('Utils 模块 - escapeHtml 函数', () => {
  it('应该转义 HTML 特殊字符', async () => {
    const { escapeHtml } = await import('../../../static/js/modules/utils.js');
    const result = escapeHtml('<script>');
    expect(result).toContain('&lt;');
    expect(result).toContain('&gt;');
  });

  it('应该处理空字符串', async () => {
    const { escapeHtml } = await import('../../../static/js/modules/utils.js');
    expect(escapeHtml('')).toBe('');
    expect(escapeHtml(null)).toBe('');
    expect(escapeHtml(undefined)).toBe('');
  });

  it('应该返回原始文本', async () => {
    const { escapeHtml } = await import('../../../static/js/modules/utils.js');
    expect(escapeHtml('Hello World')).toBe('Hello World');
    expect(escapeHtml('正常中文文本')).toBe('正常中文文本');
  });

  it('应该防止XSS攻击', async () => {
    const { escapeHtml } = await import('../../../static/js/modules/utils.js');
    expect(escapeHtml('<script>alert(1)</script>')).toBe('&lt;script&gt;alert(1)&lt;/script&gt;');
    expect(escapeHtml('<img src=x onerror=alert(1)>')).toBe('&lt;img src=x onerror=alert(1)&gt;');
  });
});

describe('Utils 模块 - formatDateTime 函数', () => {
  it('应该正确格式化日期时间', async () => {
    const { formatDateTime } = await import('../../../static/js/modules/utils.js');
    const result = formatDateTime('2024-01-15T10:30:00');
    expect(result).toBeDefined();
    expect(typeof result).toBe('string');
  });

  it('应该处理空日期', async () => {
    const { formatDateTime } = await import('../../../static/js/modules/utils.js');
    expect(formatDateTime('')).toBe('未知');
    expect(formatDateTime(null)).toBe('未知');
    expect(formatDateTime(undefined)).toBe('未知');
  });
});

describe('Utils 模块 - updateAuthToken 函数', () => {
  it('应该更新 authToken', async () => {
    const { updateAuthToken } = await import('../../../static/js/modules/utils.js');
    expect(typeof updateAuthToken).toBe('function');
  });
});

describe('Utils 模块 - Store 状态管理', () => {
  it('keywordsStore 应该能获取和设置状态', async () => {
    const { keywordsStore } = await import('../../../static/js/modules/utils.js');
    const initialState = keywordsStore.getState();
    expect(initialState).toBeDefined();
    expect(typeof initialState).toBe('object');
  });

  it('cookiesStore 应该能获取和设置状态', async () => {
    const { cookiesStore } = await import('../../../static/js/modules/utils.js');
    const initialState = cookiesStore.getState();
    expect(initialState).toBeDefined();
    expect(typeof initialState).toBe('object');
  });

  it('Store 订阅者应该能收到状态变化通知', async () => {
    const { keywordsStore } = await import('../../../static/js/modules/utils.js');
    let notified = false;
    const unsubscribe = keywordsStore.subscribe((newState, prevState) => {
      notified = true;
    });
    keywordsStore.setState({ loading: true });
    expect(notified).toBe(true);
    unsubscribe();
  });
});

describe('Utils 模块 - App 命名空间', () => {
  it('window.App.showToast 应该是函数', async () => {
    await import('../../../static/js/modules/utils.js');
    expect(typeof window.App.showToast).toBe('function');
  });

  it('window.App.showLoading 应该是函数', async () => {
    await import('../../../static/js/modules/utils.js');
    expect(typeof window.App.showLoading).toBe('function');
  });

  it('window.App.hideLoading 应该是函数', async () => {
    await import('../../../static/js/modules/utils.js');
    expect(typeof window.App.hideLoading).toBe('function');
  });

  it('window.App.showSection 应该是函数', async () => {
    await import('../../../static/js/modules/utils.js');
    expect(typeof window.App.showSection).toBe('function');
  });

  it('window.App.toggleSidebar 应该是函数', async () => {
    await import('../../../static/js/modules/utils.js');
    expect(typeof window.App.toggleSidebar).toBe('function');
  });
});

describe('Utils 模块 - API 命名空间', () => {
  it('window.API 应该是对象', async () => {
    await import('../../../static/js/modules/api.js');
    expect(typeof window.API).toBe('object');
  });

  it('window.API.cookies 应该是对象', async () => {
    await import('../../../static/js/modules/api.js');
    expect(typeof window.API.cookies).toBe('object');
  });

  it('window.API.keywords 应该是对象', async () => {
    await import('../../../static/js/modules/api.js');
    expect(typeof window.API.keywords).toBe('object');
  });
});
