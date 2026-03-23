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

  it('应该导出 keywordsData', async () => {
    const { keywordsData } = await import('../../../static/js/modules/utils.js');
    expect(keywordsData).toBeDefined();
    expect(typeof keywordsData).toBe('object');
  });

  it('应该导出 currentCookieId', async () => {
    const { currentCookieId } = await import('../../../static/js/modules/utils.js');
    expect(currentCookieId).toBeDefined();
    expect(typeof currentCookieId).toBe('string');
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
