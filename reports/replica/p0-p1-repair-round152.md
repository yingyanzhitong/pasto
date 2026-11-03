# 第一百五十二轮：来源实体创建与保存日期

继续P0修复→P1检查→P1修复。按实际来源实体批量核对，原Application和Device父指针均为SyncableManagedObject，真实实例方法表只有构造器、类方法表为空；原模型均有createdAt和updatedAt。ItemData父指针则真实绑定NSManagedObject，模型仅原始数据和item关系，不具有日期字段，不能全局套用时间回调。

新增PastoApplicationEntity与PastoDeviceEntity，当前模型明确注册这两个类；创建时super之后primitive写createdAt，已有共享willSave按inserted/syncApply/changedValues门更新updatedAt。实际来源工厂改用类型化通用fetch，保留默认predicate/sort、batch20、limit1/offset0和原错误处理。移除三个helper中较晚的createdAt赋值，日期由实际对象插入回调产生。来源名称、图标、颜色、设备标识及旧name/UUID兼容保持。

当前模型增加includeTypedSources，另保留上一个当前模型作为false候选，原十个旧候选显式false，共十一候选。旧属性、关系、约束及迁移算法尾未改；没有执行模型hash或数据库迁移，不能宣称运行迁移验收。ItemData原始模型保持，无缺字段KVC写入。

9个原片段、三类真实方法表和ItemData父导入、原v10三个schema绑定；7个来源方法及5共享源不变。同一保存回调体与151轮完全相同，实际typed子类3→5。生产修改3文件12处，其余244文件不变；新增10项直接核当前源码的检查，全2332项源码静态检查通过。

首轮2332项有8失败2错误，均为既有源码形态/摘要约束变化，原日志保留。7个旧文件20个模式23次精确调整：旧快照仅隔离本轮增量，当前设备工厂测试则直接改查真实typed factory与构造回调，仍保谓词、错误、原字段及调用顺序约束。完整生产247文件逆增量恢复与旧测试调整逆恢复均通过。

v61保持216函数记录194组；既有3b4984补来源生命周期有限合同，额外合同10→11，不重复计函数。已确认有限清单P0 77/77、P1 139/139、总216/216（100%）。完整模型、DI、原ItemData日志构造等父合同及04430c/0f733c两个未知仍保留，整体完成率未知，目标继续。

仅本地改动，版本1.0.2、HEAD、函数映射及官网/下载九文件保持。不编译、安装、执行应用或框架、不联网、不提交推送发布。
