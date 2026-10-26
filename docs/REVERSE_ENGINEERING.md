# 反编译研究记录

本文保留项目改版前的研究说明，命令从仓库根目录执行。软件介绍与当前版本请看[项目首页](../README.md)。

# Pasto 原生剪贴板与反编译研究

`replica/` 现包含可编译运行的 Swift/AppKit/SwiftUI 菜单栏应用 **Pasto**，以及独立的 stdio MCP 服务。原版参考为本机 Paste 6.6.6，复刻使用独立应用标识和数据目录。

```sh
bash replica/scripts/build-app.sh
open 'replica/dist/Pasto.app'
```

需要 macOS 14+、Apple Silicon 与 Swift Command Line Tools。本机已用 Swift 6.0.3、macOS 26.2 实际构建；0.7.0 历史交付曾运行，当前迁移快照仅编译及静态核对。构建只依赖系统框架，不需要下载第三方 Swift 包。

已实现底部横向卡片面板、剪贴板监听、多格式保留、搜索筛选、Pinboard、编辑预览、删除恢复、Stack、归档导入导出、设置、全局快捷键和 MCP 项目读写。原版工具名称、主要参数和关键分支优先由 REA 伪代码及公开资源核对；界面使用实际原版窗口作对照。

当前交付是可运行的独立实现，**尚未达到全功能一比一验收**。联网同步、原厂账号和付费解锁按用户要求排除；本地编辑、输入交互、恢复副作用及系统直接粘贴授权后的完整跨应用矩阵仍未完成对照。不能用反编译覆盖率或测试通过数替代等价性结论。运行与验证方法见 [replica/README.md](../replica/README.md) 和 [测试范围](../replica/TESTING.md)。

按用户要求，复刻免费使用，不依赖原厂账号，不实现联网同步和付费解锁。现改为[逐函数实现与验证](../replica/FUNCTION_IMPLEMENTATION.md)：[完整地址台账](../reports/function-implementation/summary.json)覆盖 81,134 个本地地址，单独记录待处理、部分实现、已有实现、双端等价验证及有理由的范围排除。现有模块或反编译成功不自动计为逐函数完成。

按最新要求，先对已有功能集中核对并直接复用，只补真实差异，见[既有功能集中核对报告](../reports/replica/fast-coverage-audit.md)。功能覆盖与二进制地址计数分开，静态核对不等于一比一验收。

0.7.0 历史快照曾有十三个函数通过 336 个原版机器码直接差分用例；源码修改后，相应记录按摘要失效转为历史。当前数量以台账为准，不沿用旧的 81,121 个剩余数。按用户要求，全部范围内迁移完成前仅编译及静态对照，之后统一功能回归；不运行 MCP 测试。

## REA 静态研究

使用 [REA](https://github.com/morluto/rea) 6.7.0 和 Ghidra 12.1.4，对本机安装的 Paste 6.6.6（29766850）进行 arm64 静态分析和批量反编译。

输出是由机器码恢复的 **C 风格伪代码**，包含优化后的控制流、未恢复的符号和反编译器警告，不是原始 Swift 工程，也不能直接编译为 Paste。

## 导出结果

2026-10-22 的三个目标共尝试反编译 81,134 个 Ghidra 识别到的本地函数，成功生成 81,132 个函数的伪代码，失败 2 个；计数包含本地跳板。主程序 `Paste` 成功 80,703 / 80,705 个，`paste-mcp-stdio` 成功 221 / 221 个，`Paste-Helper` 成功 208 / 208 个。

失败地址为 `0x100ac35f8`、`0x100ac746c`，Ghidra 报告 `Unable to find unique hash for varnode`。这两个地址另附 LLVM 汇编片段，仍计为伪代码生成失败，详见 `reports/Paste/assembly-fallbacks.json`。

## 内容

- `decompiled/`：三个目标的函数伪代码，每 64 个待处理函数一组。
- `decompiled/Paste/failures/`：两个失败地址的汇编片段，不保证等于完整语义函数体。
- `reports/<目标>/function-index.json`：已导出函数的地址、恢复名称、文件与行号。
- `reports/<目标>/procedures.json`：完整已识别函数清单，含外部声明与跳板标记。
- `reports/<目标>/coverage.json`：成功、失败、排除范围和引擎限制。
- `reports/analysis.md`：分析方法、可观察模块与限制。
- `reports/native-dispatch.json`、`reports/objc-classes.txt`：Objective-C 元数据与解码后的类名。
- `reports/function-starts.json`：Mach-O `LC_FUNCTION_STARTS` 条目数，作为独立参考。
- `reports/target-manifest.json`、`reports/toolchain.json`：目标和工具版本、SHA-256。
- `scripts/`：本地副本提取、REA MCP 批量导出和产物校验脚本。

原始安装包、二进制副本、完整 REA Evidence、引擎与日志只保存在被 Git 忽略的 `.local/`。本仓库不包含剪贴板历史或用户账号数据。

## 复现

需要 macOS Apple Silicon、Xcode Command Line Tools、Python 3.9+ 和受 REA 6.7.0 支持的 Node.js（本次使用 24.12.0）。需要自行安装待分析版本的 Paste；不同应用版本或 Ghidra 分析结果会产生不同输出。

1. 安装固定版本的 REA：

   ```sh
   mkdir -p .local/tools
   npm install --prefix .local/tools --no-audit --no-fund rea-agents@6.7.0
   ```

2. 从官方 [Ghidra 12.1.4 发布页](https://github.com/NationalSecurityAgency/ghidra/releases/tag/Ghidra_12.1.4_build) 和 [Temurin JDK 21 发布页](https://github.com/adoptium/temurin21-binaries/releases/tag/jdk-21.0.12.1%2B1) 下载 macOS arm64 工具。本次安装位置：

   ```text
   .local/tools/ghidra_12.1.4_PUBLIC/
   .local/tools/jdk-21.0.12.1+1/Contents/Home/
   ```

   `reports/toolchain.json` 记录实际使用的下载归档哈希。已有安装可通过 `GHIDRA_INSTALL_DIR`、`JAVA_HOME` 指定。

3. 从仓库根目录加载环境，并为缺少 macOS 原生反编译器的官方包编译 arm64 组件：

   ```sh
   . scripts/env.sh
   (
     cd "$GHIDRA_INSTALL_DIR/Ghidra/Features/Decompiler/src/decompile/cpp"
     make -j4 ghidra_opt ARCH_TYPE="-arch arm64" OSDIR=mac_arm_64
     mkdir -p ../../../os/mac_arm_64
     install -m 755 ghidra_opt ../../../os/mac_arm_64/decompile
   )
   node .local/tools/node_modules/rea-agents/scripts/rea.mjs doctor --provider ghidra --json
   ```

4. 提取本地分析副本并导出：

   ```sh
   python3 scripts/inventory.py /Applications/Paste.app
   python3 scripts/decompile.py
   python3 scripts/verify.py
   ```

   可以只分析一个目标：`python3 scripts/decompile.py Paste`。脚本只连接自己启动的 REA stdio MCP 进程，不需要修改 Codex 的全局 MCP 配置。Ghidra 首次导入耗时较长；`.local/<目标>/batch-*.json` 支持相同目标哈希、相同分析配置、相同函数列表的批次复用。超过 REA MCP 10 MiB 消息上限的结果会通过 `export_evidence_bundle` 导出后完整读取，不截断函数清单；该恢复路径已实际验证。`verify.py` 检查导出计数与索引的一致性，不证明反编译语义正确。

原生元数据可另行提取，完整 Evidence 写入本地目录：

```sh
node .local/tools/node_modules/rea-agents/scripts/rea.mjs inspect-macho .local/targets/Paste.arm64 --json > .local/paste-macho.json
node .local/tools/node_modules/rea-agents/scripts/rea.mjs inspect-native-dispatch-metadata .local/targets/Paste.arm64 --json > .local/paste-native-dispatch.json
```

## 阅读与限制

通过 `reports/objc-classes.txt` 和 `native-dispatch.json` 中的类型/selector 定位实现地址，再用 `function-index.json` 查伪代码。`FUN_...` 名称表示原名称未恢复，`undefined` 表示类型恢复有限。

覆盖率的分母是 **Ghidra 识别到的本地 arm64 函数**，不包含外部动态库实现，不等于所有原始源码或所有机器码路径。主程序 `LC_FUNCTION_STARTS` 的 74,585 个条目不作为 Ghidra 函数覆盖率的分母，也不表示已反编译函数数。原生元数据恢复存在 `partial` 和 `unsupported`，具体见报告。未进行动态业务验证，未分析 x86_64 副本。

版权与产物性质见 [NOTICE.md](../NOTICE.md)。原应用及其依赖保留各自权利，本项目不代表原厂。
