# Pasto 官网

官网源码位于 `website/`，使用原生 HTML、CSS 和 JavaScript，无需安装依赖。设计参考 Paste 官网的大留白、产品演示与清晰下载入口，使用 Pasto 自己的品牌、演示界面和功能说明，不使用原厂宣传图或用户评价。

## 本地预览

在仓库根目录执行：

```sh
python3 -m http.server 4173 --bind 127.0.0.1 --directory website
```

打开 `http://127.0.0.1:4173/`。搜索和类型筛选仅操作网页内的合成演示数据，不访问系统剪贴板。

提交前可执行静态检查：

```sh
python3 scripts/check-website.py
node --check website/i18n.js
node --check website/site.js
node scripts/test-website-i18n.cjs
```

## GitHub Pages

部署工作流为 `.github/workflows/pages.yml`，只上传 `website/`。首次启用时，在仓库 **Settings → Pages → Build and deployment → Source** 中选择 **GitHub Actions**。

推送 `website/`、检查脚本或部署工作流的变更到 `main` 后自动部署，也可手动运行 **Deploy Pasto website**。官网预期地址为 `https://yingyanzhitong.github.io/pasto/`，成功状态以 Actions 的部署结果为准。部署不修改应用版本，也不运行 macOS 安装包发布步骤；仓库现有 Release 工作流仍按原版本规则独立判断。

更新应用版本时，同步更新网页里的发布版本、DMG 下载地址和页面说明；静态检查会阻止下载地址与根目录 `package.json` 的当前版本不一致。复制到官网的真实演示截图来自 `docs/images/`，图标来自 `replica/Assets/`；替换素材前确保不含用户历史或其他隐私。

## 官网语言

- 支持简体中文和 English，文案位于 `website/i18n.js`，不依赖翻译服务或额外框架。
- 首次访问按浏览器提供的系统首选语言列表选择：`zh-*` 使用简体中文，`en-*` 使用英文；列表中没有支持的语言时回退到英文。
- 右上角下载按钮后的语言图标提供“跟随系统 / 简体中文 / English”。手动选择保存在本站 `localStorage` 的 `pasto.website.language`；恢复“跟随系统”时清除此覆盖。浏览器禁用存储时，当前访问仍可切换。
- 切换会更新正文、FAQ、演示、数量单复数、页面标题和描述、图片替代文字、无障碍标签及 `html.lang`，保留当前搜索、筛选和 FAQ 展开状态。搜索支持中英文关键词。
- 真实软件截图仍为中文界面的合成数据截图，英文图片替代文字明确标注，不伪造应用的英文界面。
- 无 JavaScript 时保留静态中文内容。新增语言时同步补充字典、菜单选项和语言匹配规则；19 项脚本检查验证首选语言、存储失败、切换恢复、字典完整性及搜索行为。
- GitHub Pages 工作流在部署前运行脚本语法、静态资源和 i18n 检查；这些检查不触发应用构建或安装包发布。

## 设计技能

使用本机 `design-taste-frontend` 与 `impeccable` 的简化、配色和收尾规范。此次属于现有官网的视觉调整，保留品牌、导航、下载地址、功能文案和搜索演示。技能来源：[Taste Skill](https://github.com/Leonxlnx/taste-skill)、[Impeccable](https://github.com/pbakaus/impeccable)。GitHub Pages 工作流参考 [GitHub 官方文档](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)。


## 当前视觉规范（2026-10-29）

- 官网面板截图使用当前 Pasto 真实视图和独立合成记录生成，包含 Pasto、微信、Chrome、备忘录、VS Code 和图书的来源图标及实际颜色；不对截图手工改色，不读取用户剪贴板。图片尺寸保持 3024 × 664，文档与官网共用同一份素材。
- 按用户要求保留官网原版布局：发布提示、标题比例、笔记本示意与漂浮标签、三列功能说明、本地内容轨道、对比表、迁移卡片和下载区的位置、间距及圆角均沿用原版。
- 保留灰白页面和深色下载按钮，以 Pasto 青色 `#0b6d78` 点缀标题、链接和重点；功能图标、演示卡片采用浅绿、浅蓝和暖橙，模拟桌面使用低饱和蓝绿与暖色背景。原有形状、间距与位置不变，真实图标和软件截图不改色。
- 深色跟随系统，只改变颜色。中英文语言菜单保留在右上角；窄屏收起部分导航项与顶部下载按钮，正文下载入口保留。
- 语言入口参考 [Vue 官网](https://vuejs.org/) 的导航工具图标方式：位于下载按钮右侧，以分隔线区分；入口不显示系统偏好文案，展开后提供语言与“跟随系统”。使用原生 `details/summary`，支持键盘操作、Escape、点击外部关闭和选择后恢复焦点。
- 新增翻译的文字使用无布局样式的内联包装；避免嵌套文字包装继承标签容器的内边距。
- 本轮以改版前的 HTML/CSS 作为基准，在 320、390、768、1280、1440px 下对照主要区块的坐标与尺寸；中文布局差异为零，英文无页面横向溢出。验证材料保存在 Git 忽略的 `.local/website-layout-restore/`。
