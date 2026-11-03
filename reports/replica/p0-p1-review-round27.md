# P0 / P1 第二十七轮代码复查

2026-10-30。只读原函数、机器字节与源码比对；不修改应用功能、不编译、构建、安装、运行应用/框架、联网、提交、推送或发布。

| 当前暂定清单v5 | 结果 |
| --- | ---: |
| 明确有限比较结论 | **654 / 656（99.70%）** |
| 有限合同一致 | 500 |
| 已确认差异记录 | 145 |
| 用户指定适配 | 9 |
| 未闭合 | 2 |
| P0 | 266 / 266（100.00%） |
| P1新增独立地址 | 388 / 390（99.49%） |

固定656分母，9个共享地址只计一次。P0当前清单都有有限比较结论，**含未修差异，不是完整迁移或原版全部P0完成**。整体百分比是有限比较结论覆盖率，不是Pasto迁移完成率；原版全库存分类仍未证明，full_function_migration_verified全部false。

## 1. 已确认：非plain图片恢复的阶段顺序不同

`383d90`从unclosed改为difference_confirmed，依据为真实生产链中的目录处理和表示解码顺序，而非仅有函数名或推测的故障。

| 阶段 | 原版 | 当前Pasto |
| --- | --- | --- |
| 图像分支入口 | 38222c非plain图像→383d90尾调383df4 | 本地capture分类image→ClipboardItem.kind→普通writeToPasteboard |
| 表示数据与目录 | **先处理images目录，再读实体数据并解码** | **先解码payload返回表示数组，再进入prepare处理目录** |
| Objective-C异常桥 | rawPasteboardItems getter经31b218/2ffc68 | 持久化performAndWait经OriginalObjCExceptionBridge；其后消费Swift值 |

原机器调用已逐条绑定：

```
383fe0 → 384824                images目录处理
38401c → data getter           目录可选结果的一条支线
38402c → 31b218 → 31aeec       表示解码
3840d4 → data getter           另一条支线
3840e4 → 31b218 → 31aeec       表示解码
```

当前writeToPasteboard中ordinaryRestoreRepresentations先调用originalPasteboardItems/31aeec，正常返回数组（含空数组）后才进入imageRestore.prepare；后者经383df4/384824处理目录。该次序在reload快慢路径上都成立。

**没有把“当前缺少Objective-C异常捕获”作为差异。** 当前ClipboardPersistence.perform明确在context.performAndWait内调用OriginalObjCExceptionBridge.withResult。reload还存在`local==baseline && revision==diskRevision`的快速返回，不能说每次复制都完整重读Core Data；只有需要合并的路径才读取持久层实体。确认的是目录处理与表示解码的阶段顺序，不证明普通PNG内容不同，也不声称两侧同一个Core Data fault已复现。

新差异以383d90为自身来源，不因“提前/延迟读取”等词语与索引模块的其他差异强行归并。此前383df4记录只比较已供给表示的有限图像值处理，仍保留其范围；它不证明本轮上游解码阶段相同。

## 2. 保留的有限值合同

- 有效PNG、稳定来源名/时间、目录与写入成功时，本地采集→分类→kind→普通图像准备的单/多项表示顺序、写PNG与附加fileURL语义可对应。当前临时root是隔离适配，不声称绝对路径相同；同名多项覆盖规则也未误称每项独占文件。
- getter正常返回有效空表示数组时，两侧传空表示给writer，clear后writeObjects([])。这不同于没有字符串、没有选择或getter异常。
- 取到Data但序列化解码失败时，31aeec和当前codec回[]；显式container不回填legacy display text。不据此把ObjC getter NSException当作decode失败。
- text/link使用bit1（掩码2）的plain选项，其它类型用bit0（掩码1）。原机器cmp5/cmp4、tbnz/tbz与当前usesPlainProjection对应；28个静态type/options组合已检查。plain文本getter保留空字符串、丢弃nil文本，不把两者混为一类。

这些有限值结果不抹去新的阶段合同差异，也不构成完整函数/父流程迁移证明。原成功History图片“准备读旧timestamp、写板后事务更新时间”的前轮纠正继续有效。

## 3. 差异清单与验证

当前[差异清单v3](p0-p1-difference-backlog-v3.md)为**145条记录、132保守组**（P0 64条/59组，P1新增独立81条/73组）；旧144条记录逐项保留，仅加入383d90。组数不是独立bug数、已修数量或迁移分母。v1/v2冻结保留；v3使用独立冻结的差异记录快照，并由检查与最终report逐项比对，避免测试结果写回使来源摘要循环失效。

**386项Python源码/静态检查通过，0失败、0错误。** 沿用378项并新增8项，验证实际BL、原机器块、当前解码-before-prepare顺序、reload fastpath、现有异常桥、28个静态选项组合及145条差异快照。它们不是应用执行或图像故障回归。

218个生产文件、function-map、版本和HEAD保持不变。仍待证P1 `04430c` coder输入和`0f733c` Swift setter声明/消费绑定；原版全部P0/P1分类仍非全量保证，145条应用功能/代码阶段差异未修复。目标继续进行，下一步回P1入口与剩余分类边界。

上一目标轮为progress：补真实getter和成功恢复时间链；本轮以真实阶段调用顺序取得一个有限差异结论并更新当前差异清单，同样为progress，未宣称目标完成。

[逐地址记录](p0-p1-review-round27.json) · [静态证据](p0-p1-review-round27-static-proof.json) · [清单v5](p0-p1-review-scope-v5.json)
