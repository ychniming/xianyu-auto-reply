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
    </nav>
    <button id="menuToggle">Menu</button>
    <div id="dashboard-section" class="content-section active"></div>
    <div id="accounts-section" class="content-section"></div>
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