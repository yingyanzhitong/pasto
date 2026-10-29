// Local translations only; no network requests or external translation service.
(() => {
  const messages = {
  "zh-CN": {
    "meta.title": "Pasto — 复制过的，都值得留住。",
    "meta.description": "Pasto，免费开源的 Mac 剪贴板工具。保存复制记录，用搜索、收藏分组与 Stack 找回和整理常用内容。支持 Intel 与 Apple 芯片。",
    "meta.socialDescription": "免费的 Mac 剪贴板工具。历史、搜索、分组与 OCR，都留在自己的 Mac。",
    "a11y.skip": "跳到正文",
    "a11y.navigation": "主导航",
    "a11y.home": "Pasto 首页",
    "nav.features": "功能",
    "nav.compare": "与 Paste 对比",
    "nav.faq": "常见问题",
    "nav.download": "免费下载",
    "hero.title": "复制过的，\n都值得留住。",
    "hero.description.one": "一句灵感、一张图片、一段常用文字。",
    "hero.description.two": "让复制记录留在手边，下一次需要，轻松找回。",
    "download.mac": "免费下载 Mac 版",
    "hero.try": "看看怎么用",
    "compat.chips": "Intel 与 Apple 芯片",
    "common.openSource": "免费开源",
    "a11y.panel": "Pasto 实际面板，窄屏可左右滚动查看",
    "image.panel": "Pasto 实际剪贴板面板：横向浏览文本、图片和收藏分组，内容为演示数据",
    "image.caption": "实际软件界面，内容为演示数据",
    "hero.shortcut": "打开剪贴板",
    "hero.local": "内容保存在本地",
    "hero.source": "源码公开",
    "hero.account": "没有订阅，也无需账号",
    "features.title.one": "你的剪贴板，",
    "features.title.two": "可以多做一点。",
    "features.description": "把每天重复的小动作，变得更顺手。",
    "history.title": "复制记录，不用再找一遍",
    "history.description": "文字、图片、文件和链接，自动收进历史。需要时打开面板，再次使用。",
    "type.text": "文字",
    "type.image": "图片",
    "type.file": "文件",
    "type.link": "链接",
    "collections.title": "常用内容，放在一起",
    "collections.description": "用分组收藏常用片段，用 Stack 整理待粘贴的顺序。让重复工作少一点。",
    "collections.work": "工作常用",
    "collections.ideas": "灵感收藏",
    "ocr.title": "图片里的字，也能复制",
    "ocr.description": "本地识别图片文字，搜索已有识别结果。把截图里的内容，变成可用的文字。",
    "ocr.sample": "好想法，值得留下。",
    "search.title.one": "刚刚复制的，",
    "search.title.two": "和上次收藏的。",
    "search.description.one": "记不清放在哪里，记得一点内容就好。",
    "search.description.two": "搜索、切换类型，让需要的片段浮到眼前。",
    "search.more": "了解全部功能",
    "demo.heading": "试着找一条内容",
    "demo.disclaimer": "网页交互示意 · 演示数据",
    "demo.placeholder": "搜索复制记录…",
    "a11y.search": "搜索演示记录",
    "a11y.reset": "清空搜索和筛选",
    "demo.reset": "重置",
    "a11y.filters": "演示内容类型",
    "demo.all": "全部",
    "demo.note": "灵感备忘",
    "demo.now": "刚刚",
    "demo.sample.one": "少一次寻找，",
    "demo.sample.two": "多一点心流。",
    "demo.links": "实用链接",
    "demo.twoMinutes": "2 分钟前",
    "demo.design": "设计收藏",
    "demo.fiveMinutes": "5 分钟前",
    "image.demoIcon": "演示记录中的 Pasto 图标",
    "demo.empty": "没有找到这条记录，换个关键词试试。",
    "demo.initial": "3 条演示记录",
    "demo.noScript": "启用 JavaScript 后可试用搜索与筛选；上方是演示记录。",
    "privacy.caption": "保存在你的 Mac",
    "privacy.title.one": "你的内容，",
    "privacy.title.two": "留在自己手里。",
    "privacy.description.one": "Pasto 不需要账号，不提供云同步。",
    "privacy.description.two": "剪贴板内容保存在自己的 Mac 上，",
    "privacy.description.three": "也可以暂停记录，或排除指定应用。",
    "privacy.note": "本地数据为明文存储，请妥善保管电脑及导出归档。",
    "privacy.source": "查看开源代码",
    "compare.title.one": "专注你在 Mac 上",
    "compare.title.two": "常用的那部分。",
    "compare.description": "参考 Paste 的本地使用体验，Pasto 免费开源。",
    "a11y.comparison": "Paste 与 Pasto 核心功能对比",
    "compare.column": "核心功能",
    "compare.history": "剪贴板历史与搜索",
    "common.supported": "支持",
    "common.implemented": "已有实现",
    "common.unsupported": "不支持",
    "compare.collections": "收藏分组与 Stack",
    "compare.paste": "复制粘贴与自定义快捷键",
    "compare.ocr": "图片文字识别（OCR）",
    "compare.mcp": "AI 工具接入（MCP）",
    "compare.shortcuts": "系统“快捷指令”",
    "compare.cloud": "云同步、手机端与共享协作",
    "compare.preview": "联网链接预览",
    "compare.note.one": "✅ 表示已有实现，不代表全部场景已验证。跨应用直接粘贴及完整交互仍待全面回归。",
    "compare.note.two": "对照参考 Paste 6.6.6；Pasto 是独立项目，与 Paste 原厂无关联。",
    "migration.title": "收藏的分组，一起带过来。",
    "migration.description.one": "保留分组名称、颜色、排列顺序与组内内容。",
    "migration.description.two": "只读导入，重复迁移不会覆盖你在 Pasto 中的编辑。",
    "migration.more": "查看迁移说明",
    "faq.title": "你可能想知道。",
    "faq.free.question": "Pasto 是免费的吗？",
    "faq.free.answer": "是。Pasto 的独立实现按 MIT 许可开源，无需订阅或原厂账号。原版研究材料的权利范围单独说明，详见仓库中的 NOTICE。",
    "faq.mac.question": "我的 Mac 可以使用吗？",
    "faq.mac.answer": "支持 macOS 14 及以上。一个 Universal DMG 同时包含 Intel 与 Apple 芯片架构，无需区分下载。构建通过不代表两个架构的所有功能均已完成回归。",
    "faq.install.question": "怎么安装？为什么需要辅助功能权限？",
    "faq.install.answer": "下载并打开 DMG，将 Pasto.app 拖入 Applications，从应用程序目录启动，再推出安装镜像。直接粘贴到其他应用需要 macOS 辅助功能权限；仅保存和复制内容无需通过此权限发送按键。当前安装包采用临时签名，尚未经过 Apple 公证，请先阅读 Release 中的安装说明。",
    "faq.cloud.question": "会把我的剪贴板上传到云端吗？",
    "faq.cloud.answer": "Pasto 不实现云同步，剪贴板数据保存在本地。MCP 是可选的本地工具接口；若你自行连接第三方 AI 客户端，该客户端如何使用所读取的内容取决于它自己的设置。分享归档或日志前，也请检查是否包含隐私。",
    "faq.parity.question": "和 Paste 完全一样吗？",
    "faq.parity.answer": "尚未完全一致。Pasto 依据 Paste 6.6.6 的 REA / Ghidra 逆向证据独立实现本地功能，未完成全部原函数迁移或一比一验收。云同步、远程共享、联网预览不在实现范围内；系统“快捷指令”尚未完成接入。直接粘贴等交互的完整兼容性仍在完善。",
    "image.appIcon": "Pasto 图标",
    "download.title.one": "给复制，",
    "download.title.two": "多一点记忆。",
    "download.start": "从下一次",
    "download.end": "开始。",
    "download.meta": "v1.0.0 · macOS 14+ · Intel / Apple 芯片",
    "download.releases": "更新日志与所有版本",
    "footer.tagline": "免费的本地 Mac 剪贴板工具。",
    "footer.feedback": "反馈问题",
    "footer.license": "许可说明",
    "footer.legal": "© 2026 Pasto · 独立开源项目，与 Paste 原厂无关联。",
    "language.label": "显示语言",
    "language.system": "跟随系统",
    "demo.result.one": "{count} 条演示记录",
    "demo.result.other": "{count} 条演示记录",
    "demo.keywords.text": "文字 灵感 少一次寻找 多一点心流",
    "demo.keywords.link": "链接 github pasto 开源 软件",
    "demo.keywords.image": "图片 pasto 图标 设计",
    "hero.release": "Pasto 1.0.0 现已发布",
    "hero.title.one": "复制过的，",
    "hero.title.two": "都值得",
    "hero.title.mark": "留住。",
    "a11y.stage": "Pasto 在 Mac 上的界面示意",
    "stage.idea": "刚才的灵感，还在。",
    "stage.local": "只在你的 Mac 上。",
    "stage.file": "文件",
    "stage.edit": "编辑",
    "stage.date": "周四 10:28",
    "stage.eyebrow": "给下一个灵感",
    "stage.description.one": "常用的文字、收藏的链接、",
    "stage.description.two": "还没来得及整理的好想法。",
    "stage.shortcut": "复制记录，随叫随到。",
    "features.eyebrow": "从复制，到再次使用",
    "search.eyebrow": "找回，只需要一个关键词",
    "privacy.eyebrow": "本地优先，简单就好",
    "compare.eyebrow": "熟悉的用法，更轻的选择",
    "migration.eyebrow": "已经在用 Paste？",
    "faq.eyebrow": "开始之前",
    "language.trigger": "切换语言：{language}"
  },
  "en": {
    "meta.title": "Pasto | Copy once. Keep it close.",
    "meta.description": "Pasto is a free, open-source clipboard manager for Mac. Save your copy history, search, organize collections, and queue items with Stack. For Intel and Apple silicon.",
    "meta.socialDescription": "A free clipboard manager for Mac. History, search, collections, and OCR stay on your Mac.",
    "a11y.skip": "Skip to content",
    "a11y.navigation": "Main navigation",
    "a11y.home": "Pasto home",
    "nav.features": "Features",
    "nav.compare": "Compare with Paste",
    "nav.faq": "FAQ",
    "nav.download": "Free download",
    "hero.title": "Copy once.\nKeep it close.",
    "hero.description.one": "An idea, an image, a snippet you use every day.",
    "hero.description.two": "Keep what you copy handy, ready for next time.",
    "download.mac": "Download for Mac",
    "hero.try": "See how it works",
    "compat.chips": "Intel and Apple silicon",
    "common.openSource": "Free and open source",
    "a11y.panel": "Actual Pasto panel. Scroll horizontally on smaller screens.",
    "image.panel": "Actual Pasto clipboard panel in Chinese, showing sample text, images, and collections.",
    "image.caption": "Actual app interface in Chinese, with sample data",
    "hero.shortcut": "Open clipboard",
    "hero.local": "Stored on your Mac",
    "hero.source": "Source available",
    "hero.account": "No subscription or account",
    "features.title.one": "Your clipboard,",
    "features.title.two": "with more to offer.",
    "features.description": "Make everyday copy and paste a little easier.",
    "history.title": "Find what you copied",
    "history.description": "Automatically save text, images, files, and links to your history. Open the panel to use them again.",
    "type.text": "Text",
    "type.image": "Images",
    "type.file": "Files",
    "type.link": "Links",
    "collections.title": "Keep the useful things together",
    "collections.description": "Save your favorite snippets in collections. Queue items with Stack to paste them in order.",
    "collections.work": "Work essentials",
    "collections.ideas": "Saved ideas",
    "ocr.title": "Copy text from images",
    "ocr.description": "Recognize text in images locally and search the results. Turn the words in a screenshot into usable text.",
    "ocr.sample": "Good ideas are worth keeping.",
    "search.title.one": "Just copied.",
    "search.title.two": "Or saved for later.",
    "search.description.one": "Remember a few words, even if you forget where.",
    "search.description.two": "Search and filter by type to find the right snippet.",
    "search.more": "Explore all features",
    "demo.heading": "Try finding an item",
    "demo.disclaimer": "Interactive example · Sample data",
    "demo.placeholder": "Search clipboard history…",
    "a11y.search": "Search sample items",
    "a11y.reset": "Clear search and filters",
    "demo.reset": "Reset",
    "a11y.filters": "Sample content types",
    "demo.all": "All",
    "demo.note": "Idea note",
    "demo.now": "Just now",
    "demo.sample.one": "Less searching.",
    "demo.sample.two": "More doing.",
    "demo.links": "Useful link",
    "demo.twoMinutes": "2 minutes ago",
    "demo.design": "Design pick",
    "demo.fiveMinutes": "5 minutes ago",
    "image.demoIcon": "Pasto icon in a sample item",
    "demo.empty": "No matching items. Try a different keyword.",
    "demo.initial": "3 sample items",
    "demo.noScript": "Enable JavaScript to try search and filters. The items above are samples.",
    "privacy.caption": "Stored on your Mac",
    "privacy.title.one": "Your content.",
    "privacy.title.two": "In your hands.",
    "privacy.description.one": "Pasto needs no account and has no cloud sync.",
    "privacy.description.two": "Your clipboard content stays on your Mac.",
    "privacy.description.three": "Pause recording or exclude specific apps whenever you need.",
    "privacy.note": "Local data is stored as plain text. Keep your Mac and exported archives secure.",
    "privacy.source": "View the source",
    "compare.title.one": "Focused on what you",
    "compare.title.two": "use on your Mac.",
    "compare.description": "Inspired by the local Paste experience. Free and open source.",
    "a11y.comparison": "Paste and Pasto core feature comparison",
    "compare.column": "Core features",
    "compare.history": "Clipboard history and search",
    "common.supported": "Supported",
    "common.implemented": "Implemented",
    "common.unsupported": "Not supported",
    "compare.collections": "Collections and Stack",
    "compare.paste": "Copy, paste, and custom shortcuts",
    "compare.ocr": "Text recognition (OCR)",
    "compare.mcp": "AI tool integration (MCP)",
    "compare.shortcuts": "Apple Shortcuts",
    "compare.cloud": "Cloud sync, mobile apps, and sharing",
    "compare.preview": "Online link previews",
    "compare.note.one": "✅ means implemented, not tested in every scenario. Cross-app direct paste and full interactions still need comprehensive regression testing.",
    "compare.note.two": "Based on Paste 6.6.6. Pasto is an independent project, not affiliated with Paste.",
    "migration.title": "Bring your collections with you.",
    "migration.description.one": "Keep collection names, colors, order, and contents.",
    "migration.description.two": "Read-only import. Importing again will not overwrite your edits in Pasto.",
    "migration.more": "Read the migration guide",
    "faq.title": "A few things to know.",
    "faq.free.question": "Is Pasto free?",
    "faq.free.answer": "Yes. The independent Pasto implementation is open source under the MIT license, with no subscription or original vendor account required. Rights to the original research materials are described separately in the repository NOTICE.",
    "faq.mac.question": "Will it work on my Mac?",
    "faq.mac.answer": "Pasto supports macOS 14 and later. One Universal DMG includes both Intel and Apple silicon builds. A successful build does not mean every feature has been regression-tested on both architectures.",
    "faq.install.question": "How do I install it, and why Accessibility access?",
    "faq.install.answer": "Download and open the DMG, drag Pasto.app into Applications, launch it there, then eject the disk image. Direct paste into other apps requires macOS Accessibility access to send keystrokes; saving and copying content does not. The current package is ad-hoc signed and has not been notarized by Apple. Read the Release installation notes first.",
    "faq.cloud.question": "Is my clipboard uploaded to the cloud?",
    "faq.cloud.answer": "Pasto does not provide cloud sync; clipboard data is stored locally. MCP is an optional local tool interface. If you connect a third-party AI client, its own settings govern how it uses the content it reads. Check archives and logs for private information before sharing them.",
    "faq.parity.question": "Is it exactly the same as Paste?",
    "faq.parity.answer": "Not yet. Pasto independently implements local features based on REA / Ghidra reverse-engineering evidence from Paste 6.6.6. Not all original functions have been migrated or verified for exact parity. Cloud sync, remote sharing, and online previews are outside this release; Apple Shortcuts integration is unfinished. Compatibility for direct paste and other interactions is still being improved.",
    "image.appIcon": "Pasto icon",
    "download.title.one": "Give your clipboard",
    "download.title.two": "a memory.",
    "download.start": "Starting with your next",
    "download.end": ".",
    "download.meta": "v1.0.0 · macOS 14+ · Intel / Apple silicon",
    "download.releases": "Release notes and all versions",
    "footer.tagline": "A free, local clipboard manager for Mac.",
    "footer.feedback": "Report an issue",
    "footer.license": "License notes",
    "footer.legal": "© 2026 Pasto · An independent open-source project, not affiliated with Paste.",
    "language.label": "Display language",
    "language.system": "System language",
    "demo.result.one": "{count} sample item",
    "demo.result.other": "{count} sample items",
    "demo.keywords.text": "text idea note inspiration less searching more doing",
    "demo.keywords.link": "link github pasto open source software",
    "demo.keywords.image": "image pasto icon design",
    "hero.release": "Pasto 1.0.0 is here",
    "hero.title.one": "Copy once.",
    "hero.title.two": "Keep it ",
    "hero.title.mark": "close.",
    "a11y.stage": "Illustration of Pasto on Mac, with an actual Chinese interface and sample data",
    "stage.idea": "That idea is still here.",
    "stage.local": "On your Mac.",
    "stage.file": "File",
    "stage.edit": "Edit",
    "stage.date": "Thu 10:28",
    "stage.eyebrow": "For your next idea",
    "stage.description.one": "Useful snippets, saved links,",
    "stage.description.two": "and ideas to come back to.",
    "stage.shortcut": "Your clipboard, on call.",
    "features.eyebrow": "From copy to reuse",
    "search.eyebrow": "One keyword away",
    "privacy.eyebrow": "Local first. Keep it simple.",
    "compare.eyebrow": "Familiar tools. A lighter choice.",
    "migration.eyebrow": "Already using Paste?",
    "faq.eyebrow": "Before you start",
    "language.trigger": "Change language: {language}"
  }
};

  const storageKey = 'pasto.website.language';
  const isSupported = value => Object.prototype.hasOwnProperty.call(messages, value);
  let preference = 'system';
  try {
    const saved = localStorage.getItem(storageKey);
    if (isSupported(saved)) preference = saved;
  } catch { /* Language selection still works when browser storage is unavailable. */ }

  function systemLanguage() {
    const languages = navigator.languages?.length ? navigator.languages : [navigator.language];
    for (const requested of languages) {
      const base = String(requested).toLowerCase().split(/[-_]/)[0];
      if (base === 'zh') return 'zh-CN';
      if (base === 'en') return 'en';
    }
    return 'en';
  }

  let language = preference === 'system' ? systemLanguage() : preference;
  function t(key, values = {}) {
    const text = messages[language][key] ?? messages['zh-CN'][key] ?? key;
    return text.replace(/\{(\w+)\}/g, (match, name) => values[name] === undefined ? match : String(values[name]));
  }

  function applyLanguage() {
    language = preference === 'system' ? systemLanguage() : preference;
    document.documentElement.lang = language;
    for (const element of document.querySelectorAll('[data-i18n]')) {
      element.textContent = t(element.dataset.i18n);
    }
    for (const attribute of ['alt', 'aria-label', 'placeholder', 'content']) {
      const marker = `data-i18n-${attribute}`;
      for (const element of document.querySelectorAll(`[${marker}]`)) {
        element.setAttribute(attribute, t(element.getAttribute(marker)));
      }
    }
    for (const card of document.querySelectorAll('[data-i18n-search]')) {
      const key = card.dataset.i18nSearch;
      card.dataset.search = `${messages['zh-CN'][key]} ${messages.en[key]}`;
    }
    document.querySelector('meta[property="og:locale"]').content = language === 'en' ? 'en_US' : 'zh_CN';
    const label = t('language.trigger', { language: language === 'en' ? 'English' : '简体中文' });
    const trigger = document.querySelector('#language-trigger');
    trigger.setAttribute('aria-label', label);
    trigger.setAttribute('title', label);
    for (const option of document.querySelectorAll('[data-language]')) {
      option.setAttribute('aria-pressed', String(option.dataset.language === preference));
    }
    document.dispatchEvent(new CustomEvent('pasto:languagechange', { detail: { language } }));
  }

  function setPreference(value) {
    preference = isSupported(value) ? value : 'system';
    try {
      if (preference === 'system') localStorage.removeItem(storageKey);
      else localStorage.setItem(storageKey, preference);
    } catch { /* Keep the choice for this visit without requiring persistent storage. */ }
    applyLanguage();
  }

  window.PastoI18n = { t, get language() { return language; } };
  const switcher = document.querySelector('.language-switch');
  const trigger = document.querySelector('#language-trigger');
  for (const option of document.querySelectorAll('[data-language]')) {
    option.addEventListener('click', () => {
      setPreference(option.dataset.language);
      switcher.open = false;
      trigger.focus();
    });
  }
  document.addEventListener('click', event => {
    if (!switcher.contains(event.target)) switcher.open = false;
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && switcher.open) {
      switcher.open = false;
      trigger.focus();
    }
  });
  window.addEventListener('languagechange', () => { if (preference === 'system') applyLanguage(); });
  applyLanguage();
})();
