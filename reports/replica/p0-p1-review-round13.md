# P0 / P1 第十三轮代码复查

2026-10-30。仅代码比较和Python源码/静态证据测试，不修改应用功能，不编译、运行、联网、提交或发布。

当前暂定清单从489扩为553：此前只作为支持证据引用的64个本地地址经分类纳入，并逐项比较。原488/489=99.80%只适用于旧清单，不能沿用为新总进度。

| 项目 | 数量 |
| --- | ---: |
| 有明确有限比较结论 | 538 / 553（97.29%） |
| 有限合同一致 | 402 |
| 明确差异 | 127 |
| 用户指定适配 | 9 |
| 未闭合 | 15 |
| P0 | 254 / 256（99.22%） |
| P1新增独立地址 | 284 / 297（95.62%） |

本轮新增50项明确结论（37有限一致、12差异、1用户适配）；另外14项仍未闭合，连同原setter共15项。9个P0/P1共享地址去重计一次。差异结论计入比较进度，不计为已修复；有限一致不代表整函数迁移。

新增差异涉及搜索关闭的约束/完成回调、单条fetch的limit/排序、来源采样时点、空白标题清除、候选数据库读取及错误、索引可用性门和fetch失败处理。用户明确要求的面板内分组删除确认单列适配。普通未共享分组删除许可、固定History恢复目标和合法颜色枚举按有限合同核对。

ARM静态证据确认：3ba4d0返回328f38的布尔结果；365e18调用performFetch:失败后进入Never assertion；36dc00释放fetch错误、清错误寄存器并走空数组恢复。没有将Ghidra伪返回类型、Published猜测、相似容器职责或历史迁移标签作为一致证明。

248项Python源码及静态证据检查通过（0失败、0错误），包含之前238项检查及10项本轮检查。218个生产源码文件、function-map及HEAD保持不变；这不是编译或应用回归结果。

## 未闭合地址

| 地址 | 待证边界 |
| --- | --- |
| Paste:0x10006e0dc | 原闭包弱加载 ItemCollectionView；owner 不存在时 no-op，存在时读取并 retain viewModel，再把标题与附加参数交给 0x1003bae08。当前用户路径为 ReplicaUIController.renameItem → state.perform → ClipboardStore.updateItem。 |
| Paste:0x10007d0e0 | 只比较AppDelegate本地suggestion source选择/安装分支。当前SearchEditor按需构造闭包式Provider，来源取自ClipboardStore；原初始化时的source对象经2e1b54写入owner+0x28。现有证据未把原source具体生产者/更新时机与当前各闭包读取点闭合，不能称架构适配或同合同。 |
| Paste:0x1000f733c | 原薄方法桥接Swift String并调用NSTextView.setString:；当前同名extension含相同赋值，但没有已证生产调用。当前search显示用attributed storage，不能据此判该纯String setter已经接线，也不能反推原search必需该setter。 |
| Paste:0x100223430 | 原 sink 回调先执行捕获 callback，然后依据其 param_1 可选值为nil调用22be98、非nil调用2234e0。当前没有对应可选 UI结果参数：searchIndex.identifiers是非optional Set，visibleItems仅在非空查询下对ID过滤、空查询回退历史。round9已证 subject=nil 经355a98变成 Just(emptyArray,emptySet)，这不能证明UI callback 的 param_1=nil；缺该回调参数与当前 SearchIndex结果状态的精确producer映射，故不把两种nil合并。 |
| Paste:0x1002234e0 | 原非nil callback分支更新NSCollectionView的结果/布局/selection；当前NativeCardCollection接收visibleItems并自绘复用卡片。虽然二者承担列表更新职责，但尚未证明原callback参数与当前visibleItems输入来自同一搜索结果生产链，亦未映射滚动/selection副作用，故不据容器职责相似判一致或架构适配。 |
| Paste:0x10022be98 | 原执行reloadData、清可见cells、重新读取dataSource.count、初始化selection、将bounds设为(0,0)并重新layout。当前空结果路径只观察到items/selection清理，尚未证明对应原nil callback触发，也未覆盖reload与bounds/layout副作用；待真实触发映射。 |
| Paste:0x1002e1b54 | 原仅确认setter把optional suggestion-source值写入owner+0x28；该函数本身不能证明属性为Published。当前SearchEditor.updateSuggestions局部构造Provider闭包，但尚未证明该setter的owner/持久属性消费者与当前Provider构造处于同一对象及生命周期合同，也没有同域输入的具体行为反例，故不据此判差异或架构适配。 |
| Paste:0x1002f00dc | 原为indexingAvailable=true后的复杂异步Indexer worker。完整函数含多轮输入/状态集合与Dictionary处理、async task switch、CoreSpotlight结果/错误及复位分支；当前drain另有pending Request、pendingHistory、needsReset、acknowledgements和Task取消。尚未逐字段映射原actor状态/确认时序/错误保留到当前worker，不能以“都是串行index”判一致或差异。 |
| Paste:0x1002fc0ec | 原完整体仅取100371e9c的singleton metadata并通过metadata witness +0x10调用两参数初始化器，随后原样返回param_2。100371e9c对应结构元数据支持，但此处不能仅凭该调用猜测content getter已执行。当前Entry.init eager读取ClipboardItem并组成title/text等字段；缺原initializer witness参数/目标field与当前Entry赋值的一一映射，有限合同未闭合。 |
| Paste:0x100328f38 | 原函数返回控制菜单内容构造的可见性bool；父菜单多处分支以该bool门控菜单项。当前boardTabs为有效Pinboard直接声明重命名/颜色/移动/删除项。原Optional-like输入在合法、实际UI状态下的可达值尚未从生产者闭合，因此不把门控缺失直接判为确定行为差异。 |
| Paste:0x100355874 | 原subject发布provider并switchToLatest到元素/selection publisher；当前query debounced后触发ReplicaSearchIndex，异步ID经store过滤并另行维护selection。两者都有查询结果更新职责，但尚未按有效输入闭合原provider发布、取消/切换时序及selection值与当前worker/consumer的映射，故保留未闭合。 |
| Paste:0x1003594e4 | 原 transaction 容器在 repo 缓存为空时，以容器 context 构造 Repo 并缓存其五字段 existential；命中时复用缓存 Repo。当前 ClipboardStore 持有长期 ClipboardPersistence，后者持有 NSManagedObjectContext 并在 perform/commit 中复用。 |
| Paste:0x10036299c | 有限子合同一致：移除有效rawType==2分组时清除当前关联项的对应分组关系；原完整体另有timestamp optional比较、后续集合/refresh处理，仍未闭合。 |
| Paste:0x1003724f0 | 原完整函数体是大型查询/对象转换路径，包含CoreData/NSString/NSAttributedString、UTType、URL、文件/属性相关分支与多个callback参数；当前searchItems仅按Item.key IN %@解码ClipboardItem并构造Entry。尚未把原形参/field分支逐项映射到当前Entry/searchableItem，尤其不推断其是否经2fc0ec触发lazy content；本合同待主审。 |
| Paste:0x1003b80f0 | 原函数是上下文工厂：rawType==1给标识加0x400... history tag，rawType==2加0x800... pinboard tag；其他类型记录非法type并回退history上下文。当前chooseBoard与visibleItems分别体现board选择和可见项过滤，但尚未证明原tagged context如何映射到当前有效type 1/2查询/过滤入口；不把suggestion候选的UUID转换当作该函数合同，也不推断未支持类型处理一致。 |

## 清单边界

303个新增边界候选来自167个支持地址及142个映射路径候选（重叠6）；本轮纳入64，剩239尚未全部完成边界分类。它们包含编译器/元数据/SDK/联网分支及可能的本地业务函数，不能全部自动排除或纳入。因此553仍是暂定清单，不宣称全部P0/P1函数总量已闭合。

[逐地址记录](p0-p1-review-round13.json) · [清单v2](p0-p1-review-scope-v2.json) · [本轮静态证据](p0-p1-review-round13-static-proof.json) · [边界候选](p0-p1-review-boundary-candidates-v1.json)。第十二轮109差异分组仍是115旧记录的历史清单，并未覆盖本轮新增12条差异。
