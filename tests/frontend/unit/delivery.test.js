/**
 * delivery.js 模块测试
 * 测试发货规则模块导出
 */
import { describe, it, expect } from 'vitest';

describe('Delivery 模块 - 导出验证', () => {
  it('应该导出 loadDeliveryRules', async () => {
    const delivery = await import('../../../static/js/modules/delivery.js');
    expect(typeof delivery.loadDeliveryRules).toBe('function');
  });

  it('应该导出 showAddDeliveryRuleModal', async () => {
    const delivery = await import('../../../static/js/modules/delivery.js');
    expect(typeof delivery.showAddDeliveryRuleModal).toBe('function');
  });

  it('应该导出 saveDeliveryRule', async () => {
    const delivery = await import('../../../static/js/modules/delivery.js');
    expect(typeof delivery.saveDeliveryRule).toBe('function');
  });

  it('应该导出 editDeliveryRule', async () => {
    const delivery = await import('../../../static/js/modules/delivery.js');
    expect(typeof delivery.editDeliveryRule).toBe('function');
  });

  it('应该导出 updateDeliveryRule', async () => {
    const delivery = await import('../../../static/js/modules/delivery.js');
    expect(typeof delivery.updateDeliveryRule).toBe('function');
  });

  it('应该导出 testDeliveryRule', async () => {
    const delivery = await import('../../../static/js/modules/delivery.js');
    expect(typeof delivery.testDeliveryRule).toBe('function');
  });

  it('应该导出 deleteDeliveryRule', async () => {
    const delivery = await import('../../../static/js/modules/delivery.js');
    expect(typeof delivery.deleteDeliveryRule).toBe('function');
  });

  it('应该导出 renderDeliveryRulesList', async () => {
    const delivery = await import('../../../static/js/modules/delivery.js');
    expect(typeof delivery.renderDeliveryRulesList).toBe('function');
  });

  it('应该导出 updateDeliveryStats', async () => {
    const delivery = await import('../../../static/js/modules/delivery.js');
    expect(typeof delivery.updateDeliveryStats).toBe('function');
  });

  it('应该导出 loadCardsForSelect', async () => {
    const delivery = await import('../../../static/js/modules/delivery.js');
    expect(typeof delivery.loadCardsForSelect).toBe('function');
  });

  it('应该导出 loadCardsForEditSelect', async () => {
    const delivery = await import('../../../static/js/modules/delivery.js');
    expect(typeof delivery.loadCardsForEditSelect).toBe('function');
  });
});

describe('Delivery 模块 - 函数签名验证', () => {
  it('loadDeliveryRules 应该是异步函数', async () => {
    const { loadDeliveryRules } = await import('../../../static/js/modules/delivery.js');
    expect(loadDeliveryRules.constructor.name).toBe('AsyncFunction');
  });

  it('saveDeliveryRule 应该是异步函数', async () => {
    const { saveDeliveryRule } = await import('../../../static/js/modules/delivery.js');
    expect(saveDeliveryRule.constructor.name).toBe('AsyncFunction');
  });

  it('deleteDeliveryRule 应该是异步函数', async () => {
    const { deleteDeliveryRule } = await import('../../../static/js/modules/delivery.js');
    expect(deleteDeliveryRule.constructor.name).toBe('AsyncFunction');
  });
});
