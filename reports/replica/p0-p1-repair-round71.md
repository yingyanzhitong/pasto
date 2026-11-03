# 第七十一轮：普通列表 provider 的真实协议调用链

本轮只核对上轮保留的普通历史/分组构造路径，不改应用源码。结论是现有 List→请求→稳定上下文→FRC→UI 消费者可以复用；没有证据支持在这一段额外重写。

原二进制的 conformance descriptor 分别命名为 `ItemRepositoryReading`、`ItemRepositoryWriting`，二者对应同一 `ItemRepository` 类型但使用不同协议表。`3594c0` 实际提供 `eccaa0` 读取协议表；`3bb540` 的普通历史/分组非零 tag 分支调用该表 `+0x10` 槽，目标为 `363d58`，依次构造 `329088` 列表请求、`365db4→365e18` FRC 集合，再做类型擦除。这不是根据相似函数名推断的调用关系。

`365cd8` 中另一个 `+0x10` witness 返回 Core Data 上下文，不能把它认作列表请求工厂。真实 ARM 明确从实例 `+0x20` 取已有请求，再把请求放入 `x2`、上下文放入 `x3`，调用 `initWithFetchRequest:managedObjectContext:sectionNameKeyPath:cacheName:`；后两个参数为 nil，FRC 保存到实例 `+0x28`。Pasto 已由真实 List 构造对应请求并传入稳定 context，共享此前已接的 FRC/delegate/通知与实际 UI 消费者。

12 个原函数片段、4 个 dyld 链指针、2 个协议描述符、8 个直接跳转、14 条 ARM 字及 1 个真实 selector 已绑定。`3b8bfc` 每个 viewmodel 缓存一次集合 wrapper 的字节也已确认，但完整 viewmodel 创建/替换、DI 与 actor 生命周期仍未闭合。`366344` 的同步对象 ID 读取/校对和真实间接消费者是下一处核对重点；不能仅凭初始化入口存在就称其完整等价。

| v14 已确认有限差异 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 92 | 92 | 100% |
| 合计 | 161 | 161 | 100% |

本轮新增差异 0、修复记录 0，不扩充有限分母、不升级 function-map。上述百分比是已确认差异修复率；全模块完成度仍无法证明，04430c/0f733c、任意 history 标识/元数据、pending/cross-process payload、原生模型迁移和完整父合同继续保留。

47 项定向源码/静态检查通过：新增 provider 11 项、顺序列 20 项、FRC 16 项。前轮 1087 项结果保留，相关生产和全部旧测试摘要均未变化；本轮没有重复运行全套，不能称 1087 项重新通过或应用运行回归通过。242 个生产文件、Package.swift、147 个旧测试均未修改，仅增加 1 个静态测试文件及本地审计材料。

执行范围仍为修复 P0→检查 P1→修复 P1，P2/联网不在本阶段。官网 9 文件、应用版本 1.0.2、HEAD、function-map 均保持。未编译、运行框架/数据库/应用、联网、安装、提交或发布，目标保持进行中。

[机器证据](p0-p1-repair-round71.json) · [已确认差异清单](p0-p1-difference-backlog-v14.json)
