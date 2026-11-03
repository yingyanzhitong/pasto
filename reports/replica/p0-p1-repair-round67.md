# 第六十七轮：稳定主列表上下文与私队列读取

按P0修复→P1检查→P1修复执行。P0有限已确认差异69/69已修，P1检查已完成，当前继续修复P1搜索与筛选。

读取原先共用主view/writer上下文，read/revision/search会reset，不能直接在该上下文接长期FRC。本轮将六个读取入口及history事务/identifier读取接到同协调器私队列ClipboardSnapshotReader；主列表/写入/观察上下文不再reset。原查询、严格时间边界、native/local ID区分、数据投影和错误处理保留，索引读取失败仍记录错误返回空，不能误改成FRC初始化失败的assertion。纯DTO投影静态共享；三个托管快照增加defer reset，history每批前reset，避免旧注册对象进入后续ID解析。

原35cc80明确viewContext设置automatic merge及storeTrump，370e8c创建raw1私队列history context；真实selector和dyld导入已绑定。主上下文按该策略配置；revision变化时从独立内存游标读本地history、顺序merge每笔objectIDNotification，全部完成后才推进游标并缓存revision；抓取失败保留原游标/revision。自身commit业务/save顺序不变，仅成功save后在既有Store锁内更新内存cursor，避免重复回放自身写入。此history/revision桥为Pasto现有模型的本地适配，不是原厂容器/actor/DI或ABI完整等价。

OriginalSearchHistory仍是MainActor消费者，调用私队列reader获取事务和标识；变更reducer、删除tombstone、consumer成功后全局indexHistoryTokenData推进、取消/错误及通知stream生命周期保持。只读复核先指出共享reader旧注册Item风险，已补reset；最终按SDK头证实transaction/token是NSObject值而非managed object，未发现静态可证的新问题。未执行CoreData通知、并发或数据库回归。

| v12有限差异清单 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 89 | 90 | 98.89% |
| 合计 | 158 | 159 | 99.37% |

本轮只推进365e18前置条件，不增加计分。真正FRC初始化/差分delegate/subject/搜索结果消费者尚未接入，另有04430c/0f733c未知；父合同继续partial，不代表全量原函数或模块完成。

1038项源码/静态检查通过（新增15）；9原片段、5份本地SDK头及真实selector/GOT绑定。17旧测试接实际wrapper/私队列producer，或冻结原阶段hash并比较当前相关方法；新测试明确限定projection qualifier、defer reset、成功save后cursor尾部等允许变化，不拼造Swift实现。初旧31项shape/hash失败和测试解析/定位错误日志保留。3生产文件修改、1新增、235不变。官网9文件、1.0.2、HEAD、function-map不变；不编译、不运行框架/数据库/应用、不联网、不提交或发布。

[机器证据](p0-p1-repair-round67.json) · [本轮源码补丁](p0-p1-repair-round67.patch)
