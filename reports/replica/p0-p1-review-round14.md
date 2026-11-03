# P0 / P1 第十四轮代码复查

2026-10-30。当前仅代码比较、原片段/ARM静态分析和Python源码检查；本轮不修改生产源码、迁移台账或版本，不编译、运行、联网、安装、提交或发布。

| 当前暂定清单 | 结果 |
| --- | ---: |
| 有明确有限比较结论 | **595 / 646（92.11%）** |
| 有限合同一致 | 457 |
| 明确差异 | 129 |
| 用户指定适配 | 9 |
| 未闭合 | 51 |
| P0 | 259 / 265（97.74%） |
| P1新增独立地址 | 336 / 381（88.19%） |

9个共享地址只计一次。本轮从553项补纳93个独立本地函数，逐项记录比较结果；另复查5个已有地址，补齐其中4项有限结论。新增有限结论57项，包括52项新地址有限一致、1项新差异，以及4项旧未闭合项的有限结论。分母补齐后百分比重算，旧97.29%仅适用于原553项清单。

以上是比较结论比例；差异判明不表示已经修复，有限一致不表示整函数完整迁移。全部记录的full_function_migration_verified仍为false，完整P0/P1迁移率仍未知。

## 本轮关键复核

- 普通分组移除的关系清除、历史内容保留和孤立内容删除，在合法单归属本地输入域有限一致。ARM确认原尾部批量刷新只在History(rawType=1)执行，普通分组跳过。
- 有效History/分组上下文映射已追到集合模型；非法原生类型回退、nil列表和结果成员/排序不外推一致。
- 原AppDelegate安装的候选源已证为CoreDataSuggestionDataSource(viewContext)。当前候选闭包读取内存快照，读取阶段/fetch错误域差异沿用已证父链。
- 新确认搜索scroller初始化的focusRingType不同：原raw2=exterior，当前none=raw1。枚举值由本地SDK头文件核实；本轮未修改样式。
- 撤回两项子智能体初稿误报：原清除图标同样fallback到questionmark.square；原token安全归档错误同样释放error、清错误返回寄存器并输出Optional.none。不能单凭Ghidra的willThrow标记判断错误向外传播。
- attachmentBounds的nil及有效view分支、CGRect四返回值已由ARM核实：无view返回zero；有view返回(0,-0.25*h,w,h)。
- NSPersistentStoreRemoteChange在本链是本地Core Data历史通知；纠正其被误归联网的范围分类，并纳入独立的本地处理函数。纯continuation/转发帧作为父链证据保留。

## 边界与未闭合项

此前剩余239个边界候选均建立了范围决策：93纳入、123仅作支持、14排除、9暂缓。支持项和排除项不计为完整迁移，暂缓项继续保留。范围仍从已有证据/映射/父链扩充，不能声称原版所有P0/P1函数已分类完毕。

P0未闭合地址：

| 地址 | 待证合同 |
| --- | --- |
| Paste:0x100004ab8 | 捕获管理器闭包从weak owner读取捕获状态字段，owner nil返回false；owner存在读取状态并调用0x10037aa10后反转bool。当前AppMain仅依据capture.pollTimer==nil返回bool。两者字段/副作用能否对应未证：当前引用只读Timer属性，无poll action触发证据，故不能按属性名认定替换。 |
| Paste:0x100024274 | 薄动作调用3c5408，后者按CoreData count选择确认或直接清除历史。当前clearHistory按内存中非删除history计数选择NSAlert/直接eraseHistory。原count predicate及最终清理consumer尚待逐项对应；只看到相同职责不足以判一致。 |
| Paste:0x10006e0dc | 原闭包弱加载 ItemCollectionView；owner 不存在时 no-op，存在时读取并 retain viewModel，再把标题与附加参数交给 0x1003bae08。当前用户路径为 ReplicaUIController.renameItem → state.perform → ClipboardStore.updateItem。 |
| Paste:0x1001f06f8 | 原录制器构造注入shortcut、检测/验证闭包并初始化状态及监控资源；当前OriginalShortcutRecorderView用Binding创建model，但本轮未逐项验证初始未分配、validator错误、callback回写和资源安装/释放。 |
| Paste:0x1003594e4 | 原 transaction 容器在 repo 缓存为空时，以容器 context 构造 Repo 并缓存其五字段 existential；命中时复用缓存 Repo。当前 ClipboardStore 持有长期 ClipboardPersistence，后者持有 NSManagedObjectContext 并在 perform/commit 中复用。 |
| Paste:0x100368250 | 原先按固定identifier fetch既有History，缺失才插入ListEntity，设置name/identifier，申请permanentID后JSON attributes及rawType=1。当前history由State.preferences与Item.inHistory表达，没有对应ListEntity创建consumer；完整创建/失败副作用尚未证明映射。默认保留周为用户指定值，不将这一已授权偏好差异单独冒称完整构造适配。 |

P1另有45项未闭合，主要是完整搜索建议/输入构造、结果applier及取消生命周期、本地history错误/状态、Stack预览和富文本编辑父合同；完整逐址内容见JSON。既有孤立setter0f733c仍未接通真实当前生产消费者，继续保留未知。

## 验证与产物

257项Python源码/静态证据检查通过，0失败、0错误。218个生产源码文件与本阶段起始摘要一致，function-map与HEAD保持不变；已有用户/此前落盘改动全部保留。检查覆盖新范围与逐址摘要、真实字面引用、原ARM门控/错误恢复、图标常量、SDK枚举和统计；不代表编译成功或应用功能回归。

[逐地址记录](p0-p1-review-round14.json) · [清单v3](p0-p1-review-scope-v3.json) · [239项边界决策](p0-p1-review-boundary-round14.json) · [静态证据](p0-p1-review-round14-static-proof.json)。第十二轮差异分组是115个旧记录的历史整理，并未覆盖当前129条差异。
