// API 模块 - 所有 API 调用函数
import { authToken, apiBase } from './utils.js';

// ==================== 重试配置 ====================
const MAX_RETRIES = 3;           // 最大重试次数
const BASE_DELAY = 1000;         // 基础延迟时间（毫秒）
const MAX_DELAY = 10000;         // 最大延迟时间（毫秒）

/**
 * 判断错误是否可重试
 * 网络错误、超时、5xx 服务器错误可以重试
 * @param {Error} error - 错误对象
 * @param {Response} response - fetch Response 对象（可选）
 * @returns {boolean} 是否可重试
 */
function isRetryableError(error, response = null) {
    // 网络错误（TypeError 通常表示网络问题）
    if (error.name === 'TypeError') {
        return true;
    }
    
    // 超时错误
    if (error.name === 'AbortError') {
        return true;
    }
    
    // 服务器错误（5xx）
    if (response && response.status >= 500 && response.status < 600) {
        return true;
    }
    
    // 429 Too Many Requests
    if (response && response.status === 429) {
        return true;
    }
    
    return false;
}

/**
 * 计算重试延迟时间（指数退避）
 * @param {number} retryCount - 当前重试次数（从0开始）
 * @returns {number} 延迟时间（毫秒）
 */
function calculateDelay(retryCount) {
    // 指数退避：delay = baseDelay * 2^retryCount
    const delay = BASE_DELAY * Math.pow(2, retryCount);
    // 添加随机抖动（±20%）避免请求同步
    const jitter = delay * 0.2 * (Math.random() - 0.5);
    return Math.min(delay + jitter, MAX_DELAY);
}

/**
 * 延迟执行
 * @param {number} ms - 延迟毫秒数
 * @returns {Promise}
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 带重试机制的 fetch 请求
 * @param {string} url - 请求URL
 * @param {Object} options - fetch选项
 * @param {number} retries - 剩余重试次数
 * @returns {Promise<Response>} fetch Response
 */
async function fetchWithRetry(url, options = {}, retries = MAX_RETRIES) {
    let lastError = null;
    let lastResponse = null;
    
    for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
        try {
            const response = await fetch(url, options);
            
            // 检查是否需要重试（服务器错误）
            if (!response.ok && isRetryableError(null, response) && attempt < MAX_RETRIES) {
                const delay = calculateDelay(attempt);
                console.warn(`[API] 请求失败 (HTTP ${response.status})，${delay}ms 后重试 (${attempt + 1}/${MAX_RETRIES})`);
                await sleep(delay);
                continue;
            }
            
            return response;
        } catch (error) {
            lastError = error;
            
            // 检查是否需要重试（网络错误）
            if (isRetryableError(error) && attempt < MAX_RETRIES) {
                const delay = calculateDelay(attempt);
                console.warn(`[API] 请求失败 (${error.message})，${delay}ms 后重试 (${attempt + 1}/${MAX_RETRIES})`);
                await sleep(delay);
                continue;
            }
            
            throw error;
        }
    }
    
    // 所有重试都失败
    throw lastError || new Error('请求失败，已达最大重试次数');
}

// API 请求包装函数（带重试机制）
export async function fetchJSON(url, opts = {}) {
    toggleLoading(true);
    try {
        // 添加认证头
        const token = authToken.value;
        if (token) {
            opts.headers = opts.headers || {};
            opts.headers['Authorization'] = `Bearer ${token}`;
        }

        const res = await fetchWithRetry(url, opts);
        if (res.status === 401) {
            // 未授权，跳转到登录页面
            localStorage.removeItem('auth_token');
            window.location.href = '/';
            return;
        }
        if (!res.ok) {
            let errorMessage = `HTTP ${res.status}`;
            try {
                const errorText = await res.text();
                if (errorText) {
                    // 尝试解析JSON错误信息
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
        // 统一响应格式：{code, message, data}
        // 如果响应包含 data 属性，返回 data；否则返回整个响应
        return jsonResponse.data !== undefined ? jsonResponse.data : jsonResponse;
    } catch (err) {
        handleApiError(err);
        throw err;
    }
}

// 错误处理
export async function handleApiError(err) {
    console.error(err);
    showToast(err.message || '操作失败', 'danger');
    toggleLoading(false);
}

// 显示/隐藏加载动画
export function toggleLoading(show) {
    document.getElementById('loading').classList.toggle('d-none', !show);
}

// 高阶函数：自动处理loading的API调用
// 使用方式：const data = await withLoading(fetchJSON(url, opts))
export function withLoading(handler, options = {}) {
    const { showLoading = true, showError = true, errorMessage = null } = options;
    
    return async function(...args) {
        if (showLoading) {
            toggleLoading(true);
        }
        
        try {
            const result = await handler.apply(this, args);
            return result;
        } catch (err) {
            if (showError) {
                handleApiError(err);
            } else if (errorMessage) {
                showToast(errorMessage, 'danger');
            }
            throw err;
        } finally {
            if (showLoading) {
                toggleLoading(false);
            }
        }
    };
}

// 高阶函数：创建带loading的API方法
// 使用方式：const loadCookies = createApiMethod(loadCookiesAPI)
//          const data = await loadCookies()
export function createApiMethod(apiFunc, options = {}) {
    return withLoading(apiFunc, options);
}

// 显示提示消息
export function showToast(message, type = 'success') {
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
    
    // 使用textContent安全设置消息内容，防止XSS
    toast.querySelector('.toast-body').textContent = message;

    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
    bsToast.show();

    // 自动移除
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// ==================== Cookie/账号 API ====================

// 加载Cookie列表
export async function loadCookiesAPI() {
    return await fetchJSON(apiBase + '/cookies/details');
}

// 添加Cookie
export async function addCookieAPI(id, value) {
    return await fetchJSON(apiBase + '/cookies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, value })
    });
}

// 更新Cookie
export async function updateCookieAPI(id, value) {
    return await fetchJSON(apiBase + `/cookies/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, value })
    });
}

// 删除Cookie
export async function deleteCookieAPI(id) {
    return await fetchJSON(apiBase + `/cookies/${id}`, { method: 'DELETE' });
}

// 切换账号状态
export async function toggleAccountStatusAPI(accountId, enabled) {
    return await fetch(`${apiBase}/cookies/${accountId}/status`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken.value}`
        },
        body: JSON.stringify({ enabled: enabled })
    });
}

// 切换自动确认发货状态
export async function toggleAutoConfirmAPI(accountId, enabled) {
    return await fetch(`${apiBase}/cookies/${accountId}/auto-confirm`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken.value}`
        },
        body: JSON.stringify({ auto_confirm: enabled })
    });
}

// ==================== 关键词 API ====================

// 获取账号关键词
export async function getKeywordsAPI(accountId) {
    return await fetchJSON(`${apiBase}/keywords/${accountId}`);
}

// 获取账号关键词（带item_id）
export async function getKeywordsWithItemIdAPI(accountId) {
    return await fetchJSON(`${apiBase}/keywords-with-item-id/${accountId}`);
}

// 保存关键词
export async function saveKeywordsAPI(accountId, keywords) {
    return await fetch(`${apiBase}/keywords-with-item-id/${accountId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ keywords })
    });
}

// 删除关键词
export async function deleteKeywordAPI(cookieId, index) {
    return await fetch(`${apiBase}/keywords/${cookieId}/${index}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    });
}

// 添加图片关键词
export async function addImageKeywordAPI(cookieId, formData) {
    return await fetch(`${apiBase}/keywords/${cookieId}/image`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${authToken}`
        },
        body: formData
    });
}

// 导出关键词
export async function exportKeywordsAPI(cookieId) {
    return await fetch(`${apiBase}/keywords-export/${cookieId}`, {
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    });
}

// 导入关键词
export async function importKeywordsAPI(cookieId, formData) {
    return await fetch(`${apiBase}/keywords-import/${cookieId}`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${authToken}`
        },
        body: formData
    });
}

// ==================== 商品 API ====================

// 获取所有商品
export async function getAllItemsAPI() {
    return await fetchJSON(`${apiBase}/items`);
}

// 按账号获取商品
export async function getItemsByCookieAPI(cookieId) {
    return await fetchJSON(`${apiBase}/items/cookie/${encodeURIComponent(cookieId)}`);
}

// 获取单个商品
export async function getItemAPI(cookieId, itemId) {
    return await fetchJSON(`${apiBase}/items/${encodeURIComponent(cookieId)}/${encodeURIComponent(itemId)}`);
}

// 更新商品详情
export async function updateItemAPI(cookieId, itemId, itemDetail) {
    return await fetch(`${apiBase}/items/${encodeURIComponent(cookieId)}/${encodeURIComponent(itemId)}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ item_detail: itemDetail })
    });
}

// 删除商品
export async function deleteItemAPI(cookieId, itemId) {
    return await fetch(`${apiBase}/items/${encodeURIComponent(cookieId)}/${encodeURIComponent(itemId)}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    });
}

// 批量删除商品
export async function batchDeleteItemsAPI(items) {
    return await fetch(`${apiBase}/items/batch`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ items })
    });
}

// 切换商品多规格状态
export async function toggleItemMultiSpecAPI(cookieId, itemId, isMultiSpec) {
    return await fetch(`${apiBase}/items/${encodeURIComponent(cookieId)}/${encodeURIComponent(itemId)}/multi-spec`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ is_multi_spec: isMultiSpec })
    });
}

// 按页获取商品
export async function getItemsByPageAPI(cookieId, pageNumber, pageSize = 20) {
    return await fetch(`${apiBase}/items/get-by-page`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
            cookie_id: cookieId,
            page_number: pageNumber,
            page_size: pageSize
        })
    });
}

// 获取账号所有商品
export async function getAllItemsFromAccountAPI(cookieId) {
    return await fetch(`${apiBase}/items/get-all-from-account`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ cookie_id: cookieId })
    });
}

// ==================== 默认回复 API ====================

// 获取所有默认回复
export async function getDefaultRepliesAPI() {
    return await fetchJSON(`${apiBase}/default-replies`);
}

// 保存默认回复
export async function saveDefaultReplyAPI(type, content) {
    return await fetch(`${apiBase}/default-replies/${type}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ content })
    });
}

// 获取账号默认回复
export async function getDefaultReplyAPI(accountId) {
    return await fetchJSON(`${apiBase}/default-replies/${accountId}`);
}

// 更新默认回复
export async function updateDefaultReplyAPI(accountId, data) {
    return await fetch(`${apiBase}/default-replies/${accountId}`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
}

// ==================== AI 回复 API ====================

// 获取AI回复设置
export async function getAIReplySettingsAPI(accountId) {
    return await fetchJSON(`${apiBase}/ai-reply-settings/${accountId}`);
}

// 保存AI回复设置
export async function saveAIReplySettingsAPI(accountId, settings) {
    return await fetch(`${apiBase}/ai-reply-settings/${accountId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify(settings)
    });
}

// AI回复配置保存（全局配置版本）
export async function saveAIReplyConfigAPI(config) {
    return await fetch(`${apiBase}/ai-reply-config`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify(config)
    });
}

// 测试AI回复
export async function testAIReplyAPI(accountId, testData) {
    return await fetch(`${apiBase}/ai-reply-test/${accountId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify(testData)
    });
}

// ==================== 通知渠道 API ====================

// 获取通知渠道
export async function getNotificationChannelsAPI() {
    return await fetchJSON(`${apiBase}/notification-channels`);
}

// 添加通知渠道
export async function addNotificationChannelAPI(data) {
    return await fetch(`${apiBase}/notification-channels`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
}

// 更新通知渠道
export async function updateNotificationChannelAPI(channelId, data) {
    return await fetch(`${apiBase}/notification-channels/${channelId}`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
}

// 删除通知渠道
export async function deleteNotificationChannelAPI(channelId) {
    return await fetch(`${apiBase}/notification-channels/${channelId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    });
}

// ==================== 消息通知 API ====================

// 获取消息通知配置
export async function getMessageNotificationsAPI() {
    return await fetchJSON(`${apiBase}/message-notifications`);
}

// 获取账号消息通知配置
export async function getAccountNotificationAPI(accountId) {
    return await fetchJSON(`${apiBase}/message-notifications/${accountId}`);
}

// 保存账号消息通知配置
export async function saveAccountNotificationAPI(accountId, data) {
    return await fetch(`${apiBase}/message-notifications/${accountId}`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
}

// 删除账号消息通知配置
export async function deleteAccountNotificationAPI(accountId) {
    return await fetch(`${apiBase}/message-notifications/account/${accountId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    });
}

// ==================== 卡券 API ====================

// 获取卡券列表
export async function getCardsAPI() {
    return await fetchJSON(`${apiBase}/cards`);
}

// 获取单个卡券
export async function getCardAPI(cardId) {
    return await fetchJSON(`${apiBase}/cards/${cardId}`);
}

// 添加卡券
export async function addCardAPI(cardData) {
    return await fetch(`${apiBase}/cards`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(cardData)
    });
}

// 更新卡券
export async function updateCardAPI(cardId, cardData) {
    return await fetch(`${apiBase}/cards/${cardId}`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(cardData)
    });
}

// 更新带图片的卡券
export async function updateCardWithImageAPI(cardId, formData) {
    return await fetch(`${apiBase}/cards/${cardId}/image`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${authToken}`
        },
        body: formData
    });
}

// 删除卡券
export async function deleteCardAPI(cardId) {
    return await fetch(`${apiBase}/cards/${cardId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    });
}

// 上传图片
export async function uploadImageAPI(formData) {
    return await fetch(`${apiBase}/upload-image`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${authToken}`
        },
        body: formData
    });
}

// ==================== 发货规则 API ====================

// 获取发货规则
export async function getDeliveryRulesAPI() {
    return await fetchJSON(`${apiBase}/delivery-rules`);
}

// 获取单个发货规则
export async function getDeliveryRuleAPI(ruleId) {
    return await fetchJSON(`${apiBase}/delivery-rules/${ruleId}`);
}

// 添加发货规则
export async function addDeliveryRuleAPI(ruleData) {
    return await fetch(`${apiBase}/delivery-rules`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(ruleData)
    });
}

// 更新发货规则
export async function updateDeliveryRuleAPI(ruleId, ruleData) {
    return await fetch(`${apiBase}/delivery-rules/${ruleId}`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(ruleData)
    });
}

// 删除发货规则
export async function deleteDeliveryRuleAPI(ruleId) {
    return await fetch(`${apiBase}/delivery-rules/${ruleId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    });
}

// ==================== 系统 API ====================

// 获取用户设置
export async function getUserSettingsAPI() {
    return await fetchJSON(`${apiBase}/user-settings`);
}

// 更新用户设置
export async function updateUserSettingsAPI(settings) {
    return await fetch(`${apiBase}/user-settings/theme_color`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
    });
}

// 修改密码
export async function changePasswordAPI(currentPassword, newPassword) {
    return await fetch(`${apiBase}/change-admin-password`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            current_password: currentPassword,
            new_password: newPassword
        })
    });
}

// 获取日志
export async function getLogsAPI(lines = 100) {
    return await fetchJSON(`${apiBase}/logs?lines=${lines}`);
}

// 清空日志
export async function clearLogsAPI() {
    return await fetch(`${apiBase}/logs/clear`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    });
}

// 获取日志统计
export async function getLogStatsAPI() {
    return await fetchJSON(`${apiBase}/logs/stats`);
}

// 刷新系统缓存
export async function reloadSystemCacheAPI() {
    return await fetch(`${apiBase}/system/reload-cache`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    });
}

// ==================== 备份 API ====================

// 下载数据库备份
export async function downloadDatabaseBackupAPI() {
    return await fetch(`${apiBase}/admin/backup/download`, {
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    });
}

// 上传数据库备份
export async function uploadDatabaseBackupAPI(formData) {
    return await fetch(`${apiBase}/admin/backup/upload`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${authToken}`
        },
        body: formData
    });
}

// 导出备份
export async function exportBackupAPI() {
    return await fetchJSON(`${apiBase}/backup/export`);
}

// 导入备份
export async function importBackupAPI(formData) {
    return await fetch(`${apiBase}/backup/import`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${authToken}`
        },
        body: formData
    });
}

// ==================== 二维码登录 API ====================

// 生成二维码
export async function generateQRCodeAPI() {
    return await fetch(`${apiBase}/qr-login/generate`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
        }
    });
}

// 检查二维码状态
export async function checkQRCodeStatusAPI(sessionId) {
    return await fetch(`${apiBase}/qr-login/check/${sessionId}`, {
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    });
}

// 重新检查二维码状态
export async function recheckQRCodeAPI(sessionId) {
    return await fetch(`${apiBase}/qr-login/recheck/${sessionId}`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    });
}

// 登出
export async function logoutAPI() {
    return await fetch('/logout', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    });
}

// 验证认证
export async function verifyAuthAPI() {
    return await fetch('/verify', {
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    });
}
