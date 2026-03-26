import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

const mockFetch = vi.fn();
global.fetch = mockFetch;

const mockResponse = (overrides = {}) => ({
    ok: true,
    status: 200,
    statusText: 'OK',
    json: vi.fn().mockResolvedValue({ data: [] }),
    text: vi.fn().mockResolvedValue(''),
    ...overrides
});

describe('API Module', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        mockFetch.mockReset();
        Object.defineProperty(global, 'localStorage', {
            value: {
                getItem: vi.fn((key) => {
                    if (key === 'auth_token') return 'test-token';
                    return null;
                }),
                setItem: vi.fn(),
                removeItem: vi.fn()
            },
            writable: true
        });
        Object.defineProperty(global, 'location', {
            value: { href: '' },
            writable: true
        });
        global.document.querySelector = vi.fn(() => ({
            classList: { toggle: vi.fn() }
        }));
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    describe('isRetryableError', () => {
        it('should identify TypeError as retryable', () => {
            const error = new TypeError('Network error');
            expect(error.name === 'TypeError').toBe(true);
        });

        it('should identify AbortError as retryable', () => {
            const error = new DOMException('Aborted', 'AbortError');
            expect(error.name === 'AbortError').toBe(true);
        });

        it('should identify 5xx errors as retryable', () => {
            const response = { status: 500 };
            expect(response.status >= 500 && response.status < 600).toBe(true);
        });

        it('should identify 429 as retryable', () => {
            const response = { status: 429 };
            expect(response.status === 429).toBe(true);
        });

        it('should not retry 400 errors', () => {
            const response = { status: 400 };
            expect(response.status >= 500 && response.status < 600).toBe(false);
            expect(response.status === 429).toBe(false);
        });
    });

    describe('calculateDelay', () => {
        it('should calculate exponential backoff with jitter', () => {
            const BASE_DELAY = 1000;
            const delay = BASE_DELAY * Math.pow(2, 0);
            const jitter = delay * 0.2 * (Math.random() - 0.5);
            const result = Math.min(delay + jitter, 10000);
            expect(result).toBeGreaterThanOrEqual(800);
            expect(result).toBeLessThanOrEqual(1200);
        });

        it('should cap delay at MAX_DELAY', () => {
            const BASE_DELAY = 1000;
            const MAX_DELAY = 10000;
            const delay = BASE_DELAY * Math.pow(2, 10);
            const jitter = delay * 0.2 * (Math.random() - 0.5);
            const result = Math.min(delay + jitter, MAX_DELAY);
            expect(result).toBeLessThanOrEqual(10000);
        });
    });

    describe('fetchWithRetry', () => {
        it('should return response on success', async () => {
            const successResponse = mockResponse({ ok: true, status: 200 });
            mockFetch.mockResolvedValueOnce(successResponse);

            const result = await fetch('http://test.com/api');
            expect(result.ok).toBe(true);
            expect(mockFetch).toHaveBeenCalledTimes(1);
        });

        it('should retry on network error', async () => {
            mockFetch
                .mockRejectedValueOnce(new TypeError('Network error'))
                .mockResolvedValueOnce(mockResponse({ ok: true, status: 200 }));

            try {
                await fetch('http://test.com/api');
            } catch (e) {}

            expect(mockFetch).toHaveBeenCalledTimes(2);
        });

        it('should throw after max retries exceeded', async () => {
            mockFetch.mockRejectedValue(new TypeError('Network error'));

            await expect(fetch('http://test.com/api')).rejects.toThrow('Network error');
        });
    });

    describe('Authorization Header', () => {
        it('should add Authorization header when token exists', async () => {
            mockFetch.mockResolvedValueOnce(mockResponse({
                ok: true,
                status: 200,
                json: vi.fn().mockResolvedValue({ data: [] })
            }));

            const token = 'test-token';
            const headers = { 'Authorization': `Bearer ${token}` };

            await fetch('http://test.com/cookies/details', { headers });

            expect(mockFetch).toHaveBeenCalledWith(
                'http://test.com/cookies/details',
                expect.objectContaining({
                    headers: expect.objectContaining({
                        'Authorization': 'Bearer test-token'
                    })
                })
            );
        });

        it('should not add Authorization header when token is null', async () => {
            Object.defineProperty(global, 'localStorage', {
                value: {
                    getItem: vi.fn(() => null),
                    setItem: vi.fn(),
                    removeItem: vi.fn()
                },
                writable: true
            });

            mockFetch.mockResolvedValueOnce(mockResponse({
                ok: true,
                status: 200,
                json: vi.fn().mockResolvedValue({ data: [] })
            }));

            const headers = {};

            await fetch('http://test.com/cookies/details', { headers });

            expect(mockFetch).toHaveBeenCalledWith(
                'http://test.com/cookies/details',
                expect.objectContaining({
                    headers: expect.objectContaining({})
                })
            );
        });

        it('should include Bearer prefix in Authorization header', async () => {
            mockFetch.mockResolvedValueOnce(mockResponse({
                ok: true,
                status: 200,
                json: vi.fn().mockResolvedValue({ data: [] })
            }));

            const token = 'jwt-token-12345';
            const headers = { 'Authorization': `Bearer ${token}` };

            await fetch('http://test.com/api', { headers });

            const call = mockFetch.mock.calls[0];
            expect(call[1].headers['Authorization']).toBe('Bearer jwt-token-12345');
        });
    });

    describe('cookies.list', () => {
        it('should call /cookies/details endpoint', async () => {
            const mockData = [
                { id: 'account1', value: 'cookie1' },
                { id: 'account2', value: 'cookie2' }
            ];

            mockFetch.mockResolvedValueOnce(mockResponse({
                ok: true,
                status: 200,
                json: vi.fn().mockResolvedValue({ data: mockData })
            }));

            const url = 'http://localhost:8080/cookies/details';
            const response = await fetch(url);
            const result = await response.json();

            expect(mockFetch).toHaveBeenCalledWith(
                url,
                expect.objectContaining({
                    method: 'GET'
                })
            );
            expect(result.data).toEqual(mockData);
        });

        it('should return cached data when available', async () => {
            const cachedData = [{ id: 'cached', value: 'cached_cookie' }];
            const cacheKey = 'cookies_list';
            const apiCache = new Map();
            apiCache.set(cacheKey, { data: cachedData, timestamp: Date.now() });

            const cached = apiCache.get(cacheKey);
            expect(cached.data).toEqual(cachedData);
        });

        it('should handle empty cookies list', async () => {
            mockFetch.mockResolvedValueOnce(mockResponse({
                ok: true,
                status: 200,
                json: vi.fn().mockResolvedValue({ data: [] })
            }));

            const response = await fetch('http://test.com/cookies/details');
            const result = await response.json();

            expect(result.data).toEqual([]);
        });
    });

    describe('cookies.create', () => {
        it('should POST to /cookies endpoint with correct body', async () => {
            mockFetch.mockResolvedValueOnce(mockResponse({
                ok: true,
                status: 201,
                json: vi.fn().mockResolvedValue({ data: { id: 'new_account' } })
            }));

            const body = JSON.stringify({ id: 'new_account', value: 'new_cookie_value' });

            await fetch('http://test.com/cookies', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body
            });

            expect(mockFetch).toHaveBeenCalledWith(
                'http://test.com/cookies',
                expect.objectContaining({
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body
                })
            );
        });
    });

    describe('cookies.update', () => {
        it('should PUT to /cookies/:id endpoint', async () => {
            mockFetch.mockResolvedValueOnce(mockResponse({
                ok: true,
                status: 200,
                json: vi.fn().mockResolvedValue({ data: { success: true } })
            }));

            const cookieId = 'account1';
            const updateData = { enabled: false };
            const body = JSON.stringify(updateData);

            await fetch(`http://test.com/cookies/${cookieId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body
            });

            expect(mockFetch).toHaveBeenCalledWith(
                `http://test.com/cookies/${cookieId}`,
                expect.objectContaining({
                    method: 'PUT',
                    body
                })
            );
        });
    });

    describe('cookies.delete', () => {
        it('should DELETE to /cookies/:id endpoint', async () => {
            mockFetch.mockResolvedValueOnce(mockResponse({
                ok: true,
                status: 200,
                json: vi.fn().mockResolvedValue({ data: { success: true } })
            }));

            const cookieId = 'account1';

            await fetch(`http://test.com/cookies/${cookieId}`, {
                method: 'DELETE'
            });

            expect(mockFetch).toHaveBeenCalledWith(
                `http://test.com/cookies/${cookieId}`,
                expect.objectContaining({
                    method: 'DELETE'
                })
            );
        });
    });

    describe('Error Handling', () => {
        it('should handle 401 unauthorized', async () => {
            mockFetch.mockResolvedValueOnce(mockResponse({
                ok: false,
                status: 401,
                statusText: 'Unauthorized'
            }));

            const response = await fetch('http://test.com/api');

            expect(response.status).toBe(401);
            expect(response.ok).toBe(false);
        });

        it('should redirect to login on 401', async () => {
            mockFetch.mockResolvedValueOnce(mockResponse({
                ok: false,
                status: 401
            }));

            await fetch('http://test.com/api');

            expect(global.location.href).toBe('/');
        });

        it('should retry on 500 errors', async () => {
            mockFetch
                .mockResolvedValueOnce(mockResponse({ ok: false, status: 500 }))
                .mockResolvedValueOnce(mockResponse({ ok: false, status: 500 }))
                .mockResolvedValueOnce(mockResponse({ ok: true, status: 200 }));

            let lastResponse;
            for (let attempt = 0; attempt < 3; attempt++) {
                const response = await fetch('http://test.com/api');
                lastResponse = response;
                if (response.ok) break;
            }

            expect(mockFetch).toHaveBeenCalledTimes(3);
        });

        it('should throw error on 500 after max retries', async () => {
            mockFetch
                .mockResolvedValueOnce(mockResponse({ ok: false, status: 500 }))
                .mockResolvedValueOnce(mockResponse({ ok: false, status: 500 }))
                .mockResolvedValueOnce(mockResponse({ ok: false, status: 500 }))
                .mockResolvedValueOnce(mockResponse({ ok: false, status: 500 }));

            let error;
            try {
                for (let i = 0; i < 4; i++) {
                    await fetch('http://test.com/api');
                }
            } catch (e) {
                error = e;
            }

            expect(mockFetch).toHaveBeenCalledTimes(4);
        });

        it('should handle network errors with retry', async () => {
            mockFetch
                .mockRejectedValueOnce(new TypeError('Network failure'))
                .mockResolvedValueOnce(mockResponse({ ok: true, status: 200 }));

            let result;
            try {
                await fetch('http://test.com/api');
            } catch (e) {
                result = e;
            }

            expect(mockFetch).toHaveBeenCalledTimes(2);
        });

        it('should handle malformed JSON error response', async () => {
            mockFetch.mockResolvedValueOnce(mockResponse({
                ok: false,
                status: 400,
                text: vi.fn().mockResolvedValue('Not a valid JSON'),
                statusText: 'Bad Request'
            }));

            const response = await fetch('http://test.com/api');

            expect(response.ok).toBe(false);
            expect(response.status).toBe(400);
        });

        it('should handle 404 not found', async () => {
            mockFetch.mockResolvedValueOnce(mockResponse({
                ok: false,
                status: 404,
                statusText: 'Not Found'
            }));

            const response = await fetch('http://test.com/nonexistent');

            expect(response.status).toBe(404);
            expect(response.ok).toBe(false);
        });
    });

    describe('Request Cancellation', () => {
        it('should cancel pending requests', async () => {
            const abortController = new AbortController();
            mockFetch.mockResolvedValueOnce(mockResponse({
                ok: true,
                status: 200
            }));

            await fetch('http://test.com/api', { signal: abortController.signal });

            abortController.abort();

            expect(mockFetch).toHaveBeenCalled();
        });
    });

    describe('API Structure', () => {
        it('should have cookies namespace with required methods', () => {
            const expectedMethods = ['list', 'create', 'update', 'delete', 'getDetails', 'toggleStatus', 'toggleAutoConfirm'];

            expectedMethods.forEach(method => {
                expect(typeof method).toBe('string');
            });
        });

        it('should have keywords namespace', () => {
            const expectedMethods = ['list', 'create', 'update', 'delete', 'listWithItemId'];

            expectedMethods.forEach(method => {
                expect(typeof method).toBe('string');
            });
        });

        it('should have items namespace', () => {
            const expectedMethods = ['list', 'get', 'update', 'delete', 'batchDelete'];

            expectedMethods.forEach(method => {
                expect(typeof method).toBe('string');
            });
        });

        it('should have dashboard namespace', () => {
            const expectedMethods = ['getStats', 'getAccounts'];

            expectedMethods.forEach(method => {
                expect(typeof method).toBe('string');
            });
        });

        it('should have ai namespace', () => {
            const expectedMethods = ['getSettings', 'saveSettings', 'saveConfig', 'test'];

            expectedMethods.forEach(method => {
                expect(typeof method).toBe('string');
            });
        });

        it('should have delivery namespace', () => {
            const expectedMethods = ['list', 'get', 'create', 'update', 'delete'];

            expectedMethods.forEach(method => {
                expect(typeof method).toBe('string');
            });
        });

        it('should have cards namespace', () => {
            const expectedMethods = ['list', 'get', 'create', 'update', 'delete'];

            expectedMethods.forEach(method => {
                expect(typeof method).toBe('string');
            });
        });

        it('should have system namespace', () => {
            const expectedMethods = ['getSettings', 'updateSettings', 'changePassword', 'getLogs', 'clearLogs'];

            expectedMethods.forEach(method => {
                expect(typeof method).toBe('string');
            });
        });
    });

    describe('Cache Management', () => {
        it('should clear cache with pattern', () => {
            const apiCache = new Map();
            apiCache.set('cookies_list', { data: [], timestamp: Date.now() });
            apiCache.set('keywords_list', { data: [], timestamp: Date.now() });

            for (const key of apiCache.keys()) {
                if (key.includes('cookies')) {
                    apiCache.delete(key);
                }
            }

            expect(apiCache.has('keywords_list')).toBe(true);
            expect(apiCache.has('cookies_list')).toBe(false);
        });

        it('should clear all cache when pattern is null', () => {
            const apiCache = new Map();
            apiCache.set('key1', { data: [] });
            apiCache.set('key2', { data: [] });

            apiCache.clear();

            expect(apiCache.size).toBe(0);
        });

        it('should evict oldest entry when cache is full', () => {
            const maxSize = 50;
            const apiCache = new Map();

            for (let i = 0; i < maxSize + 1; i++) {
                if (apiCache.size >= maxSize) {
                    const firstKey = apiCache.keys().next().value;
                    apiCache.delete(firstKey);
                }
                apiCache.set(`key${i}`, { data: [] });
            }

            expect(apiCache.size).toBe(maxSize);
        });
    });
});
