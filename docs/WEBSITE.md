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
node --check website/site.js
```

## GitHub Pages

部署工作流为 `.github/workflows/pages.yml`，只上传 `website/`。首次启用时，在仓库 **Settings → Pages → Build and deployment → Source** 中选择 **GitHub Actions**。

推送 `website/`、检查脚本或部署工作流的变更到 `main` 后自动部署，也可手动运行 **Deploy Pasto website**。官网预期地址为 `https://yingyanzhitong.github.io/pasto/`，成功状态以 Actions 的部署结果为准。部署不修改应用版本，也不运行 macOS 安装包发布步骤；仓库现有 Release 工作流仍按原版本规则独立判断。

更新应用版本时，同步更新网页里的发布版本、DMG 下载地址和页面说明；静态检查会阻止下载地址与根目录 `package.json` 的当前版本不一致。复制到官网的真实演示截图来自 `docs/images/`，图标来自 `replica/Assets/`；替换素材前确保不含用户历史或其他隐私。

## 设计技能

使用本机 `frontend-design` 技能指导布局、字体、内容与响应式设计；技能来源可在 [Skills 目录](https://skills.sh/anthropics/skills/frontend-design) 查看。GitHub Pages 工作流参考 [GitHub 官方文档](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)。
