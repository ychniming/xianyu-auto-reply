/**
 * Vitest 全局设置文件
 * 提供测试所需的全局 mock 和配置
 */
import { vi } from 'vitest';

const htmlTemplate = `<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
  <div id="app">
    <div class="toast-container"></div>
    <div id="loading" class="d-none"></div>
    <nav>
      <a href="#" class="nav-link active" onclick="showSection('dashboard')">Dashboard</a>
      <a href="#" class="nav-link" onclick="showSection('accounts')">Accounts</a>
      <a href="#" class="nav-link" onclick="showSection('auto-reply')">Auto Reply</a>
      <a href="#" class="nav-link" onclick="showSection('cards')">Cards</a>
      <a href="#" class="nav-link" onclick="showSection('items')">Items</a>
      <a href="#" class="nav-link" onclick="showSection('notifications')">Notifications</a>
      <a href="#" class="nav-link" onclick="showSection('ai-reply')">AI Reply</a>
      <a href="#" class="nav-link" onclick="showSection('system')">System</a>
    </nav>
    <button id="menuToggle">Menu</button>
    <button id="logoutBtn">Logout</button>
    <div id="dashboard-section" class="content-section active"></div>
    <div id="accounts-section" class="content-section"></div>
    <div id="auto-reply-section" class="content-section"></div>
    <div id="cards-section" class="content-section"></div>
    <div id="items-section" class="content-section"></div>
    <div id="notifications-section" class="content-section"></div>
    <div id="ai-reply-section" class="content-section"></div>
    <div id="system-section" class="content-section"></div>

    <!-- Accounts Section -->
    <table id="cookieTable"><tbody></tbody></table>

    <!-- Auto Reply Section -->
    <select id="accountSelect"><option value="">请选择一个账号</option></select>
    <div id="keywordManagement" style="display:none;"></div>
    <div id="keywordsList"></div>
    <div id="newItemIdSelect"></div>
    <form id="addKeywordForm" style="display:none;">
      <input id="newKeyword" />
      <textarea id="newReply"></textarea>
      <button class="add-btn">添加</button>
    </form>
    <div id="currentAccountBadge"></div>
    <div id="imagePreview" style="display:none;">
      <img id="previewImg" />
    </div>

    <!-- Cards Section -->
    <div id="cardsList"></div>
    <div id="cardsStats"></div>
    <div id="addCardModal" class="modal">
      <select id="cardTypeSelect"></select>
      <select id="cardCookieSelect"></select>
      <input id="cardName" />
      <textarea id="cardTextContent"></textarea>
      <input id="cardDeliveryContent" />
      <input id="cardImage" />
    </div>
    <div id="editCardModal" class="modal"></div>
    <div id="textFields" style="display:none;"></div>
    <div id="imageFields" style="display:block;"></div>

    <!-- Delivery Rules Section -->
    <div id="deliveryRulesList"><table id="deliveryRulesTable"><tbody id="deliveryRulesTbody"></tbody></table></div>
    <div id="deliveryStats"></div>
    <select id="deliveryCardSelect"></select>
    <div id="addDeliveryRuleModal" class="modal">
      <form id="addDeliveryRuleForm"></form>
    </div>

    <!-- Notifications Section -->
    <div id="channelsList"><table id="channelsTable"><tbody id="channelsTbody"></tbody></table></div>
    <div id="addChannelModal" class="modal"></div>
    <div id="messageNotificationSettings" style="display:none;"></div>

    <!-- Items Section -->
    <div id="itemsList"><table id="itemsTable"><tbody id="itemsTbody"></tbody></table></div>
    <select id="cookieFilter"><option value="">全部账号</option></select>
    <button id="batchDeleteBtn" disabled>批量删除</button>

    <!-- AI Reply Section -->
    <div id="aiReplySettingsPanel" style="display:none;"></div>
    <input id="aiReplyEnabled" type="checkbox" />
    <select id="aiModel"><option value="gpt-4">GPT-4</option></select>
    <input id="aiApiKey" type="password" />
    <textarea id="aiCustomPrompt"></textarea>
    <input id="aiTemperature" value="0.7" />
    <input id="aiMaxTokens" value="500" />
    <input id="intentClassification" type="checkbox" />
    <input id="autoDelivery" type="checkbox" />
    <div id="customModelInput" style="display:none;"></div>
    <textarea id="aiTestInput">Test message</textarea>
    <textarea id="aiTestOutput"></textarea>
    <button id="testAIReplyBtn">Test</button>
    <select id="aiAccountSelect"></select>

    <!-- Default Replies -->
    <div id="defaultRepliesModal" class="modal"></div>
    <textarea id="priceDefaultReply">默认价格回复</textarea>
    <textarea id="techDefaultReply">默认技术回复</textarea>
    <textarea id="defaultDefaultReply">默认回复</textarea>

    <!-- System Section -->
    <div id="systemInfo"></div>
    <div id="maintenanceModeToggle"></div>

    <!-- QR Login -->
    <div id="qrCodeModal" class="modal">
      <img id="qrCodeImage" />
      <div id="qrCodeStatus"></div>
    </div>
    <div id="loginForm">
      <input id="username" />
      <input id="password" />
    </div>

    <!-- Logs -->
    <div id="logsContainer"></div>
    <div id="statsCards">
      <span id="totalAccounts">0</span>
      <span id="totalKeywords">0</span>
      <span id="activeAccounts">0</span>
    </div>

    <!-- Auto Refresh -->
    <div id="autoRefreshToggle">
      <i class="refresh-icon"></i>
      <span>Auto Refresh</span>
    </div>
  </div>
</body>
</html>`;

class MockElement {
  constructor(tagName = 'div') {
    this.tagName = tagName.toUpperCase();
    this.children = [];
    this.classList = new MockClassList();
    this.style = {};
    this.attributes = {};
    this.innerHTML = '';
    this.textContent = '';
    this.value = '';
    this.disabled = false;
    this.id = '';
    this.onclick = null;
  }

  appendChild(child) {
    this.children.push(child);
    return child;
  }

  removeChild(child) {
    const idx = this.children.indexOf(child);
    if (idx >= 0) this.children.splice(idx, 1);
    return child;
  }

  getElementById(id) {
    if (this.id === id) return this;
    for (const child of this.children) {
      if (child.getElementById) {
        const found = child.getElementById(id);
        if (found) return found;
      }
    }
    return null;
  }

  querySelectorAll(selector) {
    const results = [];
    const check = (el) => {
      if (el.classList && el.classList.contains(selector.replace('.', ''))) {
        results.push(el);
      }
      if (el.children) el.children.forEach(check);
    };
    this.children.forEach(check);
    return results;
  }

  querySelector(selector) {
    return this.querySelectorAll(selector)[0] || null;
  }

  addEventListener(event, handler) {
    this[`on${event}`] = handler;
  }

  removeEventListener(event) {
    delete this[`on${event}`];
  }

  setAttribute(name, value) {
    this.attributes[name] = value;
    if (name === 'id') this.id = value;
  }

  getAttribute(name) {
    return this.attributes[name];
  }

  click() {
    if (this.onclick) this.onclick();
  }
}

class MockClassList {
  constructor() {
    this.classes = new Set();
  }
  add(cls) { this.classes.add(cls); }
  remove(cls) { this.classes.delete(cls); }
  contains(cls) { return this.classes.has(cls); }
  toggle(cls) {
    if (this.classes.has(cls)) this.classes.delete(cls);
    else this.classes.add(cls);
  }
}

class MockDocument {
  constructor(dom) {
    this.body = dom.body;
    this.documentElement = dom.documentElement;
  }

  getElementById(id) {
    return this.body?.getElementById(id) || null;
  }

  querySelector(selector) {
    return this.body?.querySelector(selector) || null;
  }

  querySelectorAll(selector) {
    return this.body?.querySelectorAll(selector) || [];
  }

  createElement(tagName) {
    return new MockElement(tagName);
  }

  get title() { return 'Test'; }
  get URL() { return 'http://localhost:8080'; }
}

class MockWindow {
  constructor(dom) {
    this.document = new MockDocument(dom);
    this.location = { origin: 'http://localhost:8080', href: 'http://localhost:8080/', assign: vi.fn() };
    this.navigator = { clipboard: { writeText: vi.fn().mockResolvedValue() }, userAgent: 'node' };
    this.history = { pushState: vi.fn() };
    this.localStorage = {
      data: { auth_token: 'test_token' },
      getItem(key) { return this.data[key] || null; },
      setItem(key, val) { this.data[key] = val; },
      removeItem(key) { delete this.data[key]; }
    };

    this.bootstrap = {
      Modal: class {
        constructor(el) { this.el = el; }
        show() {}
        hide() {}
      },
      Toast: class {
        constructor(el) { this.el = el; }
        show() {}
        hide() {}
      }
    };

    this.showToast = vi.fn((message, type) => {
      console.log(`Toast: ${message} (${type})`);
    });

    this.toggleLoading = vi.fn((show) => {});

    this.showSection = vi.fn((sectionName) => {});

    this.toggleSidebar = vi.fn(() => {});

    this.accountKeywordCache = {};
    this.cacheTimestamp = 0;
    this.filteredLogs = [];
    this.autoRefreshInterval = null;
    this.currentCookieId = 'test_account';
    this.keywordsData = {};
  }

  alert(msg) {}

  URL = {
    createObjectURL: vi.fn(() => 'blob:test'),
    revokeObjectURL: vi.fn()
  };
}

export function setupGlobals() {
  const { JSDOM } = require('jsdom');
  const dom = new JSDOM(htmlTemplate);

  global.document = dom.window.document;
  global.window = new MockWindow(dom);
  global.navigator = global.window.navigator;
  global.location = global.window.location;

  global.fetch = vi.fn();
  global.confirm = vi.fn(() => true);
  global.setInterval = vi.fn(() => 123);
  global.clearInterval = vi.fn();
  global.alert = vi.fn();

  global.Element = MockElement;
  global.HTMLElement = MockElement;
}

beforeEach(() => {
  setupGlobals();
});

afterEach(() => {
  vi.clearAllMocks();
});
