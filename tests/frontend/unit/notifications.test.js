/**
 * notifications.js 模块测试
 * 测试通知渠道模块导出
 */
import { describe, it, expect } from 'vitest';

describe('Notifications 模块 - 导出验证', () => {
  it('应该导出 loadNotificationChannels', async () => {
    const notifications = await import('../../../static/js/modules/notifications.js');
    expect(typeof notifications.loadNotificationChannels).toBe('function');
  });

  it('应该导出 showAddChannelModal', async () => {
    const notifications = await import('../../../static/js/modules/notifications.js');
    expect(typeof notifications.showAddChannelModal).toBe('function');
  });

  it('应该导出 saveNotificationChannel', async () => {
    const notifications = await import('../../../static/js/modules/notifications.js');
    expect(typeof notifications.saveNotificationChannel).toBe('function');
  });

  it('应该导出 deleteNotificationChannel', async () => {
    const notifications = await import('../../../static/js/modules/notifications.js');
    expect(typeof notifications.deleteNotificationChannel).toBe('function');
  });

  it('应该导出 generateFieldHtml', async () => {
    const notifications = await import('../../../static/js/modules/notifications.js');
    expect(typeof notifications.generateFieldHtml).toBe('function');
  });

  it('应该导出 renderNotificationChannels', async () => {
    const notifications = await import('../../../static/js/modules/notifications.js');
    expect(typeof notifications.renderNotificationChannels).toBe('function');
  });

  it('应该导出 loadMessageNotifications', async () => {
    const notifications = await import('../../../static/js/modules/notifications.js');
    expect(typeof notifications.loadMessageNotifications).toBe('function');
  });

  it('应该导出 saveAccountNotification', async () => {
    const notifications = await import('../../../static/js/modules/notifications.js');
    expect(typeof notifications.saveAccountNotification).toBe('function');
  });

  it('应该导出 deleteAccountNotification', async () => {
    const notifications = await import('../../../static/js/modules/notifications.js');
    expect(typeof notifications.deleteAccountNotification).toBe('function');
  });

  it('应该导出 showAddChannelModal', async () => {
    const notifications = await import('../../../static/js/modules/notifications.js');
    expect(typeof notifications.showAddChannelModal).toBe('function');
  });
});

describe('Notifications 模块 - 函数签名验证', () => {
  it('loadNotificationChannels 应该是异步函数', async () => {
    const { loadNotificationChannels } = await import('../../../static/js/modules/notifications.js');
    expect(loadNotificationChannels.constructor.name).toBe('AsyncFunction');
  });

  it('saveNotificationChannel 应该是异步函数', async () => {
    const { saveNotificationChannel } = await import('../../../static/js/modules/notifications.js');
    expect(saveNotificationChannel.constructor.name).toBe('AsyncFunction');
  });

  it('deleteNotificationChannel 应该是异步函数', async () => {
    const { deleteNotificationChannel } = await import('../../../static/js/modules/notifications.js');
    expect(deleteNotificationChannel.constructor.name).toBe('AsyncFunction');
  });

  it('generateFieldHtml 应该返回一个字符串', async () => {
    const { generateFieldHtml } = await import('../../../static/js/modules/notifications.js');
    const result = generateFieldHtml('webhook');
    expect(typeof result).toBe('string');
  });
});
