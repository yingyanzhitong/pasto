# Paste 兼容处理迁移到 Pasto

日期为 2026-11-04。原版对照为 Paste 6.6.6，Pasto 源码基线为 `0fe82119e435e99399cc63c7440e3874ac122d3b`，版本为 1.0.4。交付为本地源码补丁和本地 debug 通用测试包。

## 对比与处理

本轮对照原兼容性报告中的 12 项处理。既有分支通过源码复查复用，缺口按原版证据补齐。

| 项目 | 对照结果与处理 |
| --- | --- |
| 主程序、助手和 MCP 双架构 | 现有 universal 构建逻辑可复用。默认构建改为 universal，继续校验三份可执行文件的 arm64 与 x86_64 切片 |
| 最低 macOS 14 | Swift Package 和 Info.plist 已配置。增加逐架构 Mach-O minos 校验，避免声明与实际二进制要求不一致 |
| 玻璃效果与旧系统回退 | 保留 macOS 26 判断和运行时玻璃类查找。旧系统材质从 HUDWindow 改为原版传入的 Menu，保留 behindWindow、active |
| 模态窗口新旧实现 | 已有 macOS 26 玻璃窗口及旧系统 NSWindow 分支，原处理复用 |
| 主面板圆角、边距 | 已有 macOS 26 的 26 点圆角、8 点边距及较旧系统分支，原处理复用 |
| 搜索框焦点圆角 | 已有 macOS 26 半高圆角、较旧系统 6 点圆角，原处理复用 |
| 卡片阴影 | 补齐 macOS 26 的 0.08 透明度与零偏移，较旧系统为 0.10 透明度和向下 1 点偏移，模糊参数为 2。SwiftUI 向下坐标对应原 NSShadow 高度 -1 |
| Spotlight 新字段 | 已有 macOS 26.4 起写入和查询 contentDescription 的双向判断，原处理复用 |
| 资源 bundle 定位 | 新增共享 OriginalResourceBundle。依次检查应用 Resources、类型所在 bundle 的 Resources、应用根目录，开发环境最后使用 SwiftPM bundle。所有本地化、设置插图、音效和 Stack 图标入口接入 |
| Stack 图标跨环境加载 | 原裁剪 Assets.car 可复现 CoreUI 读取失败，改用从原版四类模板图标导出的 1×/2× PNG，保留 20 点逻辑尺寸与模板渲染 |
| Swift 兼容动态库 | 构建时使用当前工具链的 swift-stdlib-tool 扫描整个应用并按需嵌入。主程序、MCP、助手均增加指向随包 Frameworks 的 rpath，新增缺库和库架构校验 |
| 原版数据库模型匹配 | 保留前轮补充的实际安装位置查找、历史 .mom 元数据匹配和源库只读处理。对缺少必需字段的旧图结构明确拒绝，并提示先用新版 Paste 升级数据 |

## 原版证据

- `0x100036164` 机器码将材质参数设为 5，随后调用 `0x100220ffc`。本机 AppKit 头文件将该值定义为 NSVisualEffectMaterialMenu。
- `0x100220ffc`、`0x10021dd64` 包含 macOS 26 的背景视图与窗口分支。
- `0x1003f26c4` 提供新旧系统的阴影透明度、偏移与模糊参数。
- `0x1002fa3d4` 提供三组 bundle 资源根目录。
- 原版主程序两套架构弱加载 libswiftCompatibilitySpan.dylib，随包组件均提供相应切片。
- `0x100342fc4`、`0x10034c014` 提供数据库元数据兼容检查和历史模型加载。

原版玻璃类采用弱链接。Pasto 为兼容本机 SDK 15.2，使用有版本判断的 NSClassFromString 加载同一公开系统类。此处保留对应运行行为，并适配当前编译环境。

## 定向验证

环境为 arm64、macOS 26.2、SDK 15.2。x86_64 程序通过本机已有 Rosetta 2 运行。

| 验证 | 结果 |
| --- | --- |
| 默认构建生成通用应用 | 通过，主程序、助手和 MCP 均含两套架构 |
| 双架构 minos、Frameworks rpath 与完整签名校验 | 通过 |
| 打包契约与异常场景 | 4 组测试通过，覆盖架构缺失、最低系统错误、rpath 缺失、Swift 兼容库缺失及库架构缺失 |
| arm64 资源与版本分支测试 | 通过，应用 Resources 与应用根目录两种布局 |
| Rosetta x86_64 资源与版本分支测试 | 通过，同样覆盖两种布局 |
| 资源测试内容 | 四张设置插图、六类 Stack 图标、20/40 像素表示、模板标记、本地化、当前系统玻璃分支及 Spotlight 字段条件 |
| arm64 分组导入 | 通过，隔离数据库、WAL、外部二进制、模型发现、旧图结构拒绝、重开与重复导入保护 |
| Rosetta x86_64 分组导入 | 通过，同一套回归 |
| Bash 语法与 git diff --check | 通过 |

首次 PNG 导出的 2× 画布缺少缩放，新增像素覆盖断言成功复现该问题。修正后 2× 图标具备原版对应的高分辨率像素覆盖，最终通用包已重新构建并验证。

## 数据格式边界和运行验证范围

逐一读取原版 20 个编译模型，v5Paste.momd 的 v1–v10 均具备当前分组读取器需要的字段。v4Paste 和 v5Paste-old 的图结构不同，当前导入流程会明确拒绝，用户可先通过新版 Paste 将原库升级后迁移。源数据库持续以只读方式打开。

macOS 14、15 的真实运行与 Intel 真机验证尚待进行。本机 Rosetta 覆盖 x86_64 运行路径，真实 Intel 硬件结果另行记录。

本次构建使用 SDK 15.2，产物无需额外 Swift 兼容动态库。新版工具链引入该依赖时，复制流程和缺库拒绝路径已有代码及夹具覆盖，SDK 26 工具链的实际嵌入结果仍待该工具链构建验证。

卡片阴影已按参数及坐标方向适配，逐像素视觉对齐尚待验收。前轮基线的四项扩展存储回归失败仍保留，详见 `.local/m1-regression/baseline-results.json`。因此本报告记录兼容分支迁移与定向验证结果，整体运行验收继续按上述范围跟踪。

## 文件与日志

主要代码位于 `replica/Sources/PastoCore/OriginalResourceBundle.swift`、`OriginalStackCategoryIcons.swift`、`PasteGroupMigration.swift`、`replica/Sources/PastoObjC/PRPanelGlassBackground.m`、`replica/Sources/Pasto/UI/PanelViews.swift` 以及构建和校验脚本。

原版图标导出脚本为 `scripts/extract_stack_icon_pngs.swift`。原始裁剪目录的历史提取脚本仍保留用于旧证据追溯，当前打包使用 PNG 资源。

日志与实际通用包证据位于 `.local/compatibility-migration/`，包括 `universal-build.log`、`resources-arm64.log`、`resources-x86_64.log`、`paste-import.log`、`import-x86_64.log`、`packaging-tests.log`、`original-model-fields.log` 和 `summary.json`。本地测试包位于 `replica/dist/Pasto.app`。
