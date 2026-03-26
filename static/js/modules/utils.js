// 工具模块 - 全局变量和共享函数
import { Store } from './store.js';

window.App = window.App || {};

/**
 * API 基础 URL
 * @type {string}
 */
export const apiBase = location.origin;

/**
 * 认证令牌访问器
 * @type {Object}
 * @property {Function} value - 获取存储的认证令牌
 * @property {Function} toString - 转换为字符串
 */
export const authToken = {
    get value() {
        return localStorage.getItem('auth_token');
    },
    toString() {
        return this.value || '';
    }
};

/**
 * 关键词存储
 * @type {Store}
 */
export const keywordsStore = Store.create('keywords', { data: {}, loading: false });

/**
 * Cookie 存储
 * @type {Store}
 */
export const cookiesStore = Store.create('cookies', {
    currentId: '',
    editId: ''
});

/**
 * 仪表盘存储
 * @type {Store}
 */
export const dashboardStore = Store.create('dashboard', {
    accounts: [],
    totalKeywords: 0
});

/**
 * AI 存储
 * @type {Store}
 */
export const aiStore = Store.create('ai', {
    enabled: false,
    model: 'gpt-4',
    apiKey: '',
    customPrompt: '',
    temperature: 0.7,
    maxTokens: 500,
    intentClassification: true,
    autoDelivery: true
});

/**
 * 账号关键词缓存
 * @type {Store}
 */
export const accountKeywordCache = Store.create('accountKeywordCache', {
    cache: {},
    timestamp: 0
});

/**
 * 缓存有效期（毫秒）
 * @type {number}
 */
export const CACHE_DURATION = 30000;

/**
 * 自动刷新间隔 ID
 * @type {number|null}
 */
window.autoRefreshInterval = null;

/**
 * 所有日志列表
 * @type {Array}
 */
window.allLogs = [];

/**
 * 过滤后的日志列表
 * @type {Array}
 */
window.filteredLogs = [];

/**
 * 更新认证令牌
 * @param {string|null} token - 新的令牌，为 null 时删除现有令牌
 */
export function updateAuthToken(token) {
    if (token === null || token === undefined) {
        localStorage.removeItem('auth_token');
    } else {
        localStorage.setItem('auth_token', token);
    }
}

/**
 * HTML 转义函数，防止 XSS 攻击
 * @param {string|null|undefined} text - 要转义的文本
 * @returns {string} 转义后的文本
 */
export function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

/**
 * 格式化日期时间
 * @param {string|null} dateString - ISO 日期字符串
 * @returns {string} 格式化后的日期时间字符串，格式：YYYY/MM/DD HH:mm:ss
 */
export function formatDateTime(dateString) {
    if (!dateString) return '未知';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}

/**
 * 清除关键词缓存
 */
export function clearKeywordCache() {
    accountKeywordCache.setState({ cache: {}, timestamp: 0 });
}

/**
 * 加载商品列表到指定选择框
 * @param {string} accountId - 账号 ID
 * @param {string} selectElementId - 选择框元素 ID
 * @param {string} [placeholder='选择商品或留空表示通用关键词'] - 默认提示文本
 * @returns {Promise<void>}
 */
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

/**
 * App 命名空间 - 核心函数
 * @namespace App
 */
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

/**
 * 切换侧边栏折叠状态
 */
window.App.toggleSidebar = function() {
    document.getElementById('sidebar').classList.toggle('collapsed');
};

/**
 * 显示 Toast 通知
 * @param {string} message - 消息内容
 * @param {'success'|'danger'|'warning'|'info'} [type='info'] - 消息类型
 */
window.App.showToast = function(message, type) {
    type = type || 'info';
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = 'position:fixed;top:20px;right:20px;z-index:9999;padding:12px 20px;background:#333;color:#fff;border-radius:4px;box-shadow:0 2px 8px rgba(0,0,0,0.2);';
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
};

/**
 * 显示加载遮罩
 */
window.App.showLoading = function() {
    if (document.getElementById('loadingOverlay')) return;
    const overlay = document.createElement('div');
    overlay.id = 'loadingOverlay';
    overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;justify-content:center;align-items:center;z-index:9998;';
    overlay.innerHTML = '<div style="color:#fff;font-size:18px;">加载中...</div>';
    document.body.appendChild(overlay);
};

/**
 * 隐藏加载遮罩
 */
window.App.hideLoading = function() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.remove();
};

/**
 * 模态框管理器
 */
export class ModalManager {
    /**
     * 模态框容器
     * @type {HTMLElement|null}
     */
    static _container = null;

    /**
     * 获取或创建模态框容器
     * @returns {HTMLElement}
     */
    static _getContainer() {
        if (!ModalManager._container) {
            ModalManager._container = document.createElement('div');
            ModalManager._container.id = 'dynamic-modals';
            document.body.appendChild(ModalManager._container);
        }
        return ModalManager._container;
    }

    /**
     * 显示已存在的模态框
     * @param {string} modalId - 模态框 ID
     * @param {Object} [options={}] - Bootstrap 模态框选项
     * @returns {bootstrap.Modal|null}
     */
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

    /**
     * 隐藏模态框
     * @param {string} modalId - 模态框 ID
     */
    static hide(modalId) {
        const modalEl = document.getElementById(modalId);
        if (modalEl) {
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
        }
    }

    /**
     * 移除模态框
     * @param {string} modalId - 模态框 ID
     */
    static remove(modalId) {
        const modalEl = document.getElementById(modalId);
        if (modalEl) {
            modalEl.remove();
        }
    }

    /**
     * 创建并显示模态框
     * @param {string} modalId - 模态框 ID
     * @param {string} html - HTML 内容
     * @param {Object} [options={}] - 选项
     * @param {Function} [options.onShow] - 显示回调
     * @param {Function} [options.onHide] - 隐藏回调
     * @returns {HTMLElement} 创建的模态框元素
     */
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

/**
 * 二维码登录模态框
 */
ModalManager.qrCodeLogin = {
    /**
     * 模态框 HTML 模板
     * @type {string}
     */
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

    /**
     * 显示二维码登录模态框
     * @param {Function} [onSuccess] - 成功回调
     * @param {Function} [onError] - 错误回调
     * @returns {bootstrap.Modal}
     */
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

/**
 * 添加卡券模态框
 */
ModalManager.addCardModal = {
    /**
     * 模态框 HTML 模板
     * @type {string}
     */
    template: `
<div class="modal fade" id="addCardModal" tabindex="-1">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">
          <i class="bi bi-credit-card me-2"></i>
          添加卡券
        </h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <form id="addCardForm" onsubmit="event.preventDefault(); saveCard(); return false;">
          <div class="mb-3">
            <label class="form-label">卡券名称 <span class="text-danger">*</span></label>
            <input type="text" class="form-control" id="cardName" placeholder="例如：游戏点卡、会员卡等" required>
          </div>
          <div class="mb-3">
            <label class="form-label">卡券类型 <span class="text-danger">*</span></label>
            <select class="form-select" id="cardType" onchange="toggleCardTypeFields()" required>
              <option value="">请选择类型</option>
              <option value="api">API接口</option>
              <option value="text">固定文字</option>
              <option value="data">批量数据</option>
              <option value="image">图片</option>
            </select>
          </div>

          <div id="apiFields" class="card mb-3" style="display: none;">
            <div class="card-header">
              <h6 class="mb-0">API配置</h6>
            </div>
            <div class="card-body">
              <div class="mb-3">
                <label class="form-label">API地址</label>
                <input type="url" class="form-control" id="apiUrl" placeholder="https://api.example.com/get-card">
              </div>
              <div class="row">
                <div class="col-md-6">
                  <label class="form-label">请求方法</label>
                  <select class="form-select" id="apiMethod">
                    <option value="GET">GET</option>
                    <option value="POST">POST</option>
                  </select>
                </div>
                <div class="col-md-6">
                  <label class="form-label">超时时间(秒)</label>
                  <input type="number" class="form-control" id="apiTimeout" value="10" min="1" max="60">
                </div>
              </div>
              <div class="mb-3">
                <label class="form-label">请求头 (JSON格式)</label>
                <textarea class="form-control" id="apiHeaders" rows="3" placeholder='{"Authorization": "Bearer token", "Content-Type": "application/json"}'></textarea>
              </div>
              <div class="mb-3">
                <label class="form-label">请求参数 (JSON格式)</label>
                <textarea class="form-control" id="apiParams" rows="3" placeholder='{"type": "card", "count": 1}'></textarea>
              </div>
            </div>
          </div>

          <div id="textFields" class="card mb-3" style="display: none;">
            <div class="card-header">
              <h6 class="mb-0">固定文字配置</h6>
            </div>
            <div class="card-body">
              <div class="mb-3">
                <label class="form-label">固定文字内容</label>
                <textarea class="form-control" id="textContent" rows="5" placeholder="请输入要发送的固定文字内容..."></textarea>
              </div>
            </div>
          </div>

          <div id="dataFields" class="card mb-3" style="display: none;">
            <div class="card-header">
              <h6 class="mb-0">批量数据配置</h6>
            </div>
            <div class="card-body">
              <div class="mb-3">
                <label class="form-label">数据内容 (一行一个)</label>
                <textarea class="form-control" id="dataContent" rows="10" placeholder="请输入数据，每行一个：&#10;卡号1:密码1&#10;卡号2:密码2&#10;或者&#10;兑换码1&#10;兑换码2"></textarea>
                <small class="form-text text-muted">支持格式：卡号:密码 或 单独的兑换码</small>
              </div>
            </div>
          </div>

          <div id="imageFields" class="card mb-3" style="display: none;">
            <div class="card-header">
              <h6 class="mb-0">图片配置</h6>
            </div>
            <div class="card-body">
              <div class="mb-3">
                <label class="form-label">选择图片 <span class="text-danger">*</span></label>
                <input type="file" class="form-control" id="cardImageFile" accept="image/*">
                <small class="form-text text-muted">
                  <i class="bi bi-info-circle me-1"></i>
                  支持JPG、PNG、GIF格式，最大5MB，建议尺寸不超过4096x4096像素
                </small>
              </div>

              <div id="cardImagePreview" class="mb-3" style="display: none;">
                <label class="form-label">图片预览</label>
                <div class="preview-container">
                  <img id="cardPreviewImg" src="" alt="预览图片"
                       style="max-width: 100%; max-height: 300px; border-radius: 8px; border: 1px solid #ddd;">
                </div>
              </div>
            </div>
          </div>

          <div class="mb-3">
            <label class="form-label">延时发货时间</label>
            <div class="input-group">
              <input type="number" class="form-control" id="cardDelaySeconds" value="0" min="0" max="3600" placeholder="0">
              <span class="input-group-text">秒</span>
            </div>
            <small class="form-text text-muted">
              <i class="bi bi-clock me-1"></i>
              设置自动发货的延时时间，0表示立即发货，最大3600秒(1小时)
            </small>
          </div>

          <div class="mb-3">
            <label class="form-label">备注信息</label>
            <textarea class="form-control" id="cardDescription" rows="3" placeholder="可选的备注信息，支持变量替换：&#10;{DELIVERY_CONTENT} - 发货内容&#10;例如：您的卡券信息：{DELIVERY_CONTENT}，请妥善保管。"></textarea>
            <small class="form-text text-muted">
              <i class="bi bi-info-circle me-1"></i>
              备注内容会与发货内容一起发送。使用 <code>{DELIVERY_CONTENT}</code> 变量可以在备注中插入实际的发货内容。
            </small>
          </div>

          <div class="mb-3">
            <div class="form-check form-switch">
              <input class="form-check-input" type="checkbox" id="isMultiSpec" onchange="toggleMultiSpecFields()">
              <label class="form-check-label" for="isMultiSpec">
                <strong>多规格卡券</strong>
              </label>
            </div>
            <div class="form-text">开启后可以为同一商品的不同规格创建不同的卡券</div>
          </div>

          <div id="multiSpecFields" style="display: none;">
            <div class="row">
              <div class="col-md-6">
                <div class="mb-3">
                  <label class="form-label">规格名称 <span class="text-danger">*</span></label>
                  <input type="text" class="form-control" id="specName" placeholder="例如：套餐类型、颜色、尺寸">
                  <div class="form-text">规格的名称，如套餐类型、颜色等</div>
                </div>
              </div>
              <div class="col-md-6">
                <div class="mb-3">
                  <label class="form-label">规格值 <span class="text-danger">*</span></label>
                  <input type="text" class="form-control" id="specValue" placeholder="例如：30天、红色、XL">
                  <div class="form-text">具体的规格值，如30天、红色等</div>
                </div>
              </div>
            </div>
            <div class="alert alert-info">
              <i class="bi bi-info-circle"></i>
              <strong>多规格说明：</strong>
              <ul class="mb-0 mt-2">
                <li>同一卡券名称可以创建多个不同规格的卡券</li>
                <li>卡券名称+规格名称+规格值必须唯一</li>
                <li>自动发货时会优先匹配精确规格，找不到时使用普通卡券兜底</li>
              </ul>
            </div>
          </div>
        </form>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
        <button type="button" class="btn btn-primary" onclick="saveCard()">保存卡券</button>
      </div>
    </div>
  </div>
</div>
`,

    /**
     * 显示添加卡券模态框
     * @param {Function} [onSuccess] - 成功回调
     * @returns {bootstrap.Modal}
     */
    show: function(onSuccess) {
        const container = ModalManager._getContainer();
        let modalEl = document.getElementById('addCardModal');

        if (!modalEl) {
            const temp = document.createElement('div');
            temp.innerHTML = ModalManager.addCardModal.template;
            modalEl = temp.firstElementChild;
            container.appendChild(modalEl);
        }

        modalEl.querySelector('form').reset();
        toggleCardTypeFields();
        toggleMultiSpecFields();

        const modalInstance = ModalManager.show('addCardModal');

        if (onSuccess) {
            modalEl.addEventListener('hidden.bs.modal', function handler(e) {
                modalEl.removeEventListener('hidden.bs.modal', handler);
                onSuccess();
            });
        }

        return modalInstance;
    }
};

/**
 * 编辑卡券模态框
 */
ModalManager.editCardModal = {
    /**
     * 模态框 HTML 模板
     * @type {string}
     */
    template: `
<div class="modal fade" id="editCardModal" tabindex="-1">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">
          <i class="bi bi-pencil me-2"></i>
          编辑卡券
        </h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <form id="editCardForm">
          <input type="hidden" id="editCardId">
          <div class="mb-3">
            <label class="form-label">卡券名称 <span class="text-danger">*</span></label>
            <input type="text" class="form-control" id="editCardName" required>
          </div>
          <div class="mb-3">
            <label class="form-label">卡券类型 <span class="text-danger">*</span></label>
            <select class="form-select" id="editCardType" onchange="toggleEditCardTypeFields()" required>
              <option value="api">API接口</option>
              <option value="text">固定文字</option>
              <option value="data">批量数据</option>
              <option value="image">图片</option>
            </select>
          </div>

          <div id="editApiFields" class="card mb-3" style="display: none;">
            <div class="card-header">
              <h6 class="mb-0">API配置</h6>
            </div>
            <div class="card-body">
              <div class="mb-3">
                <label class="form-label">API地址</label>
                <input type="url" class="form-control" id="editApiUrl">
              </div>
              <div class="row">
                <div class="col-md-6">
                  <label class="form-label">请求方法</label>
                  <select class="form-select" id="editApiMethod">
                    <option value="GET">GET</option>
                    <option value="POST">POST</option>
                  </select>
                </div>
                <div class="col-md-6">
                  <label class="form-label">超时时间(秒)</label>
                  <input type="number" class="form-control" id="editApiTimeout" value="10" min="1" max="60">
                </div>
              </div>
              <div class="mb-3">
                <label class="form-label">请求头 (JSON格式)</label>
                <textarea class="form-control" id="editApiHeaders" rows="3"></textarea>
              </div>
              <div class="mb-3">
                <label class="form-label">请求参数 (JSON格式)</label>
                <textarea class="form-control" id="editApiParams" rows="3"></textarea>
              </div>
            </div>
          </div>

          <div id="editTextFields" class="card mb-3" style="display: none;">
            <div class="card-header">
              <h6 class="mb-0">固定文字配置</h6>
            </div>
            <div class="card-body">
              <div class="mb-3">
                <label class="form-label">固定文字内容</label>
                <textarea class="form-control" id="editTextContent" rows="5"></textarea>
              </div>
            </div>
          </div>

          <div id="editDataFields" class="card mb-3" style="display: none;">
            <div class="card-header">
              <h6 class="mb-0">批量数据配置</h6>
            </div>
            <div class="card-body">
              <div class="mb-3">
                <label class="form-label">数据内容 (一行一个)</label>
                <textarea class="form-control" id="editDataContent" rows="10"></textarea>
                <small class="form-text text-muted">支持格式：卡号:密码 或 单独的兑换码</small>
              </div>
            </div>
          </div>

          <div id="editImageFields" class="card mb-3" style="display: none;">
            <div class="card-header">
              <h6 class="mb-0">图片配置</h6>
            </div>
            <div class="card-body">
              <div class="mb-3">
                <label class="form-label">当前图片</label>
                <div id="editCurrentImagePreview" style="display: none;">
                  <img id="editCurrentImg" src="" alt="当前图片"
                       style="max-width: 100%; max-height: 200px; border-radius: 8px; border: 1px solid #ddd;">
                  <div class="mt-2">
                    <small class="text-muted">当前使用的图片</small>
                  </div>
                </div>
                <div id="editNoImageText" class="text-muted">
                  <i class="bi bi-image me-1"></i>暂无图片
                </div>
              </div>

              <div class="mb-3">
                <label class="form-label">更换图片</label>
                <input type="file" class="form-control" id="editCardImageFile" accept="image/*">
                <small class="form-text text-muted">
                  <i class="bi bi-info-circle me-1"></i>
                  支持JPG、PNG、GIF格式，最大5MB，建议尺寸不超过4096x4096像素
                </small>
              </div>

              <div id="editCardImagePreview" class="mb-3" style="display: none;">
                <label class="form-label">新图片预览</label>
                <div class="preview-container">
                  <img id="editCardPreviewImg" src="" alt="预览图片"
                       style="max-width: 100%; max-height: 300px; border-radius: 8px; border: 1px solid #ddd;">
                </div>
              </div>
            </div>
          </div>

          <div class="mb-3">
            <div class="form-check">
              <input class="form-check-input" type="checkbox" id="editCardEnabled">
              <label class="form-check-label" for="editCardEnabled">
                启用此卡券
              </label>
            </div>
          </div>

          <div class="mb-3">
            <label class="form-label">延时发货时间</label>
            <div class="input-group">
              <input type="number" class="form-control" id="editCardDelaySeconds" value="0" min="0" max="3600" placeholder="0">
              <span class="input-group-text">秒</span>
            </div>
            <small class="form-text text-muted">
              <i class="bi bi-clock me-1"></i>
              设置自动发货的延时时间，0表示立即发货，最大3600秒(1小时)
            </small>
          </div>

          <div class="mb-3">
            <label class="form-label">备注信息</label>
            <textarea class="form-control" id="editCardDescription" rows="3" placeholder="可选的备注信息，支持变量替换：&#10;{DELIVERY_CONTENT} - 发货内容&#10;例如：您的卡券信息：{DELIVERY_CONTENT}，请妥善保管。"></textarea>
            <small class="form-text text-muted">
              <i class="bi bi-info-circle me-1"></i>
              备注内容会与发货内容一起发送。使用 <code>{DELIVERY_CONTENT}</code> 变量可以在备注中插入实际的发货内容。
            </small>
          </div>

          <div class="mb-3">
            <div class="form-check form-switch">
              <input class="form-check-input" type="checkbox" id="editIsMultiSpec" onchange="toggleEditMultiSpecFields()">
              <label class="form-check-label" for="editIsMultiSpec">
                <strong>多规格卡券</strong>
              </label>
            </div>
            <div class="form-text">开启后可以为同一商品的不同规格创建不同的卡券</div>
          </div>

          <div id="editMultiSpecFields" style="display: none;">
            <div class="row">
              <div class="col-md-6">
                <div class="mb-3">
                  <label class="form-label">规格名称 <span class="text-danger">*</span></label>
                  <input type="text" class="form-control" id="editSpecName" placeholder="例如：套餐类型、颜色、尺寸">
                  <div class="form-text">规格的名称，如套餐类型、颜色等</div>
                </div>
              </div>
              <div class="col-md-6">
                <div class="mb-3">
                  <label class="form-label">规格值 <span class="text-danger">*</span></label>
                  <input type="text" class="form-control" id="editSpecValue" placeholder="例如：30天、红色、XL">
                  <div class="form-text">具体的规格值，如30天、红色等</div>
                </div>
              </div>
            </div>
            <div class="alert alert-info">
              <i class="bi bi-info-circle"></i>
              <strong>多规格说明：</strong>
              <ul class="mb-0 mt-2">
                <li>同一卡券名称可以创建多个不同规格的卡券</li>
                <li>卡券名称+规格名称+规格值必须唯一</li>
                <li>自动发货时会优先匹配精确规格，找不到时使用普通卡券兜底</li>
              </ul>
            </div>
          </div>
        </form>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
        <button type="button" class="btn btn-primary" onclick="updateCard()">保存修改</button>
      </div>
    </div>
  </div>
</div>
`,

    /**
     * 显示编辑卡券模态框
     * @param {Object} [cardData] - 卡券数据
     * @param {Function} [onSuccess] - 成功回调
     * @returns {bootstrap.Modal}
     */
    show: function(cardData, onSuccess) {
        const container = ModalManager._getContainer();
        let modalEl = document.getElementById('editCardModal');

        if (!modalEl) {
            const temp = document.createElement('div');
            temp.innerHTML = ModalManager.editCardModal.template;
            modalEl = temp.firstElementChild;
            container.appendChild(modalEl);
        }

        if (cardData) {
            document.getElementById('editCardId').value = cardData.id || '';
            document.getElementById('editCardName').value = cardData.name || '';
            document.getElementById('editCardType').value = cardData.card_type || 'text';
            document.getElementById('editCardEnabled').checked = cardData.enabled !== 0;
            document.getElementById('editCardDelaySeconds').value = cardData.delay_seconds || 0;
            document.getElementById('editCardDescription').value = cardData.description || '';
            document.getElementById('editIsMultiSpec').checked = cardData.is_multi_spec === 1;
            document.getElementById('editSpecName').value = cardData.spec_name || '';
            document.getElementById('editSpecValue').value = cardData.spec_value || '';

            if (cardData.card_type === 'api') {
                try {
                    const apiConfig = JSON.parse(cardData.api_config || '{}');
                    document.getElementById('editApiUrl').value = apiConfig.url || '';
                    document.getElementById('editApiMethod').value = apiConfig.method || 'GET';
                    document.getElementById('editApiTimeout').value = apiConfig.timeout || 10;
                    document.getElementById('editApiHeaders').value = JSON.stringify(apiConfig.headers || {}, null, 2);
                    document.getElementById('editApiParams').value = JSON.stringify(apiConfig.params || {}, null, 2);
                } catch (e) {
                    console.warn('解析API配置失败:', e);
                }
            } else if (cardData.card_type === 'text') {
                document.getElementById('editTextContent').value = cardData.text_content || '';
            } else if (cardData.card_type === 'data') {
                document.getElementById('editDataContent').value = cardData.data_content || '';
            } else if (cardData.card_type === 'image') {
                if (cardData.image_url) {
                    const imgEl = document.getElementById('editCurrentImg');
                    const previewEl = document.getElementById('editCurrentImagePreview');
                    const noImgEl = document.getElementById('editNoImageText');
                    if (imgEl) imgEl.src = cardData.image_url;
                    if (previewEl) previewEl.style.display = 'block';
                    if (noImgEl) noImgEl.style.display = 'none';
                }
            }
        }

        toggleEditCardTypeFields();
        toggleEditMultiSpecFields();

        const modalInstance = ModalManager.show('editCardModal');

        if (onSuccess) {
            modalEl.addEventListener('hidden.bs.modal', function handler(e) {
                modalEl.removeEventListener('hidden.bs.modal', handler);
                onSuccess();
            });
        }

        return modalInstance;
    }
};

/**
 * 显示添加卡券模态框
 * @deprecated 使用 ModalManager.addCardModal.show() 代替
 */
window.showAddCardModal = function() {
    ModalManager.addCardModal.show();
};

/**
 * 显示编辑卡券模态框
 * @deprecated 使用 ModalManager.editCardModal.show() 代替
 * @param {Object} cardData - 卡券数据
 */
window.showEditCardModal = function(cardData) {
    ModalManager.editCardModal.show(cardData);
};