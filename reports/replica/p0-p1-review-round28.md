# P0 / P1 第二十八轮复查与修复草案

2026-10-30。当前仍执行人工最新要求的只读P0/P1复查；已异步请求是否切换到源码修复，未收到答复前不应用补丁。没有修改218个生产文件、function-map、版本或HEAD，没有编译、构建、安装、运行应用、联网、提交或发布。

当前对比进度保持**654/656（99.70%）**：500有限一致、145差异记录、9用户适配、2项待证。原函数记录与状态逐项保持不变；草案、清单检查和文件摘要核验均不增加迁移或修复数量。P0当前266条有限结论不代表原版全部P0或迁移完成；P1新增独立388/390，coder/Swift setter仍待证，全量分类未证明。

## 有限源码覆盖清单

| 当前文件 | 显式f_地址声明 | 已在scope v5 | 既有边界支持项 |
| --- | ---: | ---: | ---: |
| OriginalSearchTextView.swift | 15 | 14 | 1 |
| OriginalSearchInputView.swift | 13 | 11 | 2 |
| OriginalSearchField.swift | 15 | 12 | 3 |
| 合计 | **43** | **37** | **6** |

主审逐项检查当前声明行、原完整片段摘要、scope/boundary归属，37项状态与最新第二十七轮canonical记录一致；SearchEditor 7处消费者字面引用和当前文件摘要匹配。构造器和override单独记录，不凭源码注释或行数生成地址。没有发现新业务地址，不扩分母，也不以这三文件推断整个原版搜索库存齐全；coder与不在这三文件中的Swift setter没有因此结案。

## 已准备的第一项修复

[草案说明](p0-save-error-alignment-proposal.md)与[612字节补丁](p0-save-error-alignment.patch)针对已有P0差异37a144：原事务错误释放后继续清Undo并发DidRestore，当前try recordRestoredItems抛出会提前离开。草案仅给这次事务调用加do/catch，保留更早的reload/找不到ID错误、writer流程及当前持久化rollback。

六项草案静态检查通过：当前源码基线、单一精确替换、git apply --check、catch与后续Undo/DidRestore结构、原Swift errorRelease汇合路径、218生产文件/HEAD/台账保持。真实SDK绑定确认37a5b8目标bfc708为_swift_errorRelease，后续继续Undo链。只执行了git apply --check，**补丁未应用**；没有Swift编译或应用执行，草案不算功能已修复。

## 验证口径与下一步

本轮执行6项草案静态检查和43项地址清单/7处消费者核验。上一轮386项Python检查的通过记录沿用，重核了已绑定输入和生产基线，不宣称本轮重跑386项，也不把已绑定摘要说成依赖图穷尽。证据见[草案检查JSON](p0-save-error-alignment-check.json)及[本轮记录](p0-p1-review-round28.json)。

需确认阶段切换的原因是[AGENTS.md第46行](../../AGENTS.md#2026-10-30-最新范围补充p0-与-p1-一并复查)明确“此次扩展不自动恢复修改应用功能”。用户授权修复后按P0→P1处理既有清单，仍不编译、安装、运行应用、联网、提交或发布；授权前继续只读。未把原目标中“修复”的旧表述当作推翻人工最新只读要求。

上一目标轮取得一个新的阶段差异，属于progress；本轮准备并核验了可直接审阅的修复补丁、完成有限源码归属审计，改变后续可执行动作，属于progress。完整迁移目标未完成，仍保持进行中。
