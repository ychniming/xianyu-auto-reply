/**
 * api.js 模块测试
 * 测试统一 API 命名空间
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';

describe('API 模块 - 命名空间结构', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('应该定义 API 命名空间', async () => {
        await import('../../../static/js/modules/api.js');
        expect(window.API).toBeDefined();
    });

    it('API.cookies 应该包含 list 方法', async () => {
        await import('../../../static/js/modules/api.js');
        expect(typeof window.API.cookies.list).toBe('function');
    });

    it('API.cookies 应该包含 update 方法', async () => {
        await import('../../../static/js/modules/api.js');
        expect(typeof window.API.cookies.update).toBe('function');
    });

    it('API.cookies 应该包含 delete 方法', async () => {
        await import('../../../static/js/modules/api.js');
        expect(typeof window.API.cookies.delete).toBe('function');
    });

    it('API.keywords 应该包含 list 方法', async () => {
        await import('../../../static/js/modules/api.js');
        expect(typeof window.API.keywords.list).toBe('function');
    });

    it('API.keywords 应该包含 delete 方法', async () => {
        await import('../../../static/js/modules/api.js');
        expect(typeof window.API.keywords.delete).toBe('function');
    });

    it('API.items 应该包含 list 方法', async () => {
        await import('../../../static/js/modules/api.js');
        expect(typeof window.API.items.list).toBe('function');
    });

    it('API.ai 应该包含 getSettings 方法', async () => {
        await import('../../../static/js/modules/api.js');
        expect(typeof window.API.ai.getSettings).toBe('function');
    });

    it('API.ai 应该包含 saveSettings 方法', async () => {
        await import('../../../static/js/modules/api.js');
        expect(typeof window.API.ai.saveSettings).toBe('function');
    });

    it('API.cards 应该包含 list 方法', async () => {
        await import('../../../static/js/modules/api.js');
        expect(typeof window.API.cards.list).toBe('function');
    });

    it('API.delivery 应该包含 list 方法', async () => {
        await import('../../../static/js/modules/api.js');
        expect(typeof window.API.delivery.list).toBe('function');
    });

    it('API.logs 应该包含 list 方法', async () => {
        await import('../../../static/js/modules/api.js');
        expect(typeof window.API.logs.list).toBe('function');
    });

    it('window.showToast 应该是函数', async () => {
        await import('../../../static/js/modules/api.js');
        expect(typeof window.showToast).toBe('function');
    });

    it('window.toggleLoading 应该是函数', async () => {
        await import('../../../static/js/modules/api.js');
        expect(typeof window.toggleLoading).toBe('function');
    });
});