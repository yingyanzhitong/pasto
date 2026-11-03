# 第七十三轮：确认实时内容 provider 尚未迁移

本轮确认一条新的 P1 差异，尚未修复：原 FetchedResultsCollection 在读取条目时，按真实 NSManagedObjectID 向当前 Core Data 上下文解析托管对象，再检查泛型实体类型。Pasto 目前仅由 FRC 提供有序 UUID 和变化 ID；普通列表、搜索两个实际 visibleItems 分支仍用 UUID 匹配 Store.items 值快照，host.update 再消费这些 DTO。当前 FRC 的 existingObject 调用只用于发布 UUID key，不是实时内容提供者。

原 conformance descriptor 的间接协议指针确实指向 ObservableCollection，类型描述符命名为 FetchedResultsCollection；6 个 dyld 指针与类型擦除 trampoline 已绑定：协议表 +0x20 经 3543e4/35440c 按索引查找，+0x28 经 3544b0/3544dc 按 ID 查找。原 FRC factory 通过该 conformance 做类型擦除，真实 ItemCollectionView 安装由此集合提供的 applier。这里证明了源协议路径；不冒称已绑定所有原 UI 间接条目调用处。

两条错误合同需要分别保留：按 ID 读取遇 existingObjectWithID:error: 失败或 expected class 不符时返回 nil；按索引读取遇负数、越界或对应对象缺失时触发 trap。不能用统一 compactMap 把 indexed 错误也吞掉。真实 selector、dynamicCastUnknownClass 与 swift_errorRelease import，以及 14 条 ARM 字证明这些分支。

该差异证明当前顺序源和内容源分离；没有运行应用或复现陈旧内容，不能称已观测跨进程故障。下一步修复需要同时接入实际渲染、选区和复制等动作消费者，保持原版按需读取。单加一个未使用 getter，或在每次 SwiftUI 重绘时解码全部历史载荷，都不能作为本缺口的完整迁移。

| v16 已确认有限差异 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 93 | 94 | 98.94% |
| 合计 | 162 | 163 | 99.39% |

v16 原样保留 v15 的 162 条/146 组，仅新增 3544dc 一条共享 provider 缺口。索引/类型擦除支持函数不重复计分；本轮新增修复数为 0，原版完整函数标记不升级。04430c/0f733c、完整源切换/DI/ABI/metadata、原生模型迁移与全部 P0/P1 父合同仍未闭合。

本轮静态绑定通过：14 原函数片段、6 个链指针、14 ARM 字、1 selector、2 import 和本地 SDK 头，并正向确认当前普通/搜索字典投影、FRC key-only 使用及真实 host.update 消费者。242 个生产文件及 150 个 Python 测试文件均未修改；前轮1112项结果保留、输入摘要不变，本轮未重跑全套。旧检查主要覆盖排序和发布，并不能由其绿色结果证明实时内容已迁移。

官网9文件、版本1.0.2、HEAD/function-map均保持；未编译、运行框架/数据库/应用、联网、安装、提交或发布。目标继续进行，当前不需要用户处理。

[机器证据](p0-p1-repair-round73.json) · [差异清单v16](p0-p1-difference-backlog-v16.json)
