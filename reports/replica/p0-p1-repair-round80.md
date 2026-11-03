# 第八十轮：复制与归组输入不再经过旧缓存过滤

主智能体加一名低模型只读代理批量清点当前消费者，主智能体核对15个实际方法并冻结方法体摘要。先纠正边界：edit/delete/duplicate及ordered assign在change闭包前按持久版本取latestState并merge，版本相同时复用baseline，不能把这些方法笼统说成每次读旧值或每次无条件读盘。其主体保留复用。

本轮修复三处输入/状态适配：

1. 单项copy(item)原先转ID再让writer重查Store，现直接selectedItems:[item]交共享writer。实际Stack复制按钮使用该入口。performCopy的成功反馈/隐藏和全部writer处理/保存失败/Undo/通知时序保持。
2. assign(ids:Set)原先只从缓存items选出ID，缓存未出现的请求ID会在进入事务前丢失。现在保留原缓存顺序，并将未缓存的请求ID按UUID稳定追加，全部交ordered assign。最终存在性与归属操作仍在原事务state内处理，不改有序归组业务。Set是本地兼容API，此排序不冒称原Sequence ABI。
3. prepareHistoryRestore原先用current缓存做availability检查，可能拒绝已在FRC中的新持久条目。现在在既有锁内，仅当revision变化才latestState/merge/validate，再校验ID并建立原native targets；版本未变仍用原local/baseline，无全量read/merge。selected传入内容及顺序不重建；写后继续同一个prepared state/previous/transaction/targets，不增加写后重取输入。

原版补证9个仓库片段，复用7个copy片段，绑定14条ARM、4个dyld指针和2个真实conformance：357cf0给x3传ItemRepositoryProtocol表eccad0，3594e4保留该witness并写入返回existential+20；3ba130读取其关联Writing+10得到ecca50，再经Writing+28→364014→3614c0处理完整输入序列。严格区分两层witness的偏移。这证明仓库服务交付链，仍不等于原UI分组动作的选区producer已对应；后者继续待核，未猜改assignSelection/createPinboard的UI顺序。

| 已确认有限差异 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 93 | 94 | 98.94% |
| 合计 | 162 | 163 | 99.39% |

上述三项属于实时原生输入向现有值存储适配的继续修复，不把3544dc整条关闭。Stack/OCR、其他持久动作的完整实体/DI/模型替换/生命周期、UI分组producer及04430c/0f733c继续开放。完整并发/未保存状态、实际性能与运行行为未执行验证。

1216项Python源码/Mach-O静态检查通过（新增17），覆盖真实单项copy/Set调用点、所有请求ID交付、revision相同不全量读/合并、版本变化锁内更新后校验、选区值/顺序保持、写后prepared操作不变及复用mutation主体。5个旧测试/工具只隔离3个精确方法体变化；原证据摘要未改。首次1199项出现26个旧结构/hash失败，更新准备函数后另1个历史冻结比较失败，日志保留，最终全绿。

245个生产文件中2个修改、243个不变；无新生产文件或schema/Package/AppMain/界面布局修改。官网9文件、1.0.2、HEAD/function-map保持。未编译、构建、框架/数据库/应用运行、联网、安装、提交或发布；目标继续进行。

[机器证据](p0-p1-repair-round80.json) · [有限差异清单](p0-p1-difference-backlog-v16.json) · [源码补丁](p0-p1-repair-round80.patch)
