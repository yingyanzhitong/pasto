# 第六十五轮：所选列表属性观察与可见卡片刷新

原3b9264/3bb7bc的有限观察缺口已接入真实生产：非搜索列表创建CurrentValueSubject，初始值由所选托管ListEntity.rawAttributes解码；通知以context为对象、objectID为筛选，按insert0/update2/delete1/refresh3分派，删除跳过，其余读取通知中当前对象的属性。weak observer仅投影并保留subject，再由静态函数解码/send，不跨send持有observer。输出按语义Value?去重。

实际host在初装/替换列表时取消旧订阅并建立所选history/group源，搜索和Pasto最近删除兼容视图不建立该源。订阅跳过初值，后续强制移除、失效渲染签名并重新铺排可见卡片，不重置items、选区或applier。原consumer经ARM确认为07660c→0687d4→虚槽+278→22c22c→221d34(1)；子审初次提及的06869c→Sidecar属于相邻另一条订阅，已纠正。

旧全局store.objectWillChange只转发UI失效，数据尾改为items/sourceApplications/list-ID集合变化去重后触发；纯分组颜色、名称和偏好不会再异步refreshSearch/normalizeSelection。渲染通过匹配的观察源、稳定objectID与context重新读取rawAttributes，既能看到通知早于StoreState发布的新值，也避免Pasto快照read/reset后的旧缓存。getter自身不发布reset事件，重绘依赖已有UI invalidation；未merge的跨进程写入不保证新值。

| v12有限差异清单 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 88 | 90 | 97.78% |
| 合计 | 157 | 159 | 98.74% |

本轮关闭3b9264/3bb7bc共享的两条有限观察记录，不是两个独立产品bug或完整父函数迁移。剩Stack命名图标0519f8与FRC365e18，另有未知入口04430c/0f733c。原shared registry、实体/DI/actor与完整模型生命周期继续partial；FRC项不能用未消费的影子对象关闭。

1007项源码/静态检查通过，新增16项；绑定18原片段、24条ARM指令、四个实际context key导入及真实虚槽。10个旧测试改为比较实际生命周期新增块之外的片段，或冻结旧hash并核对当前相关方法。初991检查的10失败/3定位错误、中间两处重复条件定位和新测试1处换行slice错误均留日志。只读低模型复核覆盖最终stable-ID getter及weak subject投影，未发现可证错接或过宽normalize；不等Swift/CoreData运行通过。

6份生产修改、1份新增，228份保持原样；未改变context reset、事务或模型迁移。官网9文件、版本1.0.2、HEAD及function-map不变；未编译、运行SDK/数据库/框架/应用、联网、提交或发布。

[机器证据](p0-p1-repair-round65.json) · [补丁](p0-p1-repair-round65.patch)
