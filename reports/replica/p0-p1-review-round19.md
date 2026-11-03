# P0 / P1 第十九轮代码复查

2026-10-30。本轮仅做本地源码、原片段、SDK及本机系统共享缓存的静态读取/比较与Python证据检查。保留已落盘改动，未修改218个生产文件、迁移台账、版本或HEAD，未编译、构建、安装、运行AppKit/应用、联网、提交、推送或发布。

| 当前暂定清单 | 结果 |
| --- | ---: |
| 有明确有限比较结论 | **639 / 646（98.92%）** |
| 有限合同一致 | 490 |
| 明确差异记录 | 140 |
| 用户指定适配 | 9 |
| 未闭合 | 7 |
| P0 | 265 / 265（100.00%） |
| P1新增独立地址 | 374 / 381（98.16%） |

固定v3分母，9个共享地址只计一次。本轮重审11个旧未闭合地址，补5个有限一致结论；不改变既有差异数量。**P0 100%只表示当前265项都有有限比较结论，含未修差异和用户适配，不是P0完整迁移完成率。** 原版全部P0/P1分类与9个暂缓边界仍未闭合，后续若有明确范围地址仍需更新清单。所有full_function_migration_verified仍为false，Pasto完整迁移率不能由本表推算。

## 初始化入口的新实证

此前044aec缺的不是字段初值代码，而是当前真实`usingTextLayoutManager:true`入口是否派发至`init(frame:textContainer:)`。SDK只有声明，本轮继续读取本机macOS **26.2 / 25C56**的AppKit共享缓存，未加载框架执行。

- AppKit Mach-O classlist定位唯一NSTextView，解析其19个方法表；选中五个初始化selector在这些表中各只有一个定义。
- 以多个独立selector名称、方法类型编码及IMP交叉验证共享selector字符串基址，而非把缓存优化后的selector offset误当普通entry-relative指针。
- `initUsingTextLayoutManager:`的IMP `0x18551f924`载入零frame后尾跳selector stub，实际selector为`_initWithFrame:usingTextLayoutManager:`。
- private initializer保留原self，在`0x18551f81c`送回x0，`0x18551f834`经另一个selector stub动态发送`initWithFrame:textContainer:`；调用目标的认证指针由libobjc导出trie绑定到`_objc_msgSend`（`0x18008d800`），与`_objc_msgSendSuper2`（`0x18008da20`）明确区分。
- 原041f9c本来就调用`initUsingTextLayoutManager(true)`，原ObjC thunk044204转到044aec；当前OriginalSearchInputView/SearchEditor真实构造同样使用该入口。因此在当前系统、未替换方法且正常构造成功的域内，frame override生产链接通，其canAcceptFocus、前景色/font默认字典、nil placeholder与super转发有限一致。

该证据不扩张到其他系统缓存版本、方法替换、完整TextKit失败/生命周期。04430c coder仍未闭合：frame入口接通不等于存在coder生产调用，外部归档/系统恢复也不能靠静态无nib检索排除。

缓存没有整份复制或哈希。本轮记录缓存UUID、映射、所用精确字节块与每块SHA，测试再次直接读取并核实；小型Mach-O文件仅为提取指令添加容器头供objdump反汇编，没有编译或执行应用。

## P0的有限成功域

- 3594e4：原owner缓存命中复用已有context-backed repository，缺失时构造并缓存；真实TabBarViewModel/事务回调拿其结果再调用witness。当前有效ClipboardStore持有一个Persistence，后续read/revision/commit经该引用使用同一context。只核已初始化活跃owner内成功访问对象/context的复用，lazy/eager精确时点、多个owner隔离、磁盘错误及全部消费者仍不外推。
- 368250：只核原函数成功提供canonical History目的地后，真实恢复/历史成员消费者对应的语义。原恢复目标为固定History、历史由timestamp表达；当前面板以nil board选择History，成功复制恢复后recordRestoredItems更新isInHistory和时间，列表与清理消费同标记。此结论**不证明原ListEntity工厂的持久化创建、identifier/name/rawAttributes写入、permanentID与编码失败已迁移**。
- 原clipboard属性数值30与当前用户指定7天龄期分列。原capacity完整单位/限制未在本轮证明，不把它称为30条，不作与7天等值的推断。

## 建议菜单的有限空候选域

0403f4/041190只在owner与输入对象存活、caret context有效、当前额外输入门均通过、稳定provider数据/已审query规则得到两侧候选数组确实为空、任务未取消的域内补一致。原selection→context→task链与当前onSelectionChange→updateSuggestions接通；空数组时两侧均移除child window、隐藏菜单并清空owner菜单引用。

不把候选非空但当前chip转换丢弃至空的情况包含进来，不比较全部候选来源、锚点/窗口布局、weak消失与任务取消，也不编造当前同步MainActor provider到show之间的跨await竞态。

## 继续保留的7项

| 地址 | 缺少的证据 |
| --- | --- |
| Paste:0x10004430c | coder入口的真实生产输入与当前消费者 |
| Paste:0x1000f733c | 原/当前纯String setter的真实生产调用，不能由方法存在或有界无引用就判完成/不可达 |
| Paste:0x100223430 | ObservableCollection关联输出到sink callback首参数Optional的类型与寄存器拆分 |
| Paste:0x1002234e0 | 增量结果/选区更新事件与当前items/selection消费者的同触发映射 |
| Paste:0x10022be98 | reload、dataSource count、bounds/layout重置对应当前的确切事件 |
| Paste:0x1002e1b54 | 长期provider owner安装与当前按需Provider生命周期的同域合同 |
| Paste:0x1002f7d60 | Toolbar inactive→mode0 reset与当前Coordinator卸载/重建生命周期映射 |

原结果provider subject nil已经被Map成Just(emptyArray,emptySet)，不能直接称为223430 sink Optional的nil；本轮新增协议witness和sink桥仍未解开其关联输出布局，保留unknown。

## 验证与证据

302项Python源码/静态检查通过（既有292项加本轮10项），0失败、0错误。覆盖原完整片段/当前引用摘要、系统缓存UUID和所用字节块、19个方法表、selector/导出trie的实际派发、有限成功域及生产文件/台账/HEAD不变。它们不是AppKit或Pasto功能回归、原二进制差分执行或完整迁移证明。

- [逐地址记录](p0-p1-review-round19.json)
- [证据索引](p0-p1-review-round19-static-proof.json)
- [本机AppKit共享缓存证据](p0-p1-review-round19-appkit-proof.json)
- [固定清单v3](p0-p1-review-scope-v3.json)
- [执行计划](offline-migration-plan.md)

此前115条差异/109组仍是历史快照，不代表当前140条记录的完整分组。本轮未修生产实现；上轮发现的多项文本索引遗漏等差异仍待后续处理。
