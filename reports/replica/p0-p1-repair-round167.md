# 第一百六十七轮：全List原生排序、metadata KVO与保存合并

保持P0修复→P1检查→P1修复。本轮替换P1拖放排序的兼容数组入口，已接全List请求、原对象身份、index写入及双context保存链；原生创建和乐观applier消费者仍待，不把这一批算完整分组模块。

## 关键纠正

原368a30并不是在新私有context写metadata.index：35f4b8/35f508在原事务context查询全部List，按metadata.index排序，以NSObject相等找到源，调用真实SwiftUI MutableCollection.move。随后在这些原对象的context重读metadata，只给不同index赋值。新backgroundContext只按同List.objectID取对应对象，发metadata键的willChange/didChange KVO。背景保存通知同步合并回原context，然后外层3c4cdc→2ff310事务才保存原index。此前“私有context写index”的概述已更正，原记录仍pending，没有把旧判断当已实现。

当前moveList按这条顺序实现：全List原生fetch（失败空数组）、isEqual找源（缺项直接返回）、SDK move、不额外clamp/UUID/type2过滤；新privateQueue context使用同coordinator和storeTrump，index仍写原context，KVO只touch metadata，不写后台index。循环后才注册特定background对象、queue:nil的DidSave观察；双weak owner分别保护取context与performAndWait内的merge。无Task/DispatchQueue异步替代。

35ca9c/35e4d8后台save辅助函数还被Ghidra删去错误块。真实机器码证明：hasChanges才save，异常桥失败先rollback，再用命名NSManagedObjectContext诊断记录level3“Error saving managed object context: ”，消费错误并返回；368a30移除观察后继续外层事务。当前保持这条顺序，原P0主事务save失败诊断/rollback/重抛代码整文件不变。

所有原生List记录事务标记，阻止旧兼容index/字段覆盖；Store仅在原生动作后投影值。UI拖放使用String原生标识，保既有paste-pinboard:载荷前缀而移除UUID前置门；使用raw ObjectID快照位置，按097828把向后目标位置+1转为SDK移除前offset，包含history等全List。旧UI movePinboard数组路径已成为无调用者，随本轮移除；公开legacy reorderPinboards API保持。

## 验证

26原片段、3真实协议槽、119实际调用、9完整机器范围、10实际ObjC选择子；SDK move、CoreData performAndWait与swift_errorRelease导入均按真实dyld链解析，metadata KVO键和错误文字直接绑定。5生产文件8处精确增量，242文件保持；12邻方法、6共享源保持；247生产文件逆恢复及7旧测试/工具15模式重放通过。

新增11项直接核对当前源码/机器码，完整2477静态检查通过。首41失败中多项来自历史逆变换恢复已删除方法不幂等，已限定有新moveList时才恢复；第二轮余1项来自公共import逆变换误删旧Swift harness既有SwiftUI import，已限定ClipboardListPersistence类并加旧harness保持检查。定向147项余1旧拖放方法断言也已更新，所有日志保留。这里没有Swift/ObjC编译、框架执行或UI功能回归。

## 剩余与进度

原097828尾部1b9460乐观applier移动、TabBar拖放几何与创建后0.2秒inline编辑交付继续复核；未用颜色优先是用户适配，仍要核其原生来源。新后台context以同coordinator适配原NSPersistentContainer工厂，完整容器/DI默认值、真实框架重入/ARC/schema不冒验收。

v73保持226记录201组/12额外完成合同，仅367f78追加部分跟进。P0已确认差异81/81（100%）、P1 144/145（99.31%）、合计225/226（99.56%）；两个unknown04430c/0f733c仍开，整体迁移完成度未知。

版本1.0.2、HEAD、function-map及官网/下载九文件保持，仅本地修改，不编译、构建、安装、运行、联网、提交推送或发布。
