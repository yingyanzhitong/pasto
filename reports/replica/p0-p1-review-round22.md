# P0 / P1 第二十二轮代码复查

2026-10-30。仅只读复核P0/P1、原指令/伪代码和无需编译的源码检查。本轮重查3个未闭合地址，补2个有限差异结论；未改218个生产文件、function-map、版本或HEAD，未编译、构建、安装、运行应用/框架、联网、提交、推送或发布。

| 当前暂定清单 | 结果 |
| --- | ---: |
| 明确有限比较结论 | **644 / 646（99.69%）** |
| 有限合同一致 | 491 |
| 明确差异记录 | 144 |
| 用户指定适配 | 9 |
| 未闭合 | 2 |
| P0 | 265 / 265（100.00%） |
| P1新增独立地址 | 379 / 381（99.48%） |

固定v3分母646，9个共享地址只计一次。**比较结论比例包含未修差异，不是迁移完成率。** 全部`full_function_migration_verified`仍为false；原版全部P0/P1分类的全量性与Pasto完整迁移未证明完成。

## 1. 集合快照移除选中项的选区差异

明确输入为old=[A,B,C]、选中B，new=[A,C]，仅删除offset 1；无插入/移动/重载，原applier已处理过old。两侧owner存活、无pendingFocus/handoff/neighbor/重入或额外用户选择，当前`allowsEmptySelection=false`。

原差分计数为1，走nonnil增量链223430→2234e0。新数组先由mutation写入applier，cellCount由3减为2。选区处理路径为：

1. 2258ac把旧选中offset构造成(kind:0, old:1, new:1)记录。
2. 1b2a0c按删除、插入、移动、重载的顺序变换。删除集合含1，1b2a90将该记录标成kind=1；其他集合为空，不产生替代选中记录。
3. 223f2c过滤kind 1/2，得到空选中offset数组；2234e0将空数组、cellCount=2、empty标志写入selectionManager。
4. 后续228f6c仅刷新cell选中外观；已初始化的空数组不会被lazy getter当作nil重新填成首项。原onChange在上述条件下也不覆盖选区。

当前`normalizeSelection`先去掉不可见B，因选择为空、默认不允许空选区且仍有visibleItems，回退选择首项A。**2234e0此有限同快照输入域记为difference_confirmed。**

该结论是传入集合更新的状态差异，**不是两端UI删除命令的完整结果**。UI删除操作可能另设pending neighbor或调整allowsEmptySelection，本轮明确排除这些覆盖，不外推到所有删除/移动/多选场景。

## 2. 清空按钮会丢掉当前撤销历史

本轮纠正此前一处解释：原2f7d60使用的DAT_101057918来自2ddf4c，它把真实dyld导入`__swiftEmptyArrayStorage`写入该全局；**它是空查询常量，不是当前Published query**。

- mode0和mode1都先调用2f7744(empty,0)，清空query。
- mode1随后直接返回，跳过额外的全量history reset。
- mode0才调用2f6550，清undo/redo/pending/timer。

不能把mode1描述为所有history字段原样不变：在非restoring且query变化时，2f7744会调用2f5e18(immediate:true)，flush pending、把旧current追加到undo，并清redo。正确说法是**mode1不额外清除可撤销的先前内容**。

清空按钮的实际消费者链已经接通：

```
原：InputView.clear → SearchField.onClear(false)
    → SearchBar桥041bf0 → 040c64 → 2f7d60(mode:1)

当前：InputView.clear → OriginalSearchField.onClear(false)
      → SearchEditor.clearInput(preserveHistory:false)
      → history.f_1002f6550()
```

原SearchBar闭包显式使用mode1，不能把底层onClear传入的false直接解释成reset函数的mode0。当前把该false作为preserveHistory参数，最终清空undo。

在非空query、已有历史、非restoring、同一活跃Coordinator且无重入的输入域，两侧query都清空；原undo保有旧query快照，当前undo为空。因此**2f7d60记录有限差异**。这是源码级历史状态反例，没有运行应用或实测Command+Z；一般blur、Toolbar关闭/重建、redo/timer完整行为不由此得出。

旧轮报告保持冻结；当前逐地址记录及本报告明确撤回“原inactive保留当前query”的解释。

## 3. URL文本setter的真实别名消费者

新追到原LinkItemContentView在有效URL编辑分支调用3e944c，其lazy textView工厂3e836c明确分配NSTextView。3e9530经真实selector stub c0e0e0发送`setText:`，selector slot f8a440对应该名称；原NSTextView类别把它映射到IMP0f72a4，最终调用setString:。当前本地link preview编辑也把非nil URL写入`textView.string`。

这证明了本地URL编辑的ObjC别名消费者，仍**没有证明待审Swift入口0f733c本身的生产调用**，也没有元数据证明它与ObjC IMP为同一声明，故不把别名的结果升级成该函数已迁移。

## 剩余2项与下一证据路线

| 地址 | 缺口 |
| --- | --- |
| 04430c | 可用coder初始化的真实归档输入及当前消费者；不能用frame初始化接通代替 |
| 0f733c | Swift String setter的真实入口消费；目前只接通ObjC setText别名链 |

继续检查归档/初始化消费者及Swift/ObjC入口关联元数据。无引用扫描只提供定位边界，不证明不可达；不将方法声明存在当作完成。239个既有候选边界0暂缓不代表原版全部函数已经分类。

## 验证与产物

**341项Python源码/静态检查通过，0失败、0错误**（此前329项加本轮12项）。本轮覆盖完整原片段/current源码摘要、精确机器字节、真实dyld empty-array/objc_msgSend绑定、选区变换链、mode分支、当前clear按钮传参、两个明确符号输入反例及218生产文件/台账/HEAD不变。没有执行原二进制、应用或SDK框架，不替代UI/功能回归或完整迁移验收。

- [逐地址记录](p0-p1-review-round22.json)
- [静态证据与符号反例](p0-p1-review-round22-static-proof.json)
- [执行计划](offline-migration-plan.md)

目标继续进行，144条差异记录未在当前只读阶段修复。
