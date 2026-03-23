// ============================================
// 闲鱼自动回复系统 - 主入口文件
// 模块化重构版本
// ============================================

// ========== 导入所有模块 ==========
import * as Utils from './modules/utils.js';
import * as API from './modules/api.js';
import * as Auth from './modules/auth.js';
import * as Dashboard from './modules/dashboard.js';
import * as Keywords from './modules/keywords.js';
import * as Cookies from './modules/cookies.js';
import * as Cards from './modules/cards.js';
import * as Notifications from './modules/notifications.js';
import * as Items from './modules/items.js';
import * as Delivery from './modules/delivery.js';
import * as AI from './modules/ai.js';
import * as System from './modules/system.js';

// ========== 全局配置 ==========
const DEBUG_MODE = false;
window.DEBUG_MODE = DEBUG_MODE;

// ========== 提前暴露全局函数（解决模块加载顺序问题） ==========
// 这些函数需要在 DOM 加载前就可用，因为 HTML 中的 onclick 会直接调用
window.showSection = function(sectionName) {
    if (DEBUG_MODE) console.log('切换到页面:', sectionName);
    document.querySelectorAll('.content-section').forEach(section => section.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
    const targetSection = document.getElementById(sectionName + '-section');
    if (targetSection) targetSection.classList.add('active');
    const menuLink = document.querySelector(`.nav-link[onclick="showSection('${sectionName}')"]`);
    if (menuLink) menuLink.classList.add('active');
};

window.toggleSidebar = function() {
    document.getElementById('sidebar').classList.toggle('collapsed');
};

// ========== 页面导航 ==========
function showSection(sectionName) {
    if (DEBUG_MODE) console.log('切换到页面:', sectionName);
    document.querySelectorAll('.content-section').forEach(section => section.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
    const targetSection = document.getElementById(sectionName + '-section');
    if (targetSection) targetSection.classList.add('active');
    const menuLink = document.querySelector(`.nav-link[onclick="showSection('${sectionName}')"]`);
    if (menuLink) menuLink.classList.add('active');
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('collapsed');
}

// ========== 初始化 ==========
document.addEventListener('DOMContentLoaded', async function() {
    // 检查认证 - authToken 是一个带 getter 的对象，需要调用 .value 获取实际值
    if (!Utils.authToken.value) {
        window.location.href = '/login.html';
        return;
    }

    // 菜单点击事件
    document.querySelectorAll('.nav-link[onclick]').forEach(link => {
        link.addEventListener('click', function(e) {
            const match = this.getAttribute('onclick').match(/showSection\('(\w+)'\)/);
            if (match) { e.preventDefault(); showSection(match[1]); }
        });
    });

    // 移动端菜单按钮
    const menuToggle = document.getElementById('menuToggle');
    if (menuToggle) menuToggle.addEventListener('click', toggleSidebar);

    // 登出按钮
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) logoutBtn.addEventListener('click', Auth.logout);

    // 加载仪表盘
    try {
        await Dashboard.loadDashboard();
    } catch (error) {
        console.error('加载仪表盘失败:', error);
    }

    // 显示第一个页面
    showSection('dashboard');
});

// ========== 创建命名空间并导出到全局 (使 onclick 等事件处理器可以调用) ==========

/**
 * 创建统一的 App 命名空间，避免全局命名空间污染
 * 所有模块都组织在 window.App 命名空间下
 * 同时保持向后兼容，导出旧的引用到 window 对象
 */
window.App = {
    // 核心模块
    Utils: Utils,
    API: API,
    Auth: Auth,
    
    // 功能模块
    Dashboard: Dashboard,
    Keywords: Keywords,
    Cookies: Cookies,
    Cards: Cards,
    Notifications: Notifications,
    Items: Items,
    Delivery: Delivery,
    AI: AI,
    System: System,
    
    // 全局配置
    DEBUG_MODE: DEBUG_MODE
};

// ========== 向后兼容：导出常用函数到全局 ==========
// 注意：新代码应使用 window.App.Utils.xxx 等命名空间方式访问

// Utils 模块 - 常用工具函数
window.escapeHtml = Utils.escapeHtml;
window.formatDateTime = Utils.formatDateTime;
window.clearKeywordCache = Utils.clearKeywordCache;

// API 模块 - 核心请求函数
window.fetchJSON = API.fetchJSON;
window.toggleLoading = API.toggleLoading;
window.showToast = API.showToast;
window.loadCookies = Cookies.loadCookies;
window.addCookie = API.addCookie;
window.updateCookie = API.updateCookie;
window.deleteCookie = API.deleteCookie;
window.toggleAccountStatus = API.toggleAccountStatus;
window.toggleAutoConfirm = API.toggleAutoConfirm;
window.getKeywords = API.getKeywords;
window.getKeywordsWithItemId = API.getKeywordsWithItemId;
window.saveKeywords = API.saveKeywords;
window.deleteKeyword = API.deleteKeyword;
window.addImageKeyword = API.addImageKeyword;
window.exportKeywordsAPI = API.exportKeywords;
window.importKeywords = API.importKeywords;
window.getAllItems = API.getAllItems;
window.getItemsByCookie = API.getItemsByCookie;
window.getItem = API.getItem;
window.updateItem = API.updateItem;
window.deleteItem = API.deleteItem;
window.batchDeleteItems = API.batchDeleteItems;
window.toggleItemMultiSpec = API.toggleItemMultiSpec;
window.getItemsByPage = API.getItemsByPage;
window.getAllItemsFromAccount = API.getAllItemsFromAccount;
window.getDefaultReplies = API.getDefaultReplies;
window.getDefaultReply = API.getDefaultReply;
window.updateDefaultReply = API.updateDefaultReply;
window.getAIReplyConfig = API.getAIReplyConfig;
window.updateAIReplyConfig = API.updateAIReplyConfig;
window.testAIReplyAPI = API.testAIReply;
window.getDeliveryRules = API.getDeliveryRules;
window.saveDeliveryRuleAPI = API.saveDeliveryRule;
window.updateDeliveryRuleAPI = API.updateDeliveryRule;
window.deleteDeliveryRule = API.deleteDeliveryRule;
window.getNotificationChannels = API.getNotificationChannels;
window.saveNotificationChannelAPI = API.saveNotificationChannel;
window.updateNotificationChannelAPI = API.updateNotificationChannel;
window.deleteNotificationChannel = API.deleteNotificationChannel;
window.getMessageNotifications = API.getMessageNotifications;
window.saveAccountNotificationAPI = API.saveAccountNotification;
window.deleteAccountNotification = API.deleteAccountNotification;
window.getSystemSettings = API.getSystemSettings;
window.updateSystemSettings = API.updateSystemSettings;
window.reloadSystemCacheAPI = API.reloadSystemCache;
window.getSystemLogs = API.getSystemLogs;
window.clearSystemLogs = API.clearSystemLogs;
window.getBackupFiles = API.getBackupFiles;
window.createBackup = API.createBackup;
window.downloadBackup = API.downloadBackup;
window.uploadBackup = API.uploadBackup;
window.deleteBackup = API.deleteBackup;
window.restoreBackup = API.restoreBackup;

// Auth 模块
window.checkAuth = Auth.checkAuth;
window.logout = Auth.logout;
window.showQRCodeLogin = Auth.showQRCodeLogin;
window.toggleManualInput = Auth.toggleManualInput;
window.refreshQRCode = Auth.refreshQRCode;
window.generateQRCode = Auth.generateQRCode;
window.showQRCodeLoading = Auth.showQRCodeLoading;
window.showQRCodeImage = Auth.showQRCodeImage;
window.showQRCodeError = Auth.showQRCodeError;
window.startQRCodeCheck = Auth.startQRCodeCheck;
window.checkQRCodeStatus = Auth.checkQRCodeStatus;
window.showVerificationRequired = Auth.showVerificationRequired;
window.continueAfterVerification = Auth.continueAfterVerification;
window.handleQRCodeSuccess = Auth.handleQRCodeSuccess;
window.clearQRCodeCheck = Auth.clearQRCodeCheck;
window.refreshCaptcha = Auth.refreshCaptcha;
window.sendVerificationCode = Auth.sendVerificationCode;
window.fillDefaultCredentials = Auth.fillDefaultCredentials;
window.login = Auth.login;
window.verifyAuth = Auth.verifyAuth;

// Dashboard 模块
window.loadDashboard = Dashboard.loadDashboard;
window.updateDashboardStats = Dashboard.updateDashboardStats;
window.updateDashboardAccountsList = Dashboard.updateDashboardAccountsList;
window.refreshLogs = Dashboard.refreshLogs;
window.displayLogs = Dashboard.displayLogs;
window.formatLogTimestamp = Dashboard.formatLogTimestamp;
window.updateLogStats = Dashboard.updateLogStats;
window.clearLogsDisplay = Dashboard.clearLogsDisplay;
window.toggleAutoRefresh = Dashboard.toggleAutoRefresh;
window.clearLogsServer = Dashboard.clearLogsServer;
window.showLogStats = Dashboard.showLogStats;

// Keywords 模块
window.getAccountKeywordCount = Keywords.getAccountKeywordCount;
window.refreshAccountList = Keywords.refreshAccountList;
window.loadAccountKeywords = Keywords.loadAccountKeywords;
window.loadItemsList = Keywords.loadItemsList;
window.updateAccountBadge = Keywords.updateAccountBadge;
window.showAddKeywordForm = Keywords.showAddKeywordForm;
window.addKeyword = Keywords.addKeyword;
window.renderKeywordsList = Keywords.renderKeywordsList;
window.focusKeywordInput = Keywords.focusKeywordInput;
window.editKeyword = Keywords.editKeyword;
window.showCancelEditButton = Keywords.showCancelEditButton;
window.cancelEdit = Keywords.cancelEdit;
window.deleteKeyword = Keywords.deleteKeyword;
window.validateImageDimensions = Keywords.validateImageDimensions;
window.showImagePreview = Keywords.showImagePreview;
window.hideImagePreview = Keywords.hideImagePreview;
window.showImageModal = Keywords.showImageModal;
window.initImageKeywordEventListeners = Keywords.initImageKeywordEventListeners;
window.showAddImageKeywordModal = Keywords.showAddImageKeywordModal;
window.loadItemsListForImageKeyword = Keywords.loadItemsListForImageKeyword;
window.addImageKeyword = Keywords.addImageKeyword;
window.editImageKeyword = Keywords.editImageKeyword;
window.exportKeywords = Keywords.exportKeywords;
window.showImportModal = Keywords.showImportModal;
window.importKeywords = Keywords.importKeywords;
window.toggleMultiReplyField = Keywords.toggleMultiReplyField;
window.toggleAdvancedConditions = Keywords.toggleAdvancedConditions;
window.collectAdvancedConditions = Keywords.collectAdvancedConditions;
window.clearAdvancedConditions = Keywords.clearAdvancedConditions;
window.fillAdvancedConditions = Keywords.fillAdvancedConditions;

// Cookies 模块
window.copyCookie = Cookies.copyCookie;
window.delCookie = Cookies.delCookie;
window.editCookieInline = Cookies.editCookieInline;
window.saveCookieInline = Cookies.saveCookieInline;
window.cancelCookieEdit = Cookies.cancelCookieEdit;
window.updateAccountRowStatus = Cookies.updateAccountRowStatus;
window.updateAutoConfirmRowStatus = Cookies.updateAutoConfirmRowStatus;
window.goToAutoReply = Cookies.goToAutoReply;

// Cards 模块
window.loadCards = Cards.loadCards;
window.renderCardsList = Cards.renderCardsList;
window.updateCardsStats = Cards.updateCardsStats;
window.showAddCardModal = Cards.showAddCardModal;
window.toggleCardTypeFields = Cards.toggleCardTypeFields;
window.toggleMultiSpecFields = Cards.toggleMultiSpecFields;
window.initCardImageFileSelector = Cards.initCardImageFileSelector;
window.validateCardImageDimensions = Cards.validateCardImageDimensions;
window.showCardImagePreview = Cards.showCardImagePreview;
window.hideCardImagePreview = Cards.hideCardImagePreview;
window.initEditCardImageFileSelector = Cards.initEditCardImageFileSelector;
window.validateEditCardImageDimensions = Cards.validateEditCardImageDimensions;
window.showEditCardImagePreview = Cards.showEditCardImagePreview;
window.hideEditCardImagePreview = Cards.hideEditCardImagePreview;
window.toggleEditMultiSpecFields = Cards.toggleEditMultiSpecFields;
window.clearAddCardForm = Cards.clearAddCardForm;
window.saveCard = Cards.saveCard;
window.editCard = Cards.editCard;
window.toggleEditCardTypeFields = Cards.toggleEditCardTypeFields;
window.updateCard = Cards.updateCard;
window.updateCardWithImage = Cards.updateCardWithImage;
window.testCard = Cards.testCard;
window.deleteCard = Cards.deleteCard;

// Notifications 模块
window.channelTypeConfigs = Notifications.channelTypeConfigs;
window.showAddChannelModal = Notifications.showAddChannelModal;
window.generateFieldHtml = Notifications.generateFieldHtml;
window.saveNotificationChannel = Notifications.saveNotificationChannel;
window.loadNotificationChannels = Notifications.loadNotificationChannels;
window.renderNotificationChannels = Notifications.renderNotificationChannels;
window.deleteNotificationChannel = Notifications.deleteNotificationChannel;
window.editNotificationChannel = Notifications.editNotificationChannel;
window.updateNotificationChannel = Notifications.updateNotificationChannel;
window.loadMessageNotifications = Notifications.loadMessageNotifications;
window.renderMessageNotifications = Notifications.renderMessageNotifications;
window.configAccountNotification = Notifications.configAccountNotification;
window.deleteAccountNotification = Notifications.deleteAccountNotification;
window.saveAccountNotification = Notifications.saveAccountNotification;

// Items 模块
window.refreshItemsData = Items.refreshItemsData;
window.loadCookieFilter = Items.loadCookieFilter;
window.loadAllItems = Items.loadAllItems;
window.loadItemsByCookie = Items.loadItemsByCookie;
window.displayItems = Items.displayItems;
window.refreshItems = Items.refreshItems;
window.getAllItemsFromAccountAll = Items.getAllItemsFromAccountAll;
window.editItem = Items.editItem;
window.saveItemDetail = Items.saveItemDetail;
window.toggleSelectAll = Items.toggleSelectAll;
window.updateSelectAllState = Items.updateSelectAllState;
window.updateBatchDeleteButton = Items.updateBatchDeleteButton;

// Delivery 模块
window.renderDeliveryRulesList = Delivery.renderDeliveryRulesList;
window.updateDeliveryStats = Delivery.updateDeliveryStats;
window.showAddDeliveryRuleModal = Delivery.showAddDeliveryRuleModal;
window.loadCardsForSelect = Delivery.loadCardsForSelect;
window.editDeliveryRule = Delivery.editDeliveryRule;
window.loadCardsForEditSelect = Delivery.loadCardsForEditSelect;
window.testDeliveryRule = Delivery.testDeliveryRule;

// AI 模块
window.toggleAIReplySettings = AI.toggleAIReplySettings;
window.loadAIReplySettings = AI.loadAIReplySettings;
window.toggleCustomModelInput = AI.toggleCustomModelInput;
window.saveAIReplyConfig = AI.saveAIReplyConfig;
window.toggleReplyContentVisibility = AI.toggleReplyContentVisibility;
window.openDefaultReplyManager = AI.openDefaultReplyManager;
window.renderDefaultRepliesTable = AI.renderDefaultRepliesTable;
window.editDefaultReply = AI.editDefaultReply;
window.saveDefaultReply = AI.saveDefaultReply;
window.configAIReply = AI.configAIReply;

// System 模块
window.loadTableData = System.loadTableData;
window.refreshTableData = System.refreshTableData;
window.getTableName = System.getTableName;
window.confirmDelete = System.confirmDelete;
window.confirmDeleteAll = System.confirmDeleteAll;
window.downloadDatabaseBackup = System.downloadDatabaseBackup;
window.uploadDatabaseBackup = System.uploadDatabaseBackup;
window.reloadSystemCache = System.reloadSystemCache;
window.toggleMaintenanceMode = System.toggleMaintenanceMode;
window.getSystemStatus = System.getSystemStatus;
window.showSystemInfo = System.showSystemInfo;
