# P0 / P1 第二十轮代码复查

2026-10-30。按用户最新要求继续只读对比P0/P1及无需编译的源码检查。本轮复核5个未闭合地址及9个暂缓分类边界，保留用户与此前落盘改动；未改218个生产文件、function-map、版本或HEAD，未编译、安装、运行应用/框架、联网、提交、推送或发布。

| 当前暂定清单 | 结果 |
| --- | ---: |
| 明确有限比较结论 | **639 / 646（98.92%）** |
| 有限合同一致 | 490 |
| 明确差异记录 | 140 |
| 用户指定适配 | 9 |
| 未闭合 | 7 |
| P0 | 265 / 265（100.00%） |
| P1新增独立地址 | 374 / 381（98.16%） |

分母固定为v3去重清单646，9个共享地址只计一次。本轮没有把新定位的支持函数或分类决定计入迁移完成；百分比不变。P0的100%只是当前清单均有有限比较结论，包含未修差异。所有`full_function_migration_verified`仍为false，原版全部P0/P1分类和Pasto完整迁移均未证明完成。

## 搜索事件的关键纠正

此前把223430描述成直接接收ObservableCollection publisher的sink，缺少中间层。本轮完整追到实际生产链：

`ItemCollectionView 067c84 → publisher getter 1aeb1c → 22338c → SnapshotApplier 1b8d88/1b8ddc → sink 1b9e54 → 1b8f38 → 1b9040 → 1b912c → 排队/排空 → 1b9b78 → 2234d8 → 223430`。

- 协议descriptor确认关联类型名为`Element`，没有声明名为`Output`的关联类型。具体publisher Output与回调payload布局是另外的问题，不能混用。
- `1b8a94`检查当前MainActor executor，然后同步调用closure；失败时assertion/trap。它不是异步交付。真正的主队列异步排队在`1b9214`。
- applier构造将`+0x58…+0x5b`置零；首次处理检查`+0x5a`，将四个payload寄存器全部置零再调用CollectionView回调。后续比较四字段差分，前三组序列计数之和大于300时也清零四字段。
- 首次mutation closure为`1ba0d8 → 1b9f80`，后续直接使用`1b9f80`。它经`1b9db0`把新数组写到applier的items字段；`223430`先执行mutation，再选择全量reload或增量更新。
- 因而原回调nil表示“请求全量重载”，既不等于原provider subject nil，也不等于空搜索结果。subject nil此前已经过Map转为`Just(emptyArray, emptySet)`，这项事实保持不变。
- 全量reload在新dataSource count非零时，会用静态数组`[0]`重建selectionManager，同时重置scroll bounds。当前normalizeSelection保留仍可见的已有ID。方法状态语义可见，但还需证明同一个有效事件、既有选区及后续callback影响，暂未把它升级为完整同输入差异或已迁移结论。

该链路改变了下一步证据路线：先对照首次应用、超过阈值重载和普通差分的当前消费，不再从“空结果是否直接送nil”反复推断。

## 9个暂缓边界的复核

原239个候选边界中的9个hold，现归为8个支持辅助和1个排除项；整个候选集计数为93纳入、131支持、15排除、0暂缓。**这只关闭既有候选集的暂缓决策，不代表原版全部函数的优先级分类完备。** 非hold的230个旧决定逐项保持不变。

- `04493c`由`InputView.initWithCoder`入口042908直接调用，写默认字段后assertion/trap。旧边界“析构清理”的解释撤回；真正`.cxx_destruct`是042e60。该失败初始化与仍未闭合的TextView可用coder入口04430c是不同路径。
- `19b694`不只依据文件名排除。工厂19b6f0经19cf88获得的metadata，nominal type实为`PasteTelemetry.TelemetryImpl`，属于用户排除的遥测注册。
- `1e7580`是通用快捷键DI包装，保留支持；`1ee744`、`1f0674`实际为4字节尾跳，父样式/状态哈希合同已审，不重复扩充分母。
- `1fec18`、`1ff964`是搜索输入实际消费的颜色once访问与字体辅助，归支持；`043258`为Scroller不支持coder入口，仍只作初始化支持。
- `370984`只是String Set.remove：命中取出并删桶，未命中返回nil。旧笼统“membership/removal/insertion”修正，不因标准集合辅助再登记一个迁移或bug。

## 剩余7项

| 地址 | 继续追查 |
| --- | --- |
| 04430c | 可用coder输入与真实归档消费者 |
| 0f733c | 原纯String setter与当前真实生产消费者 |
| 223430 | 已证applier回调，继续同事件/四字段到当前消费映射 |
| 2234e0 | 差分各字段、索引与选区/位置更新 |
| 22be98 | 首次/超过阈值的全量重载与当前同事件选区/滚动结果 |
| 2e1b54 | 长期optional source与当前按请求Provider的可观察生命周期 |
| 2f7d60 | Toolbar inactive与当前Coordinator历史重建的确切映射 |

当前Provider创建后同步消费，结构不同本身不证明当前请求丢失source；本机公开SwiftUI接口也没有给出条件分支重现时Coordinator身份的完整证明。这两项继续unknown，不把无显式reset或缺同名owner当作差异。

## 验证

**314项Python源码/静态证据检查通过，0失败、0错误。** 包括此前302项与本轮12项：完整原片段/current源码引用摘要、Mach-O精确字节、descriptor/indirect protocol引用、首次与阈值回调、mutation先后、边界保留规则及218文件/function-map/HEAD不变。它们没有执行应用，不能替代UI或完整功能回归。

- [逐地址记录](p0-p1-review-round20.json)
- [精确静态证据](p0-p1-review-round20-static-proof.json)
- [候选边界复核](p0-p1-review-boundary-round20.json)
- [当前执行计划](offline-migration-plan.md)

目标保持进行中；140条差异记录仍未在当前只读阶段修复，不能声称迁移或一比一验收通过。
