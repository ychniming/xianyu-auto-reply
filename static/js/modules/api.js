// API 模块 - 统一 API 命名空间
import { authToken, apiBase } from './utils.js';

const MAX_RETRIES = 3;
const BASE_DELAY = 1000;
const MAX_DELAY = 10000;

let abortController = null;

function isRetryableError(error, response = null) {
    if (error.name === 'TypeError') return true;
    if (error.name === 'AbortError') return true;
    if (response && response.status >= 500 && response.status < 600) return true;
    if (response && response.status === 429) return true;
    return false;
}

function calculateDelay(retryCount) {
    const delay = BASE_DELAY * Math.pow(2, retryCount);
    const jitter = delay * 0.2 * (Math.random() - 0.5);
    return Math.min(delay + jitter, MAX_DELAY);
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

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

function toggleLoading(show) {
    document.getElementById('loading').classList.toggle('d-none', !show);
}

function handleApiError(err) {
    console.error(err);
    showToast(err.message || '操作失败', 'danger');
    toggleLoading(false);
}

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

window.API = {
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

    _getAuthHeader: function() {
        const token = authToken.value;
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    },

    cancelPending: function() {
        if (abortController) {
            abortController.abort();
            abortController = null;
        }
    },

    cookies: {
        list: async function() {
            return await fetchJSON(`${apiBase}/cookies/details`);
        },

        create: async function(id, value) {
            return await fetchJSON(`${apiBase}/cookies`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id, value })
            });
        },

        update: async function(id, data) {
            return await fetchJSON(`${apiBase}/cookies/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        },

        delete: async function(id) {
            return await fetchJSON(`${apiBase}/cookies/${id}`, { method: 'DELETE' });
        },

        getDetails: async function(cookieId) {
            return await fetchJSON(`${apiBase}/cookies/details/${cookieId}`);
        },

        toggleStatus: async function(accountId, enabled) {
            return await this._request(`${apiBase}/cookies/${accountId}/status`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled })
            });
        },

        toggleAutoConfirm: async function(accountId, enabled) {
            return await this._request(`${apiBase}/cookies/${accountId}/auto-confirm`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ auto_confirm: enabled })
            });
        }
    },

    keywords: {
        list: async function(cookieId) {
            return await fetchJSON(`${apiBase}/keywords/${cookieId}`);
        },

        listWithItemId: async function(cookieId) {
            return await fetchJSON(`${apiBase}/keywords-with-item-id/${cookieId}`);
        },

        create: async function(cookieId, keyword, reply, itemId) {
            return await this._request(`${apiBase}/keywords-with-item-id/${cookieId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ keywords: [{ keyword, reply, item_id: itemId }] })
            });
        },

        update: async function(keywordId, data) {
            return await this._request(`${apiBase}/keywords/${keywordId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        },

        delete: async function(cookieId, keywordId) {
            return await this._request(`${apiBase}/keywords/${cookieId}/${keywordId}`, {
                method: 'DELETE'
            });
        },

        addImage: async function(cookieId, formData) {
            return await this._request(`${apiBase}/keywords/${cookieId}/image`, {
                method: 'POST',
                body: formData
            });
        },

        export: async function(cookieId) {
            return await this._request(`${apiBase}/keywords-export/${cookieId}`);
        },

        import: async function(cookieId, formData) {
            return await this._request(`${apiBase}/keywords-import/${cookieId}`, {
                method: 'POST',
                body: formData
            });
        }
    },

    items: {
        list: async function() {
            return await fetchJSON(`${apiBase}/items`);
        },

        get: async function(cookieId, itemId) {
            return await fetchJSON(`${apiBase}/items/${encodeURIComponent(cookieId)}/${encodeURIComponent(itemId)}`);
        },

        getByCookie: async function(cookieId) {
            return await fetchJSON(`${apiBase}/items/cookie/${encodeURIComponent(cookieId)}`);
        },

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

        getAllFromAccount: async function(cookieId) {
            return await this._request(`${apiBase}/items/get-all-from-account`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cookie_id: cookieId })
            });
        },

        update: async function(cookieId, itemId, itemDetail) {
            return await this._request(`${apiBase}/items/${encodeURIComponent(cookieId)}/${encodeURIComponent(itemId)}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ item_detail: itemDetail })
            });
        },

        delete: async function(cookieId, itemId) {
            return await this._request(`${apiBase}/items/${encodeURIComponent(cookieId)}/${encodeURIComponent(itemId)}`, {
                method: 'DELETE'
            });
        },

        batchDelete: async function(items) {
            return await this._request(`${apiBase}/items/batch`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ items })
            });
        },

        toggleMultiSpec: async function(cookieId, itemId, isMultiSpec) {
            return await this._request(`${apiBase}/items/${encodeURIComponent(cookieId)}/${encodeURIComponent(itemId)}/multi-spec`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_multi_spec: isMultiSpec })
            });
        }
    },

    dashboard: {
        getStats: async function() {
            return await fetchJSON(`${apiBase}/dashboard/stats`);
        },

        getAccounts: async function() {
            return await fetchJSON(`${apiBase}/cookies/details`);
        }
    },

    ai: {
        getSettings: async function(accountId) {
            return await fetchJSON(`${apiBase}/ai-reply-settings/${accountId}`);
        },

        saveSettings: async function(accountId, settings) {
            return await this._request(`${apiBase}/ai-reply-settings/${accountId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
        },

        saveConfig: async function(config) {
            return await this._request(`${apiBase}/ai-reply-config`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
        },

        test: async function(accountId, testData) {
            return await this._request(`${apiBase}/ai-reply-test/${accountId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(testData)
            });
        }
    },

    delivery: {
        list: async function() {
            return await fetchJSON(`${apiBase}/delivery-rules`);
        },

        get: async function(ruleId) {
            return await fetchJSON(`${apiBase}/delivery-rules/${ruleId}`);
        },

        create: async function(data) {
            return await this._request(`${apiBase}/delivery-rules`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        },

        update: async function(ruleId, data) {
            return await this._request(`${apiBase}/delivery-rules/${ruleId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        },

        delete: async function(ruleId) {
            return await this._request(`${apiBase}/delivery-rules/${ruleId}`, {
                method: 'DELETE'
            });
        }
    },

    defaultReplies: {
        list: async function() {
            return await fetchJSON(`${apiBase}/default-replies`);
        },

        get: async function(accountId) {
            return await fetchJSON(`${apiBase}/default-replies/${accountId}`);
        },

        update: async function(accountId, data) {
            return await this._request(`${apiBase}/default-replies/${accountId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        },

        save: async function(type, content) {
            return await this._request(`${apiBase}/default-replies/${type}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content })
            });
        }
    },

    notifications: {
        getChannels: async function() {
            return await fetchJSON(`${apiBase}/notification-channels`);
        },

        addChannel: async function(data) {
            return await this._request(`${apiBase}/notification-channels`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        },

        updateChannel: async function(channelId, data) {
            return await this._request(`${apiBase}/notification-channels/${channelId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        },

        deleteChannel: async function(channelId) {
            return await this._request(`${apiBase}/notification-channels/${channelId}`, {
                method: 'DELETE'
            });
        },

        getMessageConfig: async function() {
            return await fetchJSON(`${apiBase}/message-notifications`);
        },

        getAccountConfig: async function(accountId) {
            return await fetchJSON(`${apiBase}/message-notifications/${accountId}`);
        },

        saveAccountConfig: async function(accountId, data) {
            return await this._request(`${apiBase}/message-notifications/${accountId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        },

        deleteAccountConfig: async function(accountId) {
            return await this._request(`${apiBase}/message-notifications/account/${accountId}`, {
                method: 'DELETE'
            });
        }
    },

    cards: {
        list: async function() {
            return await fetchJSON(`${apiBase}/cards`);
        },

        get: async function(cardId) {
            return await fetchJSON(`${apiBase}/cards/${cardId}`);
        },

        create: async function(cardData) {
            return await this._request(`${apiBase}/cards`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(cardData)
            });
        },

        update: async function(cardId, cardData) {
            return await this._request(`${apiBase}/cards/${cardId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(cardData)
            });
        },

        updateWithImage: async function(cardId, formData) {
            return await this._request(`${apiBase}/cards/${cardId}/image`, {
                method: 'PUT',
                body: formData
            });
        },

        delete: async function(cardId) {
            return await this._request(`${apiBase}/cards/${cardId}`, {
                method: 'DELETE'
            });
        },

        uploadImage: async function(formData) {
            return await this._request(`${apiBase}/upload-image`, {
                method: 'POST',
                body: formData
            });
        }
    },

    system: {
        getSettings: async function() {
            return await fetchJSON(`${apiBase}/user-settings`);
        },

        updateSettings: async function(settings) {
            return await this._request(`${apiBase}/user-settings/theme_color`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
        },

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

        getLogs: async function(lines = 100) {
            return await fetchJSON(`${apiBase}/logs?lines=${lines}`);
        },

        clearLogs: async function() {
            return await this._request(`${apiBase}/logs/clear`, { method: 'POST' });
        },

        getLogStats: async function() {
            return await fetchJSON(`${apiBase}/logs/stats`);
        },

        reloadCache: async function() {
            return await this._request(`${apiBase}/system/reload-cache`, { method: 'POST' });
        }
    },

    backup: {
        download: async function() {
            return await this._request(`${apiBase}/admin/backup/download`);
        },

        upload: async function(formData) {
            return await this._request(`${apiBase}/admin/backup/upload`, {
                method: 'POST',
                body: formData
            });
        },

        export: async function() {
            return await fetchJSON(`${apiBase}/backup/export`);
        },

        import: async function(formData) {
            return await this._request(`${apiBase}/backup/import`, {
                method: 'POST',
                body: formData
            });
        }
    },

    qrLogin: {
        generate: async function() {
            return await this._request(`${apiBase}/qr-login/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
        },

        checkStatus: async function(sessionId) {
            return await this._request(`${apiBase}/qr-login/check/${sessionId}`);
        },

        recheck: async function(sessionId) {
            return await this._request(`${apiBase}/qr-login/recheck/${sessionId}`, { method: 'POST' });
        }
    },

    auth: {
        logout: async function() {
            return await this._request('/logout', { method: 'POST' });
        },

        verify: async function() {
            return await this._request('/verify');
        }
    }
};

window.fetchJSON = fetchJSON;
window.showToast = showToast;
window.toggleLoading = toggleLoading;
window.handleApiError = handleApiError;
