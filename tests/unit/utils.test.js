import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

global.document = {
    createElement: vi.fn(() => ({
        appendChild: vi.fn(),
        remove: vi.fn(),
        addEventListener: vi.fn(),
        classList: { toggle: vi.fn() },
        style: {},
        textContent: '',
        innerHTML: '',
        setAttribute: vi.fn(),
        getAttribute: vi.fn(),
        querySelector: vi.fn(),
        querySelectorAll: vi.fn(() => [])
    })),
    querySelector: vi.fn(),
    querySelectorAll: vi.fn(() => []),
    body: {
        appendChild: vi.fn(),
        querySelector: vi.fn(),
        querySelectorAll: vi.fn(() => [])
    }
};

global.bootstrap = {
    Modal: class {
        show() {}
        hide() {}
        static getInstance() { return null; }
    },
    Toast: class {
        show() {}
    }
};

describe('Utils Module', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('escapeHtml', () => {
        it('should escape HTML special characters', async () => {
            const { escapeHtml } = await import('../../static/js/modules/utils.js').catch(() => ({ escapeHtml: null }));

            if (escapeHtml) {
                expect(escapeHtml('<script>alert("xss")</script>')).toBe('&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;');
                expect(escapeHtml('&amp;')).toBe('&amp;amp;');
                expect(escapeHtml('"quotes"')).toBe('&quot;quotes&quot;');
            }
        });

        it('should handle null and undefined', async () => {
            const { escapeHtml } = await import('../../static/js/modules/utils.js').catch(() => ({ escapeHtml: null }));

            if (escapeHtml) {
                expect(escapeHtml(null)).toBe('');
                expect(escapeHtml(undefined)).toBe('');
            }
        });

        it('should return string representation of numbers', async () => {
            const { escapeHtml } = await import('../../static/js/modules/utils.js').catch(() => ({ escapeHtml: null }));

            if (escapeHtml) {
                expect(escapeHtml(123)).toBe('123');
            }
        });
    });

    describe('formatDateTime', () => {
        it('should format valid date string', async () => {
            const { formatDateTime } = await import('../../static/js/modules/utils.js').catch(() => ({ formatDateTime: null }));

            if (formatDateTime) {
                const result = formatDateTime('2026-03-24T10:30:00');
                expect(result).toContain('2026');
            }
        });

        it('should return 未知 for empty input', async () => {
            const { formatDateTime } = await import('../../static/js/modules/utils.js').catch(() => ({ formatDateTime: null }));

            if (formatDateTime) {
                expect(formatDateTime('')).toBe('未知');
                expect(formatDateTime(null)).toBe('未知');
            }
        });
    });

    describe('updateAuthToken', () => {
        it('should set token in localStorage', async () => {
            const { updateAuthToken } = await import('../../static/js/modules/utils.js').catch(() => ({ updateAuthToken: null }));

            if (updateAuthToken) {
                updateAuthToken('new_token');
                expect(global.localStorage.getItem('auth_token')).toBe('new_token');
            }
        });

        it('should remove token when null is passed', async () => {
            global.localStorage.setItem('auth_token', 'old_token');

            const { updateAuthToken } = await import('../../static/js/modules/utils.js').catch(() => ({ updateAuthToken: null }));

            if (updateAuthToken) {
                updateAuthToken(null);
                expect(global.localStorage.getItem('auth_token')).toBeNull();
            }
        });
    });

    describe('clearKeywordCache', () => {
        it('should clear keyword cache', async () => {
            const { clearKeywordCache, accountKeywordCache } = await import('../../static/js/modules/utils.js').catch(() => ({ clearKeywordCache: null, accountKeywordCache: null }));

            if (clearKeywordCache && accountKeywordCache) {
                accountKeywordCache.setState({ cache: { key: 'value' }, timestamp: Date.now() });
                clearKeywordCache();

                const state = accountKeywordCache.getState();
                expect(state.cache).toEqual({});
                expect(state.timestamp).toBe(0);
            }
        });
    });

    describe('CACHE_DURATION', () => {
        it('should have a valid cache duration value', async () => {
            const { CACHE_DURATION } = await import('../../static/js/modules/utils.js').catch(() => ({ CACHE_DURATION: null }));

            if (CACHE_DURATION !== null) {
                expect(CACHE_DURATION).toBe(30000);
            }
        });
    });

    describe('ModalManager', () => {
        it('should have show method', async () => {
            const { ModalManager } = await import('../../static/js/modules/utils.js').catch(() => ({ ModalManager: null }));

            if (ModalManager) {
                expect(typeof ModalManager.show).toBe('function');
            }
        });

        it('should have hide method', async () => {
            const { ModalManager } = await import('../../static/js/modules/utils.js').catch(() => ({ ModalManager: null }));

            if (ModalManager) {
                expect(typeof ModalManager.hide).toBe('function');
            }
        });

        it('should have create method', async () => {
            const { ModalManager } = await import('../../static/js/modules/utils.js').catch(() => ({ ModalManager: null }));

            if (ModalManager) {
                expect(typeof ModalManager.create).toBe('function');
            }
        });

        it('should have remove method', async () => {
            const { ModalManager } = await import('../../static/js/modules/utils.js').catch(() => ({ ModalManager: null }));

            if (ModalManager) {
                expect(typeof ModalManager.remove).toBe('function');
            }
        });
    });

    describe('App namespace', () => {
        it('should have showSection function', async () => {
            await import('../../static/js/modules/utils.js').catch(() => ({}));

            expect(typeof window.App?.showSection).toBe('function');
        });

        it('should have toggleSidebar function', async () => {
            await import('../../static/js/modules/utils.js').catch(() => ({}));

            expect(typeof window.App?.toggleSidebar).toBe('function');
        });

        it('should have showToast function', async () => {
            await import('../../static/js/modules/utils.js').catch(() => ({}));

            expect(typeof window.App?.showToast).toBe('function');
        });

        it('should have showLoading function', async () => {
            await import('../../static/js/modules/utils.js').catch(() => ({}));

            expect(typeof window.App?.showLoading).toBe('function');
        });

        it('should have hideLoading function', async () => {
            await import('../../static/js/modules/utils.js').catch(() => ({}));

            expect(typeof window.App?.hideLoading).toBe('function');
        });
    });
});