# 第六十八轮：真实 FRC 搜索结果与面板消费者

按P0修复→P1检查→P1修复推进。本轮把实际搜索结果接入长期NSFetchedResultsController，而不是仅创建一个未被显示消费的对象。

SDK返回的原String数组通过Store/Persistence factory创建结果源；空数组为nil。非空源使用稳定view context、既有typed Item默认timestamp降序/batch20请求和nativeIdentifier谓词（保留旧nil-native/key适配），section/cache均nil。初次performFetch错误按原边界终止，成功才持有/安装差分delegate、发布首批ID、订阅同context对象通知。命中数与抓取数不等仅诊断。

差分空值跳过；先applying到旧ID序列，失败或与首section数量不符时按原从fetchedObjects重建。更新/刷新通知仅取Updated∪Refreshed并过滤为当前或pending成员；插入/删除/次序由FRC差分提供。pending保留最新顺序、合并变化ID，仅首次安排弱flush，清槽后再send，允许订阅者重入。

index实际持有源和订阅，以缓存首值更新orderedIdentifiers，后续交付有序IDs和reload IDs；面板按源顺序映射Store DTO，不再用内存筛选后自行排序。真实collection host消费visibleItems和变化ID。取消查询保留原结果，空/失败及storeless新结果取消旧订阅；原SDK查询、错误/取消、索引drain/retry/ack和快照读取合同不变。

此前365e18记录将FRC构造错误与index liveEntries/searchItems错误对照，层次有误。现按SDK结果→360808→365e18→实际显示源对照；36dc00是另一索引读取生产者，记录错误返回空或既有throws均保留，不能将其统一改为fatal。

| v12已确认有限差异 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 90 | 90 | 100% |
| 合计 | 159 | 159 | 100% |

本轮关闭的是365e18有限首次抓取错误边界，支持方法不重复计分；不是整个原函数、搜索模块或全产品100%。04430c/0f733c仍未知；原完整模型/ItemMetadata、DI/actor/ABI、一般history/group源及完整父合同仍partial。原调度witness+8仅确认首次pending调用一次弱flush，当前context.perform为主context调度适配，尚不能声称精确API一致；366344完整dirty-context/ID协调域未外推。CoreData回调、MainActor executor和跨进程payload快照时序没有运行验证。

1054项源码/静态检查通过（新增16）：绑定15原片段、7真实selector、原difference delegate三条runtime方法、3真实通知key导入和15条ARM字，另核本地SDK头文件。定向覆盖fetch失败在delegate前、差分兜底、成员/顺序、pending并集/单次调度/重入、弱捕获/取消及真实UI接线。10旧测试接实际新边界或冻结历史摘要并比当前相关方法；初13断言/1定位、4个遗留转义/历史domain断言和新增消费者名称定位错误日志保留。

低模型只读复核确认实际消费者和核心源码顺序，未发现可证错接；主审补充store是weak，因此storeless结果先取消旧FRC源再写fallback，避免旧源后续覆盖新结果。Swift delegate拼写由ObjC SDK导入规则和原CollectionDifference bridge确认方向，未编译验证。

4生产文件修改、1新增、235不变。官网9文件、1.0.2、HEAD与function-map不变；没有编译、运行框架/数据库/应用、联网、提交或发布。固定清单闭合后继续审完整父合同及未知，目标保持进行中。

[机器证据](p0-p1-repair-round68.json) · [本轮源码补丁](p0-p1-repair-round68.patch)
