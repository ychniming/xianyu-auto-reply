/**
 * cards.js 模块测试
 * 测试卡券管理模块导出
 */
import { describe, it, expect } from 'vitest';

describe('Cards 模块 - 导出验证', () => {
  it('应该导出 loadCards', async () => {
    const cards = await import('../../../static/js/modules/cards.js');
    expect(typeof cards.loadCards).toBe('function');
  });

  it('应该导出 showAddCardModal', async () => {
    const cards = await import('../../../static/js/modules/cards.js');
    expect(typeof cards.showAddCardModal).toBe('function');
  });

  it('应该导出 saveCard', async () => {
    const cards = await import('../../../static/js/modules/cards.js');
    expect(typeof cards.saveCard).toBe('function');
  });

  it('应该导出 editCard', async () => {
    const cards = await import('../../../static/js/modules/cards.js');
    expect(typeof cards.editCard).toBe('function');
  });

  it('应该导出 deleteCard', async () => {
    const cards = await import('../../../static/js/modules/cards.js');
    expect(typeof cards.deleteCard).toBe('function');
  });

  it('应该导出 testCard', async () => {
    const cards = await import('../../../static/js/modules/cards.js');
    expect(typeof cards.testCard).toBe('function');
  });

  it('应该导出 toggleCardTypeFields', async () => {
    const cards = await import('../../../static/js/modules/cards.js');
    expect(typeof cards.toggleCardTypeFields).toBe('function');
  });

  it('应该导出 renderCardsList', async () => {
    const cards = await import('../../../static/js/modules/cards.js');
    expect(typeof cards.renderCardsList).toBe('function');
  });
});

describe('Cards 模块 - 函数签名验证', () => {
  it('loadCards 应该是异步函数', async () => {
    const { loadCards } = await import('../../../static/js/modules/cards.js');
    expect(loadCards.constructor.name).toBe('AsyncFunction');
  });

  it('saveCard 应该是异步函数', async () => {
    const { saveCard } = await import('../../../static/js/modules/cards.js');
    expect(saveCard.constructor.name).toBe('AsyncFunction');
  });

  it('deleteCard 应该是异步函数', async () => {
    const { deleteCard } = await import('../../../static/js/modules/cards.js');
    expect(deleteCard.constructor.name).toBe('AsyncFunction');
  });
});
