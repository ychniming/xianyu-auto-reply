// 工具模块 - 全局变量和共享函数
// 这些变量和函数被多个模块共享

// 全局变量
export const apiBase = location.origin;
// authToken 每次都从 localStorage 读取最新值
export const authToken = {
    get value() {
        return localStorage.getItem('auth_token');
    },
    toString() {
        return this.value || '';
    }
};
export let keywordsData = {};
export let currentCookieId = '';
export let editCookieId = '';
export let dashboardData = {
    accounts: [],
    totalKeywords: 0
};

// AI 配置
export let aiSettings = {
    enabled: false,
    model: 'gpt-4',
    apiKey: '',
    customPrompt: '',
    temperature: 0.7,
    maxTokens: 500,
    intentClassification: true,
    autoDelivery: true
};

// 账号关键词缓存
export let accountKeywordCache = {};
export let cacheTimestamp = 0;
export const CACHE_DURATION = 30000; // 30秒缓存

// 日志相关
window.autoRefreshInterval = null;
window.allLogs = [];
window.filteredLogs = [];

// 更新 authToken
export function updateAuthToken(token) {
    if (token === null || token === undefined) {
        localStorage.removeItem('auth_token');
    } else {
        localStorage.setItem('auth_token', token);
    }
}

// HTML转义函数
export function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 格式化日期时间
export function formatDateTime(dateString) {
    if (!dateString) return '未知';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}

// 清除关键词缓存
export function clearKeywordCache() {
    accountKeywordCache = {};
    cacheTimestamp = 0;
}
