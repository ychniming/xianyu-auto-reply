// 工具模块 - 全局变量和共享函数
// 这些变量和函数被多个模块共享

window.App = window.App || {};

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
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
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

// 加载商品列表（公共函数）
export async function loadItemsList(accountId, selectElementId, placeholder = '选择商品或留空表示通用关键词') {
    try {
        const response = await fetch(`${apiBase}/items/${accountId}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            const items = data.items || [];

            const selectElement = document.getElementById(selectElementId);
            if (selectElement) {
                selectElement.innerHTML = `<option value="">${placeholder}</option>`;

                items.forEach(item => {
                    const option = document.createElement('option');
                    option.value = item.item_id;
                    option.textContent = `${item.item_id} - ${item.item_title}`;
                    selectElement.appendChild(option);
                });
            }
        } else {
            console.warn('加载商品列表失败:', response.status);
        }
    } catch (error) {
        console.error('加载商品列表时发生错误:', error);
    }
}

// App 命名空间 - 核心函数
window.App.showSection = function(sectionName) {
    const DEBUG_MODE = window.DEBUG_MODE || false;
    if (DEBUG_MODE) console.log('切换到页面:', sectionName);
    document.querySelectorAll('.content-section').forEach(section => section.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
    const targetSection = document.getElementById(sectionName + '-section');
    if (targetSection) targetSection.classList.add('active');
    const menuLink = document.querySelector(`.nav-link[onclick="showSection('${sectionName}')"]`);
    if (menuLink) menuLink.classList.add('active');
};

window.App.toggleSidebar = function() {
    document.getElementById('sidebar').classList.toggle('collapsed');
};

window.App.showToast = function(message, type) {
    type = type || 'info';
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = 'position:fixed;top:20px;right:20px;z-index:9999;padding:12px 20px;background:#333;color:#fff;border-radius:4px;box-shadow:0 2px 8px rgba(0,0,0,0.2);';
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
};

window.App.showLoading = function() {
    if (document.getElementById('loadingOverlay')) return;
    const overlay = document.createElement('div');
    overlay.id = 'loadingOverlay';
    overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;justify-content:center;align-items:center;z-index:9998;';
    overlay.innerHTML = '<div style="color:#fff;font-size:18px;">加载中...</div>';
    document.body.appendChild(overlay);
};

window.App.hideLoading = function() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.remove();
};

export class ModalManager {
    static _container = null;

    static _getContainer() {
        if (!ModalManager._container) {
            ModalManager._container = document.createElement('div');
            ModalManager._container.id = 'dynamic-modals';
            document.body.appendChild(ModalManager._container);
        }
        return ModalManager._container;
    }

    static show(modalId, options = {}) {
        const modalEl = document.getElementById(modalId);
        if (modalEl) {
            const modal = new bootstrap.Modal(modalEl, options);
            modal.show();
            return modal;
        }
        console.warn(`Modal ${modalId} not found`);
        return null;
    }

    static hide(modalId) {
        const modalEl = document.getElementById(modalId);
        if (modalEl) {
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
        }
    }

    static remove(modalId) {
        const modalEl = document.getElementById(modalId);
        if (modalEl) {
            modalEl.remove();
        }
    }

    static create(modalId, html, options = {}) {
        const existing = document.getElementById(modalId);
        if (existing) existing.remove();

        const container = ModalManager._getContainer();
        const temp = document.createElement('div');
        temp.innerHTML = html;
        const modalEl = temp.firstElementChild;
        modalEl.id = modalId;
        container.appendChild(modalEl);

        if (options.onShow) {
            modalEl.addEventListener('show.bs.modal', options.onShow);
        }
        if (options.onHide) {
            modalEl.addEventListener('hidden.bs.modal', options.onHide);
        }

        return modalEl;
    }
}

window.ModalManager = ModalManager;

ModalManager.qrCodeLogin = {
    template: `
    <div class="modal fade" id="qrCodeLoginModal" tabindex="-1">
      <div class="modal-dialog modal-dialog-centered modal-lg">
        <div class="modal-content">
          <div class="modal-header bg-success text-white">
            <h5 class="modal-title">
              <i class="bi bi-qr-code me-2"></i>扫码登录闲鱼账号
            </h5>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body text-center py-4">
            <div class="row mb-4">
              <div class="col-12">
                <div class="d-flex justify-content-center align-items-center">
                  <div class="step-item me-3">
                    <div class="step-number bg-success text-white rounded-circle d-inline-flex align-items-center justify-content-center" style="width: 30px; height: 30px;">1</div>
                    <small class="d-block mt-1">打开闲鱼APP</small>
                  </div>
                  <i class="bi bi-arrow-right text-muted me-3"></i>
                  <div class="step-item me-3">
                    <div class="step-number bg-success text-white rounded-circle d-inline-flex align-items-center justify-content-center" style="width: 30px; height: 30px;">2</div>
                    <small class="d-block mt-1">扫描二维码</small>
                  </div>
                  <i class="bi bi-arrow-right text-muted me-3"></i>
                  <div class="step-item">
                    <div class="step-number bg-success text-white rounded-circle d-inline-flex align-items-center justify-content-center" style="width: 30px; height: 30px;">3</div>
                    <small class="d-block mt-1">自动添加账号</small>
                  </div>
                </div>
              </div>
            </div>
            <div id="qrCodeContainer">
              <div class="spinner-border text-success mb-3" role="status" style="width: 3rem; height: 3rem;">
                <span class="visually-hidden">生成二维码中...</span>
              </div>
              <p class="text-muted fs-5 mb-2">正在生成二维码...</p>
              <div class="alert alert-warning border-0 bg-light-warning d-inline-block qr-loading-tip">
                <i class="bi bi-clock me-2 text-warning"></i>
                <small class="text-warning fw-bold">二维码生成较慢，请耐心等待</small>
              </div>
            </div>
            <div id="qrCodeImage" style="display: none;">
              <div class="qr-code-wrapper p-3 bg-light rounded-3 d-inline-block mb-3">
                <img id="qrCodeImg" src="" alt="登录二维码" class="img-fluid" style="max-width: 280px;">
              </div>
              <h6 class="text-success mb-2">
                <i class="bi bi-phone me-2"></i>请使用闲鱼APP扫描二维码
              </h6>
              <div class="alert alert-info border-0 bg-light">
                <i class="bi bi-info-circle me-2 text-info"></i>
                <small>扫码后请等待页面提示，系统会自动获取并保存您的账号信息</small>
              </div>
            </div>
            <div id="qrCodeStatus" class="mt-3">
              <div class="d-flex align-items-center justify-content-center">
                <div class="spinner-border spinner-border-sm text-success me-2" role="status" style="display: none;" id="statusSpinner">
                  <span class="visually-hidden">检查中...</span>
                </div>
                <span id="statusText" class="text-muted">等待扫码...</span>
              </div>
            </div>
          </div>
          <div class="modal-footer bg-light">
            <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">
              <i class="bi bi-x-circle me-1"></i>关闭
            </button>
            <button type="button" class="btn btn-success" onclick="refreshQRCode()" id="refreshQRBtn">
              <i class="bi bi-arrow-clockwise me-1"></i>重新生成二维码
            </button>
          </div>
        </div>
      </div>
    </div>
    `,

    show: function(onSuccess, onError) {
        const container = ModalManager._getContainer();
        let modalEl = document.getElementById('qrCodeLoginModal');

        if (!modalEl) {
            const temp = document.createElement('div');
            temp.innerHTML = ModalManager.qrCodeLogin.template;
            modalEl = temp.firstElementChild;
            container.appendChild(modalEl);
        }

        const modalInstance = ModalManager.show('qrCodeLoginModal');

        const containerEl = document.getElementById('qrCodeContainer');
        const imageEl = document.getElementById('qrCodeImage');
        const statusText = document.getElementById('statusText');

        if (containerEl) containerEl.style.display = 'block';
        if (imageEl) imageEl.style.display = 'none';
        if (statusText) statusText.textContent = '等待扫码...';

        if (typeof refreshQRCode === 'function') {
            refreshQRCode();
        }

        return modalInstance;
    }
};
