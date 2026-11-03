# 第一百五十轮：List 与 Metadata 本地 willSave

继续P0修复→P1检查→P1修复。149轮已接实际List/Metadata模型和插入验证，本轮沿其真实Syncable parent保存回调，确认并修复本地updatedAt缺口，没有把共享父类整体当联网排除。

原List/Metadata真实类表均继承SyncableManagedObject，原parent method表willSave→3b4b94→3b4984。原函数先读取managedObjectContext及transactionAuthor，识别原小字符串syncApply；随后检查isInserted，非inserted且非syncApply时取changedValues，字典非空才创建Date并setPrimitiveValue(updatedAt)，所有分支最后super.willSave。已绑定managedObjectContext/transactionAuthor/isInserted/changedValues/setPrimitiveValue:forKey:/willSave六真实selector、24 ARM字，以及syncApply和updatedAt原小字符串。不能改用hasChanges或changedValuesForCurrentEvent，也不能额外加isDeleted门或省略super。

Pasto实际注册的List与Metadata子类原先只有awake创建日期和插入验证，没有该willSave行为。现两类各接同一override，先计算作者标志再按原门写primitive updatedAt，最后super；不写作者、不调用save、发送通知、调度异步或启用网络。syncApply只是本地事务标记读取，当前生产代码也未新增任何设置该标记的路径。原awake、validator、默认请求、model/10旧候选、创建helper和Store均不改。Item及其它原Syncable实体不因本轮两类接入就声称完整迁移，仍按其实际本地模型/调用链继续核证。

1生产文件1双站点模式2精确增量，246文件不变；3原片段、149的真实parent类表、六selector、24 ARM字、两SDK头文件、10旧方法与4共享生产源绑定。新增8项静态检查；源码三个布尔条件与原tbnz/cbz到super join的实际跳转按24种状态组合对比。这里是静态条件一致性，不是模拟CoreData或实测回调。

完整2314项源码/Python/Mach-O检查通过。首轮唯一失败是新增检查误把transactionAuthor ==中的等号当赋值；修为只匹配单等号的检查后定向8项及完整2314项通过，初始日志保留，生产源码未因测试误报改动。唯一旧测试工具改动为在全局逆隔离链前接本轮精确1模式/2站点，原旧业务断言未改。

v59保旧215记录193组及9额外合同，新增3b4984一个共享方法有限合同修至216记录194组：P0 77/77（100%）、P1 139/139（100%）、总216/216（100%）。不是整体完成率；其它原Syncable本地实体、完整模型/DI/生命周期、旧创建父链及04430c/0f733c两个unknown仍开放，目标继续。

官网/README下载9文件、版本1.0.2、HEAD与function-map保持；未编译、构建、安装、运行CoreData/应用/框架、联网、提交、推送或发布。
