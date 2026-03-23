/**
 * 集成测试 - 模块间交互测试
 * 测试模块导出完整性
 */
import { describe, it, expect } from 'vitest';

describe('集成测试 - 模块导出完整性', () => {
  const modules = [
    { name: 'api', path: '../../../static/js/modules/api.js' },
    { name: 'auth', path: '../../../static/js/modules/auth.js' },
    { name: 'cards', path: '../../../static/js/modules/cards.js' },
    { name: 'cookies', path: '../../../static/js/modules/cookies.js' },
    { name: 'dashboard', path: '../../../static/js/modules/dashboard.js' },
    { name: 'delivery', path: '../../../static/js/modules/delivery.js' },
    { name: 'items', path: '../../../static/js/modules/items.js' },
    { name: 'keywords', path: '../../../static/js/modules/keywords.js' },
    { name: 'notifications', path: '../../../static/js/modules/notifications.js' },
    { name: 'ai', path: '../../../static/js/modules/ai.js' },
    { name: 'system', path: '../../../static/js/modules/system.js' },
    { name: 'utils', path: '../../../static/js/modules/utils.js' }
  ];

  modules.forEach(({ name, path }) => {
    it(`${name}.js 模块应该能正常加载`, async () => {
      const module = await import(path);
      expect(module).toBeDefined();
      expect(typeof module).toBe('object');
    });
  });

  it('所有模块应该至少导出一个函数', async () => {
    for (const { name, path } of modules) {
      const module = await import(path);
      const exports = Object.keys(module);
      expect(exports.length).toBeGreaterThan(0);
    }
  });
});

describe('集成测试 - 核心 onclick 函数验证', () => {
  it('所有必需的 onclick 函数应该从 app.js 导出', async () => {
    const app = await import('../../../static/js/app.js');
    const onclickFunctions = [
      'showSection',
      'toggleSidebar',
      'loadCookies',
      'copyCookie',
      'delCookie',
      'toggleAccountStatus',
      'toggleAutoConfirm',
      'goToAutoReply',
      'loadAccountKeywords',
      'addKeyword',
      'exportKeywords',
      'showImportModal',
      'showAddKeywordForm',
      'loadCards',
      'showAddCardModal',
      'saveCard',
      'editCard',
      'deleteCard',
      'loadDeliveryRules',
      'showAddDeliveryRuleModal',
      'saveDeliveryRule',
      'deleteDeliveryRule',
      'loadNotificationChannels',
      'showAddChannelModal',
      'saveNotificationChannel',
      'deleteNotificationChannel',
      'loadMessageNotifications',
      'refreshLogs',
      'clearLogsDisplay',
      'clearLogsServer',
      'showLogStats',
      'toggleAutoRefresh',
      'downloadDatabaseBackup',
      'uploadDatabaseBackup',
      'reloadSystemCache',
      'refreshQRCode',
      'toggleMaintenanceMode',
      'loadItems',
      'refreshItems',
      'getAllItemsFromAccount',
      'getAllItemsFromAccountAll',
      'batchDeleteItems',
      'loadAIReplySettings',
      'saveAIReplyConfig',
      'testAIReply',
      'openDefaultReplyManager',
      'configAIReply'
    ];

    for (const fn of onclickFunctions) {
      expect(typeof app[fn]).toBe('function');
    }
  });
});

describe('集成测试 - 模块依赖关系验证', () => {
  it('API 模块应该能正确导入 Utils', async () => {
    const api = await import('../../../static/js/modules/api.js');
    expect(api).toBeDefined();
  });

  it('每个模块应该有至少一个异步函数', async () => {
    const asyncModules = [
      '../../../static/js/modules/api.js',
      '../../../static/js/modules/auth.js',
      '../../../static/js/modules/cookies.js',
      '../../../static/js/modules/dashboard.js',
      '../../../static/js/modules/keywords.js',
      '../../../static/js/modules/cards.js',
      '../../../static/js/modules/delivery.js',
      '../../../static/js/modules/items.js',
      '../../../static/js/modules/notifications.js',
      '../../../static/js/modules/ai.js',
      '../../../static/js/modules/system.js'
    ];

    for (const path of asyncModules) {
      const module = await import(path);
      const asyncFunctions = Object.values(module).filter(
        fn => fn && fn.constructor && fn.constructor.name === 'AsyncFunction'
      );
      expect(asyncFunctions.length).toBeGreaterThan(0);
    }
  });
});
