/**
 * ai.js 模块测试
 * 测试 AI 回复配置模块导出
 */
import { describe, it, expect } from 'vitest';

describe('AI 模块 - 导出验证', () => {
  it('应该导出 toggleAIReplySettings', async () => {
    const ai = await import('../../../static/js/modules/ai.js');
    expect(typeof ai.toggleAIReplySettings).toBe('function');
  });

  it('应该导出 loadAIReplySettings', async () => {
    const ai = await import('../../../static/js/modules/ai.js');
    expect(typeof ai.loadAIReplySettings).toBe('function');
  });

  it('应该导出 toggleCustomModelInput', async () => {
    const ai = await import('../../../static/js/modules/ai.js');
    expect(typeof ai.toggleCustomModelInput).toBe('function');
  });

  it('应该导出 testAIReply', async () => {
    const ai = await import('../../../static/js/modules/ai.js');
    expect(typeof ai.testAIReply).toBe('function');
  });

  it('应该导出 saveAIReplyConfig', async () => {
    const ai = await import('../../../static/js/modules/ai.js');
    expect(typeof ai.saveAIReplyConfig).toBe('function');
  });

  it('应该导出 toggleReplyContentVisibility', async () => {
    const ai = await import('../../../static/js/modules/ai.js');
    expect(typeof ai.toggleReplyContentVisibility).toBe('function');
  });

  it('应该导出 saveDefaultReply', async () => {
    const ai = await import('../../../static/js/modules/ai.js');
    expect(typeof ai.saveDefaultReply).toBe('function');
  });

  it('应该导出 openDefaultReplyManager', async () => {
    const ai = await import('../../../static/js/modules/ai.js');
    expect(typeof ai.openDefaultReplyManager).toBe('function');
  });

  it('应该导出 getDefaultReplies', async () => {
    const ai = await import('../../../static/js/modules/ai.js');
    expect(typeof ai.getDefaultReplies).toBe('function');
  });

  it('应该导出 getDefaultReply', async () => {
    const ai = await import('../../../static/js/modules/ai.js');
    expect(typeof ai.getDefaultReply).toBe('function');
  });

  it('应该导出 updateDefaultReply', async () => {
    const ai = await import('../../../static/js/modules/ai.js');
    expect(typeof ai.updateDefaultReply).toBe('function');
  });

  it('应该导出 configAIReply', async () => {
    const ai = await import('../../../static/js/modules/ai.js');
    expect(typeof ai.configAIReply).toBe('function');
  });
});

describe('AI 模块 - 函数签名验证', () => {
  it('testAIReply 应该是异步函数', async () => {
    const { testAIReply } = await import('../../../static/js/modules/ai.js');
    expect(testAIReply.constructor.name).toBe('AsyncFunction');
  });

  it('saveAIReplyConfig 应该是异步函数', async () => {
    const { saveAIReplyConfig } = await import('../../../static/js/modules/ai.js');
    expect(saveAIReplyConfig.constructor.name).toBe('AsyncFunction');
  });

  it('getDefaultReplies 应该是异步函数', async () => {
    const { getDefaultReplies } = await import('../../../static/js/modules/ai.js');
    expect(getDefaultReplies.constructor.name).toBe('AsyncFunction');
  });

  it('updateDefaultReply 应该是异步函数', async () => {
    const { updateDefaultReply } = await import('../../../static/js/modules/ai.js');
    expect(updateDefaultReply.constructor.name).toBe('AsyncFunction');
  });
});
