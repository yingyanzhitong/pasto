# Paste 原版兼容性处理报告

核查日期为 2026-11-04。二进制样本为本机安装的 **Paste 6.6.6，构建号 29766850**。官方网页用于核对当前支持声明，源码证据来自该样本的反编译输出。

## 结论摘要

Paste 的兼容性由多个层面共同处理。

- 主程序及随包组件提供 Intel 和 Apple Silicon 对应机器码。
- 声明最低 macOS 14.0，并在运行时按系统版本选择 API 和界面实现。
- 新玻璃类采用弱链接，旧系统走 NSVisualEffectView 分支。
- 随包携带 Swift 兼容动态库。
- 应用资源和数据库模型通过 bundle 定位，数据库版本通过元数据校验。

这些结论来自静态检查。报告包含原始检测结果与函数索引，原机跨系统运行情况列在末尾。

## 1. 官方公开说明

官方下载页注明需要 macOS 14 或更高版本。[Paste 官方下载页](https://pasteapp.io/download)

官方迁移帮助说明，当前仍支持符合要求的 Intel Mac，Apple Silicon 可使用原生版本。旧的 Intel 构建可通过安装当前版本更新。[Paste 官方 Intel 与 Apple Silicon 说明](https://pasteapp.io/help/intel-to-apple-silicon)

本次检索得到以上兼容说明。下文为本地二进制和反编译核查形成的技术报告。

## 2. 芯片与随包组件

通过 `lipo -archs` 检查应用包内实际 Mach-O 文件。

| 组件 | 实际包含的架构 |
| --- | --- |
| Paste 主程序 | x86_64、arm64 |
| Paste Helper 登录助手 | x86_64、arm64 |
| paste-mcp-stdio | x86_64、arm64 |
| Sentry.framework | x86_64、arm64 |
| libswiftCompatibilitySpan.dylib | x86_64、arm64、arm64e |

主程序、助手和动态依赖均含 Intel 与 Apple Silicon 切片，保证整套启动链具备相应架构。M1 对应 arm64 切片。

反编译函数 `0x100b33480` 读取 hw.cputype 并识别 x86_64、arm64 等架构，附近源文件路径指向 SentryDevice.m。该证据说明诊断模块会记录硬件架构，其作用范围为设备信息与诊断。M1 专属设置修补逻辑尚未确认。

## 3. 最低系统与 SDK

| 项目 | arm64 | x86_64 |
| --- | --- | --- |
| Mach-O 最低系统 minos | 14.0 | 14.0 |
| 构建 SDK | 26.5 | 26.5 |

Info.plist 的 LSMinimumSystemVersion 同样为 14.0。使用新版 SDK 构建与允许旧系统运行同时成立，具体新功能由版本判断和兼容分支控制。

对当前反编译文本扫描，索引到 **570 个运行时版本检查调用点**，其中主版本条件为 26.0.0 的有 57 个，26.4.0 的有 5 个，15.0.0 的有 406 个。统计包含链接进主程序的 SDK 实现与编译器生成代码，也包含带 variant 参数的调用。此数量用于定位证据，独立功能数量和语义审计覆盖率需要另行计算。

索引中也存在 macOS 14 之前的版本条件。应用的系统支持范围仍以 Info.plist 和两套 Mach-O 声明的 macOS 14.0 为准。

## 4. 人工核实的系统适配

| 范围 | 较旧系统分支 | 新系统分支 | 原版函数证据 |
| --- | --- | --- | --- |
| 背景效果视图 | macOS 26 以下创建 NSVisualEffectView，设置材质、混合和状态 | macOS 26 起创建 NSGlassEffectView，并设置 contentView、圆角 | 0x100220ffc，part-0186.c 第 1445 行 |
| 背景窗口 | 创建 NSWindow 并配置原有效果视图 | macOS 26 起创建 GlassBackgroundWindow，配置玻璃视图和工具栏 | 0x10021dd64，part-0185.c 第 366 行 |
| 主面板背景圆角参数 | 传入 0 | macOS 26 起传入 26 点 | 0x100036104，part-0020.c 第 839 行 |
| 主面板容器边距 | 传入 0 | macOS 26 起传入 8 点 | 0x1000368a4，part-0020.c 第 1118 行 |
| 搜索焦点轮廓 | 6 点圆角 | macOS 26 起使用高度的一半 | 0x100043418，part-0025.c 第 263 行 |
| 卡片阴影 | 一组旧系统透明度、偏移参数 | macOS 26 起采用另一组参数 | 0x1003f26c4，part-0314.c 第 1672 行 |
| Spotlight 内容属性 | 设置已有 textContent 等属性 | macOS 26.4 起额外设置 contentDescription | 0x1002e3b18，part-0240.c 第 276 行 |

通过 `nm -m` 检查两套架构，NSGlassEffectView 都标记为 weak external。它与函数中的系统版本判断共同支撑旧系统加载及回退。

主程序的两套架构还通过 LC_LOAD_WEAK_DYLIB 引用随包的 libswiftCompatibilitySpan.dylib。该项记录打包和链接事实，具体 Swift 兼容库内部行为超出本次人工核查范围。

## 5. 资源路径与数据库版本

### 应用资源

`0x1002fa3d4` 的 Core 模块资源加载器依次准备 mainBundle.resourceURL、bundleForClass.resourceURL、mainBundle.bundleURL 等候选位置，再创建资源 bundle。证据位于 part-0246.c 第 638 行。

设置插图函数 `0x10005d810` 调用 SwiftUI.Image.init(_:bundle:)。对应机器码在 0x10005dd4c 将 bundle 参数 x2 置零，使用默认应用 bundle。反汇编节选保存在 `.local/m1-regression/compatibility/paste-settings-asm.txt`。

### 历史模型

`0x100342fc4` 读取数据库元数据并检查模型兼容。`0x10034c014` 从 Core bundle 定位指定版本 .mom，加载 NSManagedObjectModel，并将用于读取的实体类设置为通用 NSManagedObject。证据位于 part-0269.c 第 255 行和第 5959 行。

应用包中共找到 **20 个 .mom 文件**，分布于多个 .momd 模型目录。这是随包保留历史模型的直接证据。读取或迁移到当前版本需要按实际元数据和迁移分支决定。

## 6. 与本次 M1 反馈的关联

原版在设置、背景和资源路径中的已核实决策依据为系统版本、应用 bundle 及数据库元数据。芯片运行入口由双架构切片提供。

Pasto 已复现的设置闪退发生于资源 bundle 定位，导入失败已复现必需内容关系缺失，同时发现固定安装路径和模型资源名限制。其修复记录另见 `.local/m1-regression/compatibility/report.md`。

这些缺陷与安装环境及数据兼容性有关。反馈者原机的准确触发路径仍需运行证据确认。

## 7. 证据与验证范围

- 已完成两套主程序架构、最低系统、SDK、新玻璃类弱链接和 Swift 兼容库弱加载的静态核查。
- 已枚举随包 Mach-O 架构及历史模型文件。
- 已人工核实表格中的背景、窗口、搜索、阴影、Spotlight、资源及模型分支。
- 570 个调用点的完整索引和原始检测结果保存在同名 JSON。
- Intel 真机及 macOS 14、15 的运行测试尚待进行。该报告的静态结论与跨设备运行验收分开记录。

主程序 SHA-256 为 `7255357661f83d0d10ae8eaedefa64442cb3b1c300d8963ac50cb8547251d9af`。
