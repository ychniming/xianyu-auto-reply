/**
 * items.js 模块测试
 * 测试商品管理模块导出
 */
import { describe, it, expect } from 'vitest';

describe('Items 模块 - 导出验证', () => {
  it('应该导出 loadItems', async () => {
    const items = await import('../../../static/js/modules/items.js');
    expect(typeof items.loadItems).toBe('function');
  });

  it('应该导出 refreshItems', async () => {
    const items = await import('../../../static/js/modules/items.js');
    expect(typeof items.refreshItems).toBe('function');
  });

  it('应该导出 getAllItemsFromAccount', async () => {
    const items = await import('../../../static/js/modules/items.js');
    expect(typeof items.getAllItemsFromAccount).toBe('function');
  });

  it('应该导出 getAllItemsFromAccountAll', async () => {
    const items = await import('../../../static/js/modules/items.js');
    expect(typeof items.getAllItemsFromAccountAll).toBe('function');
  });

  it('应该导出 batchDeleteItems', async () => {
    const items = await import('../../../static/js/modules/items.js');
    expect(typeof items.batchDeleteItems).toBe('function');
  });

  it('应该导出 displayItems', async () => {
    const items = await import('../../../static/js/modules/items.js');
    expect(typeof items.displayItems).toBe('function');
  });

  it('应该导出 toggleSelectAll', async () => {
    const items = await import('../../../static/js/modules/items.js');
    expect(typeof items.toggleSelectAll).toBe('function');
  });

  it('应该导出 toggleItemMultiSpec', async () => {
    const items = await import('../../../static/js/modules/items.js');
    expect(typeof items.toggleItemMultiSpec).toBe('function');
  });
});

describe('Items 模块 - 函数签名验证', () => {
  it('loadItems 应该是异步函数', async () => {
    const { loadItems } = await import('../../../static/js/modules/items.js');
    expect(loadItems.constructor.name).toBe('AsyncFunction');
  });

  it('getAllItemsFromAccount 应该是异步函数', async () => {
    const { getAllItemsFromAccount } = await import('../../../static/js/modules/items.js');
    expect(getAllItemsFromAccount.constructor.name).toBe('AsyncFunction');
  });

  it('batchDeleteItems 应该是异步函数', async () => {
    const { batchDeleteItems } = await import('../../../static/js/modules/items.js');
    expect(batchDeleteItems.constructor.name).toBe('AsyncFunction');
  });
});
