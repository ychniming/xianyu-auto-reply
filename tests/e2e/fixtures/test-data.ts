/**
 * 测试数据配置
 * 包含测试用例中使用的所有测试数据
 */

export const TestUsers = {
  admin: {
    username: 'admin',
    password: 'admin123',
    email: 'admin@example.com'
  },
  user: {
    username: 'testuser',
    password: 'test123',
    email: 'test@example.com'
  }
};

export const TestCookies = {
  valid: {
    id: 'test_cookie_001',
    value: 'test_cookie_value_example'
  },
  invalid: {
    id: '',
    value: ''
  }
};

export const TestKeywords = {
  text: {
    keyword: '你好',
    reply: '您好，欢迎咨询！有什么可以帮助您的吗？',
    matchType: 'contains',
    priority: 50
  },
  image: {
    keyword: '图片测试',
    reply: '这是一条图片回复测试'
  },
  multiReply: {
    keyword: '多回复测试',
    replies: ['回复1', '回复2', '回复3'],
    replyMode: 'random'
  }
};

export const TestItems = {
  sample: {
    itemId: 'test_item_001',
    title: '测试商品标题',
    description: '测试商品描述内容'
  }
};

export const TestDeliveryRules = {
  card: {
    itemKeyword: '测试商品',
    deliveryContent: '卡密内容测试',
    cardData: 'CARD123456'
  },
  text: {
    itemKeyword: '文本商品',
    deliveryContent: '这是自动发货的文本内容'
  }
};

export const TestNotifications = {
  channel: {
    name: '测试通知渠道',
    type: 'webhook',
    config: {
      url: 'https://example.com/webhook'
    }
  }
};

export const TestSettings = {
  ai: {
    enabled: true,
    model: 'gpt-3.5-turbo',
    temperature: 0.7,
    maxTokens: 500
  },
  system: {
    logLevel: 'info',
    autoBackup: true,
    backupInterval: 24
  }
};

export const Selectors = {
  // 登录页面
  login: {
    usernameInput: '#username',
    passwordInput: '#password',
    emailInput: '#emailForPassword',
    captchaInput: '#captchaCode',
    verificationCodeInput: '#verificationCode',
    loginButton: 'button[type="submit"]',
    sendCodeButton: '#sendCodeBtn',
    captchaImage: '#captchaImage',
    loginTypeRadio: 'input[name="loginType"]',
    usernameLoginTab: '#usernameLogin + label',
    emailPasswordTab: '#emailPasswordLogin + label',
    emailCodeTab: '#emailCodeLogin + label'
  },
  
  // 导航菜单
  nav: {
    sidebar: '#sidebar',
    mobileToggle: '.mobile-toggle',
    dashboard: 'a[onclick="showSection(\'dashboard\')"]',
    accounts: 'a[onclick="showSection(\'accounts\')"]',
    items: 'a[onclick="showSection(\'items\')"]',
    autoReply: 'a[onclick="showSection(\'auto-reply\')"]',
    cards: 'a[onclick="showSection(\'cards\')"]',
    autoDelivery: 'a[onclick="showSection(\'auto-delivery\')"]',
    notifications: 'a[onclick="showSection(\'notification-channels\')"]',
    messages: 'a[onclick="showSection(\'message-notifications\')"]',
    settings: 'a[onclick="showSection(\'system-settings\')"]',
    logout: 'a[onclick="logout()"]'
  },
  
  // 账号管理
  accounts: {
    qrLoginButton: '.qr-login-btn',
    manualInputButton: '.manual-input-btn',
    manualInputForm: '#manualInputForm',
    cookieIdInput: '#cookieId',
    cookieValueInput: '#cookieValue',
    addForm: '#addForm',
    addButton: 'button[type="submit"]',
    cancelButton: 'button[onclick="toggleManualInput()"]',
    refreshButton: 'button[onclick="loadCookies()"]',
    defaultReplyButton: 'button[onclick="openDefaultReplyManager()"]',
    cookieTable: '#cookieTable',
    tableRows: '#cookieTable tbody tr'
  },
  
  // 关键词管理
  keywords: {
    accountSelect: '#accountSelect',
    refreshAccountList: 'button[onclick="refreshAccountList()"]',
    keywordInput: '#newKeyword',
    replyInput: '#newReply',
    itemIdSelect: '#newItemIdSelect',
    matchTypeSelect: '#newMatchType',
    priorityInput: '#newPriority',
    replyModeSelect: '#newReplyMode',
    addTextButton: 'button[onclick="addKeyword()"]',
    addImageButton: 'button[onclick="showAddImageKeywordModal()"]',
    keywordsList: '#keywordsList',
    testMessageInput: '#testMessage',
    testItemIdInput: '#testItemId',
    testButton: 'button[onclick="testKeywordMatch()"]',
    exportButton: 'button[onclick="exportKeywords()"]',
    importButton: 'button[onclick="showImportModal()"]',
    advancedConditions: '.advanced-conditions-header',
    timeStartInput: '#timeStartHour',
    timeEndInput: '#timeEndHour',
    excludeKeywordsInput: '#excludeKeywords',
    maxTriggerInput: '#maxTriggerCount',
    userTypeSelect: '#userType'
  },
  
  // 商品管理
  items: {
    cookieFilter: '#itemCookieFilter',
    pageNumber: '#pageNumber',
    getPageButton: 'button[onclick="getAllItemsFromAccount()"]',
    getAllButton: 'button[onclick="getAllItemsFromAccountAll()"]',
    refreshButton: 'button[onclick="refreshItems()"]',
    selectAllCheckbox: '#selectAllItems',
    batchDeleteButton: '#batchDeleteBtn',
    itemsTable: '#itemsTableBody'
  },
  
  // 卡券管理
  cards: {
    addCardButton: 'button[onclick="showAddCardModal()"]',
    cardTable: '#cardTable',
    importCardsButton: 'button[onclick="showImportCardsModal()"]',
    exportCardsButton: 'button[onclick="exportCards()"]'
  },
  
  // 自动发货
  delivery: {
    addRuleButton: 'button[onclick="showAddDeliveryRuleModal()"]',
    ruleTable: '#deliveryRulesTable',
    refreshButton: 'button[onclick="loadDeliveryRules()"]'
  },
  
  // 系统设置
  settings: {
    saveButton: 'button[onclick="saveSystemSettings()"]',
    resetButton: 'button[onclick="resetSystemSettings()"]',
    reloadCacheButton: 'button[onclick="reloadSystemCache()"]',
    logLevelSelect: '#logLevel',
    autoBackupToggle: '#autoBackup',
    backupIntervalInput: '#backupInterval'
  },
  
  // 通用
  common: {
    modal: '.modal',
    modalContent: '.modal-content',
    modalClose: '.modal-header .btn-close, button[data-bs-dismiss="modal"]',
    toast: '.toast',
    toastMessage: '.toast .toast-body',
    confirmButton: '.modal-footer .btn-primary',
    cancelButton: '.modal-footer .btn-secondary',
    loading: '.loading, .spinner-border'
  }
};

export const Timeouts = {
  short: 2000,
  medium: 5000,
  long: 10000,
  navigation: 30000,
  api: 15000
};

export const URLs = {
  login: '/login.html',
  register: '/register.html',
  dashboard: '/',
  index: '/index.html',
  userManagement: '/user_management.html',
  logManagement: '/log_management.html',
  dataManagement: '/data_management.html',
  itemSearch: '/item_search.html'
};
