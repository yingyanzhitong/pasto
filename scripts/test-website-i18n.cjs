// Run the shipped browser scripts against DOM/storage fixtures; no dependencies or network.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'website/index.html'), 'utf8');
const i18n = fs.readFileSync(path.join(root, 'website/i18n.js'), 'utf8');
const demo = fs.readFileSync(path.join(root, 'website/site.js'), 'utf8');
const storageKey = 'pasto.website.language';
let checks = 0;
function check(name, operation) { operation(); checks++; }

class Element {
  constructor(tag, attrs) {
    this.tag = tag; this.attrs = attrs; this.textContent = ''; this.value = ''; this.hidden = false;
    this.dataset = Object.fromEntries(Object.entries(attrs).filter(([key]) => key.startsWith('data-'))
      .map(([key, value]) => [key.slice(5).replace(/-([a-z])/g, (_, c) => c.toUpperCase()), value]));
    this.events = new Map();
  }
  getAttribute(name) { return this.attrs[name] ?? null; }
  setAttribute(name, value) { this.attrs[name] = value; }
  addEventListener(name, callback) { this.events.set(name, callback); }
  emit(name) { this.events.get(name)?.({ target: this }); }
  focus() { this.ownerDocument.activeElement = this; }
}
function runtime(languages, saved = null, blocked = false) {
  const elements = [...html.matchAll(/<([a-z][\w-]*)\b([^>]*)>/gi)].map(([, tag, raw]) => {
    const attrs = Object.fromEntries([...raw.matchAll(/([\w:-]+)="([^"]*)"/g)].map(m => [m[1], m[2]]));
    return new Element(tag.toLowerCase(), attrs);
  });
  function matches(element, selector) {
    if (selector.startsWith('#')) return element.attrs.id === selector.slice(1);
    if (selector.startsWith('.')) return (element.attrs.class || '').split(/\s+/).includes(selector.slice(1));
    const attribute = selector.match(/^(?:([\w-]+))?\[([\w-]+)(?:="([^"]*)")?\]$/);
    return attribute && (!attribute[1] || attribute[1] === element.tag) &&
      Object.hasOwn(element.attrs, attribute[2]) && (attribute[3] === undefined || element.attrs[attribute[2]] === attribute[3]);
  }
  const events = new Map();
  const document = {
    documentElement: { lang: 'zh-CN' },
    querySelectorAll: selector => elements.filter(el => matches(el, selector)),
    querySelector: selector => elements.find(el => matches(el, selector)),
    addEventListener: (name, callback) => events.set(name, callback),
    dispatchEvent: event => events.get(event.type)?.(event)
  };
  for (const element of elements) element.ownerDocument = document;
  const storage = new Map(saved === null ? [] : [[storageKey, saved]]);
  const storageAPI = {
    getItem(key) { if (blocked) throw new Error('storage blocked'); return storage.get(key) ?? null; },
    setItem(key, value) { if (blocked) throw new Error('storage blocked'); storage.set(key, value); },
    removeItem(key) { if (blocked) throw new Error('storage blocked'); storage.delete(key); }
  };
  const windowEvents = new Map();
  const window = { addEventListener: (name, callback) => windowEvents.set(name, callback) };
  const navigator = { languages, language: languages[0] };
  const context = vm.createContext({ document, window, navigator, localStorage: storageAPI,
    CustomEvent: class { constructor(type, options) { this.type = type; this.detail = options.detail; } } });
  vm.runInContext(i18n, context, { filename: 'website/i18n.js' });
  vm.runInContext(demo, context, { filename: 'website/site.js' });
  return { document, storage, navigator, api: window.PastoI18n,
    choose(value) { document.querySelector(`[data-language="${value}"]`).emit('click'); },
    systemChanges(languages) { navigator.languages = languages; navigator.language = languages[0]; windowEvents.get('languagechange')(); } };
}

const messages = JSON.parse(i18n.match(/const messages = (\{[\s\S]*?\n\});/)[1]);
check('catalogs have identical keys and placeholders', () => {
  assert.deepEqual(Object.keys(messages.en).sort(), Object.keys(messages['zh-CN']).sort());
  for (const key of Object.keys(messages.en)) {
    assert.ok(messages.en[key] && messages['zh-CN'][key], key);
    assert.deepEqual(messages.en[key].match(/\{\w+\}/g), messages['zh-CN'][key].match(/\{\w+\}/g), key);
  }
});
check('all HTML translation bindings exist in both catalogs', () => {
  for (const [, key] of html.matchAll(/data-i18n(?:-(?:alt|aria-label|placeholder|content|search))?="([^"]+)"/g)) {
    assert.ok(Object.hasOwn(messages.en, key) && Object.hasOwn(messages['zh-CN'], key), key);
  }
});
for (const [languages, expected] of [
  [['zh-CN', 'en'], 'zh-CN'], [['zh-TW'], 'zh-CN'], [['en-US'], 'en'],
  [['ja-JP', 'fr-FR'], 'en'], [['fr-FR', 'zh-CN'], 'zh-CN'], [[], 'en']
]) check(`system negotiation ${languages.join(',') || 'missing'}`, () => {
  const app = runtime(languages);
  assert.equal(app.api.language, expected);
  assert.equal(app.document.documentElement.lang, expected);
  assert.equal(app.document.querySelector('[data-language="system"]').getAttribute('aria-pressed'), 'true');
  assert.equal(app.storage.size, 0);
});
check('manual preference wins over system and persists across visits', () => {
  const app = runtime(['zh-CN']); app.choose('en');
  assert.equal(app.storage.get(storageKey), 'en');
  assert.equal(runtime(['zh-CN'], app.storage.get(storageKey)).api.language, 'en');
});
check('returning to system removes manual override', () => {
  const app = runtime(['zh-CN'], 'en'); app.choose('system');
  assert.equal(app.api.language, 'zh-CN'); assert.equal(app.storage.has(storageKey), false);
});
check('invalid saved preference falls back to system', () => {
  assert.equal(runtime(['zh-CN'], 'not-a-supported-language').api.language, 'zh-CN');
});
check('storage denial preserves usable language switching', () => {
  const app = runtime(['zh-CN'], null, true); app.choose('en');
  assert.equal(app.api.language, 'en'); assert.equal(app.document.documentElement.lang, 'en');
});
check('system language changes are observed in automatic mode', () => {
  const app = runtime(['zh-CN']); app.systemChanges(['en-GB']); assert.equal(app.api.language, 'en');
});
check('system changes do not override manual choice', () => {
  const app = runtime(['en-US'], 'zh-CN'); app.systemChanges(['en-GB']); assert.equal(app.api.language, 'zh-CN');
});
check('metadata, accessible labels, placeholder and image alt are localized', () => {
  const app = runtime(['en-US']);
  assert.equal(app.document.querySelector('meta[property="og:locale"]').content, 'en_US');
  assert.equal(app.document.querySelector('#demo-search').getAttribute('placeholder'), 'Search clipboard history…');
  assert.equal(app.document.querySelector('#demo-search').getAttribute('aria-label'), 'Search sample items');
  assert.ok(app.document.querySelector('.actual-panel').getAttribute('alt').includes('in Chinese'));
});
check('English count uses singular and plural forms', () => {
  const app = runtime(['en-US']); const doc = app.document;
  assert.equal(doc.querySelector('.demo-result').textContent, '3 sample items');
  doc.querySelector('#demo-search').value = 'pasto'; doc.querySelector('#demo-search').emit('input');
  assert.equal(doc.querySelector('.demo-result').textContent, '2 sample items');
  doc.querySelector('[data-filter="link"]').emit('click');
  assert.equal(doc.querySelector('.demo-result').textContent, '1 sample item');
});
check('switching language preserves query, filter, and visible results', () => {
  const app = runtime(['en-US']); const doc = app.document;
  doc.querySelector('#demo-search').value = 'pasto'; doc.querySelector('#demo-search').emit('input');
  doc.querySelector('[data-filter="link"]').emit('click'); app.choose('zh-CN');
  assert.equal(doc.querySelector('#demo-search').value, 'pasto');
  assert.equal(doc.querySelector('[data-filter="link"]').getAttribute('aria-pressed'), 'true');
  assert.equal(doc.querySelector('.demo-result').textContent, '1 条演示记录');
});
check('English keyword search and empty/reset states remain functional', () => {
  const app = runtime(['en-US']); const doc = app.document; const input = doc.querySelector('#demo-search');
  input.value = 'inspiration'; input.emit('input');
  assert.equal(doc.querySelector('.demo-result').textContent, '1 sample item');
  input.value = 'no matching fixture'; input.emit('input'); assert.equal(doc.querySelector('.demo-empty').hidden, false);
  doc.querySelector('.demo-reset').emit('click');
  assert.equal(doc.querySelector('.demo-result').textContent, '3 sample items');
  assert.equal(doc.querySelector('.demo-empty').hidden, true); assert.equal(doc.activeElement, input);
});
check('language control reports current language and closes after selection', () => {
  const app = runtime(['zh-CN']); const doc = app.document;
  assert.equal(doc.querySelector('#language-trigger').getAttribute('title'), '切换语言：简体中文');
  doc.querySelector('.language-switch').open = true;
  app.choose('en');
  assert.equal(doc.querySelector('[data-language="en"]').getAttribute('aria-pressed'), 'true');
  assert.equal(doc.querySelector('[data-language="system"]').getAttribute('aria-pressed'), 'false');
  assert.equal(doc.querySelector('#language-trigger').getAttribute('aria-label'), 'Change language: English');
  assert.equal(doc.querySelector('.language-switch').open, false);
  assert.equal(doc.activeElement, doc.querySelector('#language-trigger'));
});
console.log(JSON.stringify({ passed: true, checks, translation_keys: Object.keys(messages.en).length }));
