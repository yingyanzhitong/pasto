# P0 / P1 第二十一轮代码复查

2026-10-30。继续按用户最新范围只读复查P0/P1。本轮重查6个未闭合地址，补3个有限比较结论；未改218个生产文件、function-map、版本或HEAD，未编译、构建、安装、运行应用/框架、联网、提交、推送或发布。

| 当前暂定清单 | 结果 |
| --- | ---: |
| 明确有限比较结论 | **642 / 646（99.38%）** |
| 有限合同一致 | 491 |
| 明确差异记录 | 142 |
| 用户指定适配 | 9 |
| 未闭合 | 4 |
| P0 | 265 / 265（100.00%） |
| P1新增独立地址 | 377 / 381（98.95%） |

固定v3分母646，9个共享地址只计一次。新增2条差异记录属于同一个reload选区差异来源，不代表两个独立bug；另补1条source可用性有限一致。**此百分比是当前清单的比较结论比例，含未修差异，不是Pasto迁移完成率。** 所有`full_function_migration_verified`仍为false，完整原版优先级分类及完整迁移未证明完成。

## 大差分重载后的选择差异

上轮定位到SnapshotApplier中间层，本轮继续解开四个返回值和真实count消费者：

| 1b5a8c输出 | 真实含义 | ARM构建槽 |
| --- | --- | --- |
| x0 | 删除offset的Set<Int> | fp-0x60 |
| x1 | 插入offset的Set<Int> | fp-0x68 |
| x2 | 移动offset pair的集合 | fp-0x70 |
| x3 | 重载offset的Set<Int> | fp-0x78 |

原SDK调用已从真实Mach-O stub、符号及dyld binding交叉确认：`new.difference(from: old)`、`inferringMoves`、`removals`、`insertions`。删除/插入各自无association时把offset插到对应Int Set；有关联的移除记录插入移动pair Set。ARM返回与消费者寄存器一致，1b9b78阈值只累加前三集合计数。

采用明确的有序逻辑快照输入：

```
old = [oldID]，当前选中oldID
new = [new0, new1, …, new300, oldID]
changedIDs = []
```

301个新ID均不同且不在old中。任何正确difference都必须引入它们；`inferringMoves`不能把与old元素不相等的新ID关联为移动，因此至少有301个无association插入，offset各异，插入集合计数至少301。此推导不要求具体差分算法选出某个最短脚本，也不假设所有其他差分集合恰好为空。

原1b9b78的前三集合计数和大于300，清零四个payload；223430先执行mutation，再进入22be98。这里进一步证明了新数组不是写完却未被读取：

- ItemCollectionView原构造函数通过metadata虚槽`+0xe0 → 22a6d0`，以self和`CollectionViewDataSource` witness安装dataSource。
- witness `eb2708 +0x10 → 06e188`读取`applier.items.count`；mutation已先将新数组写到applier的`+0x10`，所以读到302项。
- 非空reload用静态数组`[0]`重建selectionManager，选择`new[0]`。reload尾部只更新布局/可见cell及选中外观，不替换已初始化的selectionManager。
- applier的后续onChange在本例限定的rawtag0、无pending neighbor/handoff/focus、无重入或用户覆盖域不恢复oldID；card序号刷新也不写选区。
- 当前store/search更新接到`normalizeSelection`，保留仍可见的oldID及primaryID；NativeCollectionHost接收新items后更新布局，没有相同阈值的重选首项操作。因此当前仍选择末尾oldID。

**22be98的此有限同快照输入差异成立；223430真实调用该reload分支，记录同来源差异传播。** 两条记录均绑定`difference_origin = Paste:0x10022be98`。这是源码/静态指令及符号化输入的反例，不是实测301次复制、批量导入或UI运行结果；不覆盖全部增量/移动/删除、SDK内部故障、并发及外部回调行为。

## Provider成功安装后的有限合同

原2e1b54的直接BL位于07d330，属于AppDelegate setup 07d0e0；真实DI解析结果被写入SpotlightIndex.source，后续建议消费者读取同字段。setup可由多个启动/等待恢复路径再次进入，不能声称整个进程只安装一次，也不能从未找到其他直接BL排除任意间接调用。

当前有效updateSuggestions Task在构造Provider后同步消费，捕获store保持到候选计算结束。因此在setup成功、owner存活、有效同步请求且source读取成功的域内，“真实请求能够使用source”记为有限一致。候选值、fetch错误、nil替换、owner销毁及跨setup生命周期不因此判等价，既有来源数据差异不重复登记。

## 两条仍未闭合的入口背景

新解析原`__objc_catlist`及dyld class bind，确认PastePlatform类别确实附加在NSTextView；四个UIKit兼容入口为`attributedText / setAttributedText: / text / setText:`。`setText:`真实IMP是0f72a4，MainActor守卫后调用setString:。这补全了相邻Swift薄setter 0f733c的背景，但没有证明其直接生产调用，也没有把当前独立helper声明当作已接入消费，故仍unknown。

Toolbar普通失焦只撤去第一响应者；inactive来自显式dismiss动画完成。当前非空query维持SearchEditor条件分支，Coordinator跨卸载/重现的历史身份仍缺静态实现证明，不凭缺显式reset判差异。

## 剩余4项

| 地址 | 待证内容 |
| --- | --- |
| 04430c | 可用coder初始化的真实输入与归档消费者 |
| 0f733c | Swift纯String setter及当前对应真实生产消费 |
| 2234e0 | 非nil增量事件的删除/移动/重载索引、选区与滚动结果；四字段来源已证 |
| 2f7d60 | Toolbar inactive与当前Coordinator历史卸载/重建映射 |

当前239个候选边界的0暂缓决定沿用第二十轮，不将其称为全原版全部P0/P1分类完成。搜索模块仍在进行；其他模块的completed仅指当前有限清单比较结论已齐，包含未修差异。

## 检查结果

**329项Python源码/静态检查通过，0失败、0错误。** 本轮15项加此前314项，覆盖完整原片段/current源码摘要、精确机器字节与SDK绑定、四差分槽、DataSource真实count消费、明确符号快照反例、Provider直接调用拓扑、NSTextView category绑定与生产/台账/HEAD不变。源码级反例不执行原二进制，不冒充功能回归或完整ABI等价证明。

- [逐地址记录](p0-p1-review-round21.json)
- [精确静态证据及符号快照](p0-p1-review-round21-static-proof.json)
- [执行计划](offline-migration-plan.md)

目标保持进行中。142条差异记录尚未在本阶段修复，不宣称迁移或一比一验收通过。
