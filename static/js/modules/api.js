// API 模块 - 统一 API 命名空间
import { authToken, apiBase } from './utils.js';

/**
 * 最大重试次数
 * @type {number}
 */
const MAX_RETRIES = 3;

/**
 * 基础延迟时间（毫秒）
 * @type {number}
 */
const BASE_DELAY = 1000;

/**
 * 最大延迟时间（毫秒）
 * @type {number}
 */
const MAX_DELAY = 10000;

/**
 * AbortController 实例，用于取消请求
 * @type {AbortController|null}
 */
let abortController = null;

/**
 * 判断错误是否可重试
 * @param {Error} error - 错误对象
 * @param {Response} [response=null] - 响应对象
 * @returns {boolean} 是否可重试
 */
function isRetryableError(error, response = null) {
    if (error.name === 'TypeError') return true;
    if (error.name === 'AbortError') return true;
    if (response && response.status >= 500 && response.status < 600) return true;
    if (response && response.status === 429) return true;
    return false;
}

/**
 * 计算重试延迟时间（带抖动）
 * @param {number} retryCount - 当前重试次数
 * @returns {number} 延迟时间（毫秒）
 */
function calculateDelay(retryCount) {
    const delay = BASE_DELAY * Math.pow(2, retryCount);
    const jitter = delay * 0.2 * (Math.random() - 0.5);
    return Math.min(delay + jitter, MAX_DELAY);
}

/**
 * 延迟函数
 * @param {number} ms - 延迟时间（毫秒）
 * @returns {Promise<void>}
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 带重试的 fetch 请求
 * @param {string} url - 请求 URL
 * @param {RequestInit} [options={}] - fetch 选项
 * @param {number} [retries=MAX_RETRIES] - 最大重试次数
 * @returns {Promise<Response>} 响应对象
 * @throws {Error} 请求失败或已达最大重试次数
 */
async function fetchWithRetry(url, options = {}, retries = MAX_RETRIES) {
    let lastError = null;
    for (let attempt = 0; attempt <= retries; attempt++) {
        try {
            const response = await fetch(url, options);
            if (!response.ok && isRetryableError(null, response) && attempt < retries) {
                const delay = calculateDelay(attempt);
                console.warn(`[API] 请求失败 (HTTP ${response.status})，${delay}ms 后重试 (${attempt + 1}/${MAX_RETRIES})`);
                await sleep(delay);
                continue;
            }
            return response;
        } catch (error) {
            lastError = error;
            if (isRetryableError(error) && attempt < retries) {
                const delay = calculateDelay(attempt);
                console.warn(`[API] 请求失败 (${error.message})，${delay}ms 后重试 (${attempt + 1}/${MAX_RETRIES})`);
                await sleep(delay);
                continue;
            }
            throw error;
        }
    }
    throw lastError || new Error('请求失败，已达最大重试次数');
}

/**
 * 显示 Toast 通知
 * @param {string} message - 消息内容
 * @param {'success'|'danger'|'warning'|'info'} [type='success'] - 消息类型
 */
function showToast(message, type = 'success') {
    const toastContainer = document.querySelector('.toast-container');
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body"></div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    toast.querySelector('.toast-body').textContent = message;
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
    bsToast.show();
    toast.addEventListener('hidden.bs.toast', () => toast.remove());
}

/**
 * 显示/隐藏加载状态
 * @param {boolean} show - 是否显示加载状态
 */
function toggleLoading(show) {
    document.getElementById('loading').classList.toggle('d-none', !show);
}

/**
 * 处理 API 错误
 * @param {Error} err - 错误对象
 */
function handleApiError(err) {
    console.error(err);
    showToast(err.message || '操作失败', 'danger');
    toggleLoading(false);
}

/**
 * 发送 JSON 请求并自动处理响应
 * @param {string} url - 请求 URL
 * @param {RequestInit} [opts={}] - fetch 选项
 * @returns {Promise<any>} 响应数据
 * @throws {Error} 请求失败时抛出错误
 */
async function fetchJSON(url, opts = {}) {
    toggleLoading(true);
    try {
        const token = authToken.value;
        if (token) {
            opts.headers = opts.headers || {};
            opts.headers['Authorization'] = `Bearer ${token}`;
        }
        const res = await fetchWithRetry(url, opts);
        if (res.status === 401) {
            localStorage.removeItem('auth_token');
            window.location.href = '/';
            return;
        }
        if (!res.ok) {
            let errorMessage = `HTTP ${res.status}`;
            try {
                const errorText = await res.text();
                if (errorText) {
                    try {
                        const errorJson = JSON.parse(errorText);
                        errorMessage = errorJson.detail || errorJson.message || errorText;
                    } catch {
                        errorMessage = errorText;
                    }
                }
            } catch {
                errorMessage = `HTTP ${res.status} ${res.statusText}`;
            }
            throw new Error(errorMessage);
        }
        const jsonResponse = await res.json();
        toggleLoading(false);
        return jsonResponse.data !== undefined ? jsonResponse.data : jsonResponse;
    } catch (err) {
        handleApiError(err);
        throw err;
    }
}

/**
 * API 统一命名空间
 * @namespace API
 */
window.API = {
    /**
     * 通用请求方法
     * @param {string} url - 请求 URL
     * @param {RequestInit} [options={}] - fetch 选项
     * @returns {Promise<any>} 响应数据
     */
    _request: async function(url, options = {}) {
        const token = authToken.value;
        const headers = { ...options.headers };
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        const opts = { ...options, headers };

        abortController = new AbortController();
        opts.signal = abortController.signal;

        toggleLoading(true);
        try {
            const res = await fetchWithRetry(url, opts);
            if (res.status === 401) {
                localStorage.removeItem('auth_token');
                window.location.href = '/';
                return null;
            }
            if (!res.ok) {
                let errorMessage = `HTTP ${res.status}`;
                try {
                    const errorText = await res.text();
                    if (errorText) {
                        try {
                            const errorJson = JSON.parse(errorText);
                            errorMessage = errorJson.detail || errorJson.message || errorText;
                        } catch {
                            errorMessage = errorText;
                        }
                    }
                } catch {
                    errorMessage = `HTTP ${res.status} ${res.statusText}`;
                }
                throw new Error(errorMessage);
            }
            const jsonResponse = await res.json();
            toggleLoading(false);
            return jsonResponse.data !== undefined ? jsonResponse.data : jsonResponse;
        } catch (err) {
            handleApiError(err);
            throw err;
        }
    },

    /**
     * 获取认证头
     * @returns {Object} 包含 Authorization 的请求头对象
     */
    _getAuthHeader: function() {
        const token = authToken.value;
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    },

    /**
     * 取消 pending 的请求
     */
    cancelPending: function() {
        if (abortController) {
            abortController.abort();
            abortController = null;
        }
    },

    /**
     * Cookie 管理 API
     * @namespace API.cookies
     */
    cookies: {
        /**
         * 获取所有 Cookie 列表
         * @returns {Promise<Array>} Cookie 列表
         * @throws {Error} 请求失败时抛出错误
         */
        list: async function() {
            return await fetchJSON(`${apiBase}/cookies/details`);
        },

        /**
         * 创建新 Cookie
         * @param {string} id - Cookie ID
         * @param {string} value - Cookie 值
         * @returns {Promise<Object>} 创建的 Cookie 对象
         * @throws {Error} 请求失败时抛出错误
         */
        create: async function(id, value) {
            return await fetchJSON(`${apiBase}/cookies`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id, value })
            });
        },

        /**
         * 更新 Cookie 信息
         * @param {string} id - Cookie ID
         * @param {Object} data - 更新的数据
         * @returns {Promise<Object>} 更新后的 Cookie 对象
         * @throws {Error} 请求失败时抛出错误
         */
        update: async function(id, data) {
            return await fetchJSON(`${apiBase}/cookies/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        },

        /**
         * 删除 Cookie
         * @param {string} id - Cookie ID
         * @returns {Promise<Object>} 删除操作结果
         * @throws {Error} 请求失败时抛出错误
         */
        delete: async function(id) {
            return await fetchJSON(`${apiBase}/cookies/${id}`, { method: 'DELETE' });
        },

        /**
         * 获取 Cookie 详情
         * @param {string} cookieId - Cookie ID
         * @returns {Promise<Object>} Cookie 详情
         * @throws {Error} 请求失败时抛出错误
         */
        getDetails: async function(cookieId) {
            return await fetchJSON(`${apiBase}/cookies/details/${cookieId}`);
        },

        /**
         * 切换 Cookie 启用/禁用状态
         * @param {string} accountId - 账号 ID
         * @param {boolean} enabled - 是否启用
         * @returns {Promise<Object>} 操作结果
         * @throws {Error} 请求失败时抛出错误
         */
        toggleStatus: async function(accountId, enabled) {
            return await this._request(`${apiBase}/cookies/${accountId}/status`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled })
            });
        },

        /**
         * 切换自动确认收货状态
         * @param {string} accountId - 账号 ID
         * @param {boolean} enabled - 是否启用自动确认
         * @returns {Promise<Object>} 操作结果
         * @throws {Error} 请求失败时抛出错误
         */
        toggleAutoConfirm: async function(accountId, enabled) {
            return await this._request(`${apiBase}/cookies/${accountId}/auto-confirm`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ auto_confirm: enabled })
            });
        }
    },

    /**
     * 关键词管理 API
     * @namespace API.keywords
     */
    keywords: {
        /**
         * 获取关键词列表
         * @param {string} cookieId - Cookie ID
         * @returns {Promise<Array>} 关键词列表
         * @throws {Error} 请求失败时抛出错误
         */
        list: async function(cookieId) {
            return await fetchJSON(`${apiBase}/keywords/${cookieId}`);
        },

        /**
         * 获取带商品 ID 的关键词列表
         * @param {string} cookieId - Cookie ID
         * @returns {Promise<Array>} 关键词列表（包含商品 ID）
         * @throws {Error} 请求失败时抛出错误
         */
        listWithItemId: async function(cookieId) {
            return await fetchJSON(`${apiBase}/keywords-with-item-id/${cookieId}`);
        },

        /**
         * 创建关键词
         * @param {string} cookieId - Cookie ID
         * @param {string} keyword - 关键词
         * @param {string} reply - 回复内容
         * @param {string} [itemId] - 商品 ID（可选）
         * @returns {Promise<Object>} 创建的关键词对象
         * @throws {Error} 请求失败时抛出错误
         */
        create: async function(cookieId, keyword, reply, itemId) {
            return await this._request(`${apiBase}/keywords-with-item-id/${cookieId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ keywords: [{ keyword, reply, item_id: itemId }] })
            });
        },

        /**
         * 更新关键词
         * @param {number} keywordId - 关键词 ID
         * @param {Object} data - 更新的数据
         * @returns {Promise<Object>} 更新后的关键词对象
         * @throws {Error} 请求失败时抛出错误
         */
        update: async function(keywordId, data) {
            return await this._request(`${apiBase}/keywords/${keywordId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        },

        /**
         * 删除关键词
         * @param {string} cookieId - Cookie ID
         * @param {number} keywordId - 关键词 ID
         * @returns {Promise<Object>} 删除操作结果
         * @throws {Error} 请求失败时抛出错误
         */
        delete: async function(cookieId, keywordId) {
            return await this._request(`${apiBase}/keywords/${cookieId}/${keywordId}`, {
                method: 'DELETE'
            });
        },

        /**
         * 添加关键词图片
         * @param {string} cookieId - Cookie ID
         * @param {FormData} formData - 包含图片的 FormData
         * @returns {Promise<Object>} 上传结果
         * @throws {Error} 请求失败时抛出错误
         */
        addImage: async function(cookieId, formData) {
            return await this._request(`${apiBase}/keywords/${cookieId}/image`, {
                method: 'POST',
                body: formData
            });
        },

        /**
         * 导出关键词
         * @param {string} cookieId - Cookie ID
         * @returns {Promise<Object>} 导出结果
         * @throws {Error} 请求失败时抛出错误
         */
        export: async function(cookieId) {
            return await this._request(`${apiBase}/keywords-export/${cookieId}`);
        },

        /**
         * 导入关键词
         * @param {string} cookieId - Cookie ID
         * @param {FormData} formData - 包含关键词文件的 FormData
         * @returns {Promise<Object>} 导入结果
         * @throws {Error} 请求失败时抛出错误
         */
        import: async function(cookieId, formData) {
            return await this._request(`${apiBase}/keywords-import/${cookieId}`, {
                method: 'POST',
                body: formData
            });
        }
    },

    /**
     * 商品管理 API
     * @namespace API.items
     */
    items: {
        /**
         * 获取商品列表
         * @returns {Promise<Array>} 商品列表
         * @throws {Error} 请求失败时抛出错误
         */
        list: async function() {
            const cacheKey = 'items_list';
            const cached = getCached(cacheKey);
            if (cached) return cached;
            const result = await fetchJSON(`${apiBase}/items`);
            setCache(cacheKey, result);
            return result;
        },

        /**
         * 获取单个商品详情
         * @param {string} cookieId - Cookie ID
         * @param {string} itemId - 商品 ID
         * @returns {Promise<Object>} 商品详情
         * @throws {Error} 请求失败时抛出错误
         */
        get: async function(cookieId, itemId) {
            return await fetchJSON(`${apiBase}/items/${encodeURIComponent(cookieId)}/${encodeURIComponent(itemId)}`);
        },

        /**
         * 根据 Cookie 获取商品列表
         * @param {string} cookieId - Cookie ID
         * @returns {Promise<Array>} 商品列表
         * @throws {Error} 请求失败时抛出错误
         */
        getByCookie: async function(cookieId) {
            return await fetchJSON(`${apiBase}/items/cookie/${encodeURIComponent(cookieId)}`);
        },

        /**
         * 分页获取商品列表
         * @param {string} cookieId - Cookie ID
         * @param {number} pageNumber - 页码
         * @param {number} [pageSize=20] - 每页数量
         * @returns {Promise<Object>} 分页结果
         * @throws {Error} 请求失败时抛出错误
         */
        getByPage: async function(cookieId, pageNumber, pageSize = 20) {
            return await this._request(`${apiBase}/items/get-by-page`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    cookie_id: cookieId,
                    page_number: pageNumber,
                    page_size: pageSize
                })
            });
        },

        /**
         * 获取账号下所有商品
         * @param {string} cookieId - Cookie ID
         * @returns {Promise<Object>} 商品列表结果
         * @throws {Error} 请求失败时抛出错误
         */
        getAllFromAccount: async function(cookieId) {
            return await this._request(`${apiBase}/items/get-all-from-account`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cookie_id: cookieId })
            });
        },

        /**
         * 更新商品信息
         * @param {string} cookieId - Cookie ID
         * @param {string} itemId - 商品 ID
         * @param {Object} itemDetail - 商品详情
         * @returns {Promise<Object>} 更新结果
         * @throws {Error} 请求失败时抛出错误
         */
        update: async function(cookieId, itemId, itemDetail) {
            return await this._request(`${apiBase}/items/${encodeURIComponent(cookieId)}/${encodeURIComponent(itemId)}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ item_detail: itemDetail })
            });
        },

        /**
         * 删除商品
         * @param {string} cookieId - Cookie ID
         * @param {string} itemId - 商品 ID
         * @returns {Promise<Object>} 删除结果
         * @throws {Error} 请求失败时抛出错误
         */
        delete: async function(cookieId, itemId) {
            return await this._request(`${apiBase}/items/${encodeURIComponent(cookieId)}/${encodeURIComponent(itemId)}`, {
                method: 'DELETE'
            });
        },

        /**
         * 批量删除商品
         * @param {Array<Object>} items - 要删除的商品列表
         * @param {string} items[].cookie_id - Cookie ID
         * @param {string} items[].item_id - 商品 ID
         * @returns {Promise<Object>} 删除结果
         * @throws {Error} 请求失败时抛出错误
         */
        batchDelete: async function(items) {
            return await this._request(`${apiBase}/items/batch`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ items })
            });
        },

        /**
         * 切换多规格状态
         * @param {string} cookieId - Cookie ID
         * @param {string} itemId - 商品 ID
         * @param {boolean} isMultiSpec - 是否多规格
         * @returns {Promise<Object>} 操作结果
         * @throws {Error} 请求失败时抛出错误
         */
        toggleMultiSpec: async function(cookieId, itemId, isMultiSpec) {
            return await this._request(`${apiBase}/items/${encodeURIComponent(cookieId)}/${encodeURIComponent(itemId)}/multi-spec`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_multi_spec: isMultiSpec })
            });
        }
    },

    /**
     * 仪表盘 API
     * @namespace API.dashboard
     */
    dashboard: {
        /**
         * 获取统计数据
         * @returns {Promise<Object>} 统计数据
         * @throws {Error} 请求失败时抛出错误
         */
        getStats: async function() {
            return await fetchJSON(`${apiBase}/dashboard/stats`);
        },

        /**
         * 获取账号列表
         * @returns {Promise<Array>} 账号列表
         * @throws {Error} 请求失败时抛出错误
         */
        getAccounts: async function() {
            return await fetchJSON(`${apiBase}/cookies/details`);
        }
    },

    /**
     * AI 回复设置 API
     * @namespace API.ai
     */
    ai: {
        /**
         * 获取 AI 回复设置
         * @param {string} accountId - 账号 ID
         * @returns {Promise<Object>} AI 设置
         * @throws {Error} 请求失败时抛出错误
         */
        getSettings: async function(accountId) {
            return await fetchJSON(`${apiBase}/ai-reply-settings/${accountId}`);
        },

        /**
         * 保存 AI 回复设置
         * @param {string} accountId - 账号 ID
         * @param {Object} settings - 设置内容
         * @returns {Promise<Object>} 保存结果
         * @throws {Error} 请求失败时抛出错误
         */
        saveSettings: async function(accountId, settings) {
            return await this._request(`${apiBase}/ai-reply-settings/${accountId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
        },

        /**
         * 保存 AI 全局配置
         * @param {Object} config - 全局配置
         * @returns {Promise<Object>} 保存结果
         * @throws {Error} 请求失败时抛出错误
         */
        saveConfig: async function(config) {
            return await this._request(`${apiBase}/ai-reply-config`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
        },

        /**
         * 测试 AI 回复
         * @param {string} accountId - 账号 ID
         * @param {Object} testData - 测试数据
         * @returns {Promise<Object>} 测试结果
         * @throws {Error} 请求失败时抛出错误
         */
        test: async function(accountId, testData) {
            return await this._request(`${apiBase}/ai-reply-test/${accountId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(testData)
            });
        }
    },

    /**
     * 发货规则 API
     * @namespace API.delivery
     */
    delivery: {
        /**
         * 获取发货规则列表
         * @returns {Promise<Array>} 发货规则列表
         * @throws {Error} 请求失败时抛出错误
         */
        list: async function() {
            return await fetchJSON(`${apiBase}/delivery-rules`);
        },

        /**
         * 获取单个发货规则
         * @param {string} ruleId - 规则 ID
         * @returns {Promise<Object>} 发货规则详情
         * @throws {Error} 请求失败时抛出错误
         */
        get: async function(ruleId) {
            return await fetchJSON(`${apiBase}/delivery-rules/${ruleId}`);
        },

        /**
         * 创建发货规则
         * @param {Object} data - 规则数据
         * @returns {Promise<Object>} 创建的规则
         * @throws {Error} 请求失败时抛出错误
         */
        create: async function(data) {
            return await this._request(`${apiBase}/delivery-rules`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        },

        /**
         * 更新发货规则
         * @param {string} ruleId - 规则 ID
         * @param {Object} data - 更新的数据
         * @returns {Promise<Object>} 更新后的规则
         * @throws {Error} 请求失败时抛出错误
         */
        update: async function(ruleId, data) {
            return await this._request(`${apiBase}/delivery-rules/${ruleId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        },

        /**
         * 删除发货规则
         * @param {string} ruleId - 规则 ID
         * @returns {Promise<Object>} 删除结果
         * @throws {Error} 请求失败时抛出错误
         */
        delete: async function(ruleId) {
            return await this._request(`${apiBase}/delivery-rules/${ruleId}`, {
                method: 'DELETE'
            });
        }
    },

    /**
     * 默认回复 API
     * @namespace API.defaultReplies
     */
    defaultReplies: {
        /**
         * 获取默认回复列表
         * @returns {Promise<Array>} 默认回复列表
         * @throws {Error} 请求失败时抛出错误
         */
        list: async function() {
            return await fetchJSON(`${apiBase}/default-replies`);
        },

        /**
         * 获取账号的默认回复
         * @param {string} accountId - 账号 ID
         * @returns {Promise<Object>} 默认回复内容
         * @throws {Error} 请求失败时抛出错误
         */
        get: async function(accountId) {
            return await fetchJSON(`${apiBase}/default-replies/${accountId}`);
        },

        /**
         * 更新默认回复
         * @param {string} accountId - 账号 ID
         * @param {Object} data - 回复内容
         * @returns {Promise<Object>} 更新结果
         * @throws {Error} 请求失败时抛出错误
         */
        update: async function(accountId, data) {
            return await this._request(`${apiBase}/default-replies/${accountId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        },

        /**
         * 保存默认回复
         * @param {string} type - 回复类型
         * @param {string} content - 回复内容
         * @returns {Promise<Object>} 保存结果
         * @throws {Error} 请求失败时抛出错误
         */
        save: async function(type, content) {
            return await this._request(`${apiBase}/default-replies/${type}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content })
            });
        }
    },

    /**
     * 通知渠道 API
     * @namespace API.notifications
     */
    notifications: {
        /**
         * 获取通知渠道列表
         * @returns {Promise<Array>} 渠道列表
         * @throws {Error} 请求失败时抛出错误
         */
        getChannels: async function() {
            return await fetchJSON(`${apiBase}/notification-channels`);
        },

        /**
         * 添加通知渠道
         * @param {Object} data - 渠道配置数据
         * @returns {Promise<Object>} 创建的渠道
         * @throws {Error} 请求失败时抛出错误
         */
        addChannel: async function(data) {
            return await this._request(`${apiBase}/notification-channels`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        },

        /**
         * 更新通知渠道
         * @param {string} channelId - 渠道 ID
         * @param {Object} data - 更新的数据
         * @returns {Promise<Object>} 更新结果
         * @throws {Error} 请求失败时抛出错误
         */
        updateChannel: async function(channelId, data) {
            return await this._request(`${apiBase}/notification-channels/${channelId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        },

        /**
         * 删除通知渠道
         * @param {string} channelId - 渠道 ID
         * @returns {Promise<Object>} 删除结果
         * @throws {Error} 请求失败时抛出错误
         */
        deleteChannel: async function(channelId) {
            return await this._request(`${apiBase}/notification-channels/${channelId}`, {
                method: 'DELETE'
            });
        },

        /**
         * 获取消息通知配置
         * @returns {Promise<Object>} 消息通知配置
         * @throws {Error} 请求失败时抛出错误
         */
        getMessageConfig: async function() {
            return await fetchJSON(`${apiBase}/message-notifications`);
        },

        /**
         * 获取账号的消息通知配置
         * @param {string} accountId - 账号 ID
         * @returns {Promise<Object>} 账号通知配置
         * @throws {Error} 请求失败时抛出错误
         */
        getAccountConfig: async function(accountId) {
            return await fetchJSON(`${apiBase}/message-notifications/${accountId}`);
        },

        /**
         * 保存账号消息通知配置
         * @param {string} accountId - 账号 ID
         * @param {Object} data - 通知配置
         * @returns {Promise<Object>} 保存结果
         * @throws {Error} 请求失败时抛出错误
         */
        saveAccountConfig: async function(accountId, data) {
            return await this._request(`${apiBase}/message-notifications/${accountId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        },

        /**
         * 删除账号消息通知配置
         * @param {string} accountId - 账号 ID
         * @returns {Promise<Object>} 删除结果
         * @throws {Error} 请求失败时抛出错误
         */
        deleteAccountConfig: async function(accountId) {
            return await this._request(`${apiBase}/message-notifications/account/${accountId}`, {
                method: 'DELETE'
            });
        }
    },

    /**
     * 卡券管理 API
     * @namespace API.cards
     */
    cards: {
        /**
         * 获取卡券列表
         * @returns {Promise<Array>} 卡券列表
         * @throws {Error} 请求失败时抛出错误
         */
        list: async function() {
            return await fetchJSON(`${apiBase}/cards`);
        },

        /**
         * 获取卡券详情
         * @param {string} cardId - 卡券 ID
         * @returns {Promise<Object>} 卡券详情
         * @throws {Error} 请求失败时抛出错误
         */
        get: async function(cardId) {
            return await fetchJSON(`${apiBase}/cards/${cardId}`);
        },

        /**
         * 创建卡券
         * @param {Object} cardData - 卡券数据
         * @returns {Promise<Object>} 创建的卡券
         * @throws {Error} 请求失败时抛出错误
         */
        create: async function(cardData) {
            return await this._request(`${apiBase}/cards`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(cardData)
            });
        },

        /**
         * 更新卡券
         * @param {string} cardId - 卡券 ID
         * @param {Object} cardData - 更新的数据
         * @returns {Promise<Object>} 更新结果
         * @throws {Error} 请求失败时抛出错误
         */
        update: async function(cardId, cardData) {
            return await this._request(`${apiBase}/cards/${cardId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(cardData)
            });
        },

        /**
         * 更新卡券图片
         * @param {string} cardId - 卡券 ID
         * @param {FormData} formData - 包含图片的 FormData
         * @returns {Promise<Object>} 更新结果
         * @throws {Error} 请求失败时抛出错误
         */
        updateWithImage: async function(cardId, formData) {
            return await this._request(`${apiBase}/cards/${cardId}/image`, {
                method: 'PUT',
                body: formData
            });
        },

        /**
         * 删除卡券
         * @param {string} cardId - 卡券 ID
         * @returns {Promise<Object>} 删除结果
         * @throws {Error} 请求失败时抛出错误
         */
        delete: async function(cardId) {
            return await this._request(`${apiBase}/cards/${cardId}`, {
                method: 'DELETE'
            });
        },

        /**
         * 上传卡券图片
         * @param {FormData} formData - 包含图片的 FormData
         * @returns {Promise<Object>} 上传结果
         * @throws {Error} 请求失败时抛出错误
         */
        uploadImage: async function(formData) {
            return await this._request(`${apiBase}/upload-image`, {
                method: 'POST',
                body: formData
            });
        }
    },

    /**
     * 系统设置 API
     * @namespace API.system
     */
    system: {
        /**
         * 获取系统设置
         * @returns {Promise<Object>} 系统设置
         * @throws {Error} 请求失败时抛出错误
         */
        getSettings: async function() {
            return await fetchJSON(`${apiBase}/user-settings`);
        },

        /**
         * 更新系统设置
         * @param {Object} settings - 设置内容
         * @returns {Promise<Object>} 更新结果
         * @throws {Error} 请求失败时抛出错误
         */
        updateSettings: async function(settings) {
            return await this._request(`${apiBase}/user-settings/theme_color`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
        },

        /**
         * 修改管理员密码
         * @param {string} currentPassword - 当前密码
         * @param {string} newPassword - 新密码
         * @returns {Promise<Object>} 修改结果
         * @throws {Error} 请求失败时抛出错误
         */
        changePassword: async function(currentPassword, newPassword) {
            return await this._request(`${apiBase}/change-admin-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    current_password: currentPassword,
                    new_password: newPassword
                })
            });
        },

        /**
         * 获取日志
         * @param {number} [lines=100] - 日志行数
         * @returns {Promise<string>} 日志内容
         * @throws {Error} 请求失败时抛出错误
         */
        getLogs: async function(lines = 100) {
            return await fetchJSON(`${apiBase}/logs?lines=${lines}`);
        },

        /**
         * 清除日志
         * @returns {Promise<Object>} 操作结果
         * @throws {Error} 请求失败时抛出错误
         */
        clearLogs: async function() {
            return await this._request(`${apiBase}/logs/clear`, { method: 'POST' });
        },

        /**
         * 获取日志统计
         * @returns {Promise<Object>} 日志统计信息
         * @throws {Error} 请求失败时抛出错误
         */
        getLogStats: async function() {
            return await fetchJSON(`${apiBase}/logs/stats`);
        },

        /**
         * 重新加载缓存
         * @returns {Promise<Object>} 操作结果
         * @throws {Error} 请求失败时抛出错误
         */
        reloadCache: async function() {
            return await this._request(`${apiBase}/system/reload-cache`, { method: 'POST' });
        }
    },

    /**
     * 备份管理 API
     * @namespace API.backup
     */
    backup: {
        /**
         * 下载备份
         * @returns {Promise<Object>} 备份文件信息
         * @throws {Error} 请求失败时抛出错误
         */
        download: async function() {
            return await this._request(`${apiBase}/admin/backup/download`);
        },

        /**
         * 上传备份
         * @param {FormData} formData - 包含备份文件的 FormData
         * @returns {Promise<Object>} 上传结果
         * @throws {Error} 请求失败时抛出错误
         */
        upload: async function(formData) {
            return await this._request(`${apiBase}/admin/backup/upload`, {
                method: 'POST',
                body: formData
            });
        },

        /**
         * 导出备份信息
         * @returns {Promise<Object>} 导出信息
         * @throws {Error} 请求失败时抛出错误
         */
        export: async function() {
            return await fetchJSON(`${apiBase}/backup/export`);
        },

        /**
         * 导入备份
         * @param {FormData} formData - 包含备份文件的 FormData
         * @returns {Promise<Object>} 导入结果
         * @throws {Error} 请求失败时抛出错误
         */
        import: async function(formData) {
            return await this._request(`${apiBase}/backup/import`, {
                method: 'POST',
                body: formData
            });
        }
    },

    /**
     * 二维码登录 API
     * @namespace API.qrLogin
     */
    qrLogin: {
        /**
         * 生成二维码
         * @returns {Promise<Object>} 二维码信息
         * @throws {Error} 请求失败时抛出错误
         */
        generate: async function() {
            return await this._request(`${apiBase}/qr-login/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
        },

        /**
         * 检查二维码扫描状态
         * @param {string} sessionId - 会话 ID
         * @returns {Promise<Object>} 状态信息
         * @throws {Error} 请求失败时抛出错误
         */
        checkStatus: async function(sessionId) {
            return await this._request(`${apiBase}/qr-login/check/${sessionId}`);
        },

        /**
         * 重新检查二维码状态
         * @param {string} sessionId - 会话 ID
         * @returns {Promise<Object>} 状态信息
         * @throws {Error} 请求失败时抛出错误
         */
        recheck: async function(sessionId) {
            return await this._request(`${apiBase}/qr-login/recheck/${sessionId}`, { method: 'POST' });
        }
    },

    /**
     * 认证 API
     * @namespace API.auth
     */
    auth: {
        /**
         * 登出
         * @returns {Promise<Object>} 登出结果
         * @throws {Error} 请求失败时抛出错误
         */
        logout: async function() {
            return await this._request('/logout', { method: 'POST' });
        },

        /**
         * 验证认证状态
         * @returns {Promise<Object>} 验证结果
         * @throws {Error} 请求失败时抛出错误
         */
        verify: async function() {
            return await this._request('/verify');
        }
    }
};

window._fetchJSON = fetchJSON;
window.fetchJSON = fetchJSON;
window._showToast = showToast;
window.showToast = showToast;
window._toggleLoading = toggleLoading;
window.toggleLoading = toggleLoading;
window._handleApiError = handleApiError;
window.handleApiError = handleApiError;

const exportedAPI = window.API;
export { exportedAPI as API, fetchJSON, showToast, toggleLoading, handleApiError };