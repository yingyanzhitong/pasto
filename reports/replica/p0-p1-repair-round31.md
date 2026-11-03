# P0/P1 源码修复：第三十一轮

执行顺序保持：先修复 P0，再检查 P1，最后修复 P1。本轮仅处理 P0 历史恢复。

原361ec0先反转输入实体，逐个 Date→NSDate→setTimestamp，然后按列表属性清理，读取首个列表并refresh。旧Pasto在值模型先取完时间，再到持久层统一写timestamp，清理发生在原生setter之前。当前在同一个Transaction及其repository上解析目标，倒序逐项取Date并立即写对应原生实体，再回写值投影、清理和refresh/save；后续通用commit跳过相同timestamp setter。未创建独立context或拆开保存。

失效或已删除ID在原生list/target变化前预检失败；空输入继续直接返回。输入不通过Set去重，重复ID保留次数并共享对应原生对象。尚未保存的值记录保留兼容插入入口，不冒称原361690实体克隆工厂。未改已有数据/品牌、列表关系实现或联网代码。

| 已确认有限差异 | 已修复 | 分母 | 比例 |
| --- | ---: | ---: | ---: |
| P0 | 57 | 69 | 82.61% |
| P1历史依赖 | 8 | 81 | 9.88% |
| 合计 | 65 | 150 | 43.33% |

计既有361ec0有限时序差异1条，分母不变；剩P0 12、P1 73，共85差异及2未知。完整函数迁移仍false。实体Sequence、361690 contains/clone、DI/context生命期、清理的完整原生生命周期、错误与重入未闭合；这些父合同不会随本轮时序修复升级。

502项Python源码/C/Mach-O静态检查通过，新增10项，4个旧测试按实际消费者调整，并用phase31-before保留旧历史检查；Store和Persistence的其他内容有精确复原比较。9个原C片段、190字节原二进制范围、Date两项真实SDK导入和setTimestamp: selector绑定已核对。2个旧生产文件变化，其余225个不变。

有限源码案例：输入A/B/C且各Date不同，原版与当前均为Date C→set C→Date B→set B→Date A→set A→清理→refresh→save；旧实现先取完3个Date再进入后续持久化。该案例仅是源码时序比较，没有执行Swift/CoreData或应用。

数据与删除安全仍为唯一in_progress，继续其余P0实体/归档身份和父合同；P1等待P0。未编译、构建、安装、运行、联网、提交、推送或发布。官网9文件、版本1.0.2、HEAD和function-map保持不变。见[JSON](p0-p1-repair-round31.json)、[补丁](p0-p1-repair-round31.patch)。
