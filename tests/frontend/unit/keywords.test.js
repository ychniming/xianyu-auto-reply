/**
 * keywords.js 模块测试
 * 测试关键词管理模块导出
 */
import { describe, it, expect } from 'vitest';

describe('Keywords 模块 - 导出验证', () => {
  it('应该导出 getAccountKeywordCount', async () => {
    const keywords = await import('../../../static/js/modules/keywords.js');
    expect(typeof keywords.getAccountKeywordCount).toBe('function');
  });

  it('应该导出 refreshAccountList', async () => {
    const keywords = await import('../../../static/js/modules/keywords.js');
    expect(typeof keywords.refreshAccountList).toBe('function');
  });

  it('应该导出 loadAccountKeywords', async () => {
    const keywords = await import('../../../static/js/modules/keywords.js');
    expect(typeof keywords.loadAccountKeywords).toBe('function');
  });

  it('应该导出 addKeyword', async () => {
    const keywords = await import('../../../static/js/modules/keywords.js');
    expect(typeof keywords.addKeyword).toBe('function');
  });

  it('应该导出 importKeywords', async () => {
    const keywords = await import('../../../static/js/modules/keywords.js');
    expect(typeof keywords.importKeywords).toBe('function');
  });

  it('应该导出 exportKeywords', async () => {
    const keywords = await import('../../../static/js/modules/keywords.js');
    expect(typeof keywords.exportKeywords).toBe('function');
  });

  it('应该导出 showImportModal', async () => {
    const keywords = await import('../../../static/js/modules/keywords.js');
    expect(typeof keywords.showImportModal).toBe('function');
  });

  it('应该导出 showAddKeywordForm', async () => {
    const keywords = await import('../../../static/js/modules/keywords.js');
    expect(typeof keywords.showAddKeywordForm).toBe('function');
  });

  it('应该导出 showAddImageKeywordModal', async () => {
    const keywords = await import('../../../static/js/modules/keywords.js');
    expect(typeof keywords.showAddImageKeywordModal).toBe('function');
  });

  it('应该导出 validateImageDimensions', async () => {
    const keywords = await import('../../../static/js/modules/keywords.js');
    expect(typeof keywords.validateImageDimensions).toBe('function');
  });

  it('应该导出 editKeyword', async () => {
    const keywords = await import('../../../static/js/modules/keywords.js');
    expect(typeof keywords.editKeyword).toBe('function');
  });

  it('应该导出 deleteKeyword', async () => {
    const keywords = await import('../../../static/js/modules/keywords.js');
    expect(typeof keywords.deleteKeyword).toBe('function');
  });

  it('应该导出 renderKeywordsList', async () => {
    const keywords = await import('../../../static/js/modules/keywords.js');
    expect(typeof keywords.renderKeywordsList).toBe('function');
  });

  it('应该导出 goToAutoReply', async () => {
    const keywords = await import('../../../static/js/modules/keywords.js');
    expect(typeof keywords.goToAutoReply).toBe('function');
  });

  it('应该导出 addImageKeyword', async () => {
    const keywords = await import('../../../static/js/modules/keywords.js');
    expect(typeof keywords.addImageKeyword).toBe('function');
  });
});

describe('Keywords 模块 - 函数签名验证', () => {
  it('getAccountKeywordCount 应该是异步函数', async () => {
    const { getAccountKeywordCount } = await import('../../../static/js/modules/keywords.js');
    expect(getAccountKeywordCount.constructor.name).toBe('AsyncFunction');
  });

  it('loadAccountKeywords 应该是异步函数', async () => {
    const { loadAccountKeywords } = await import('../../../static/js/modules/keywords.js');
    expect(loadAccountKeywords.constructor.name).toBe('AsyncFunction');
  });

  it('addKeyword 应该是异步函数', async () => {
    const { addKeyword } = await import('../../../static/js/modules/keywords.js');
    expect(addKeyword.constructor.name).toBe('AsyncFunction');
  });

  it('deleteKeyword 应该是异步函数', async () => {
    const { deleteKeyword } = await import('../../../static/js/modules/keywords.js');
    expect(deleteKeyword.constructor.name).toBe('AsyncFunction');
  });

  it('exportKeywords 应该是异步函数', async () => {
    const { exportKeywords } = await import('../../../static/js/modules/keywords.js');
    expect(exportKeywords.constructor.name).toBe('AsyncFunction');
  });
});
