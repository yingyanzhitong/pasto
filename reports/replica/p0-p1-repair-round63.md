# 第六十三轮：专用 Item 类型与默认查询工厂

新增实际PastoManagedObject/PastoItemEntity，接入当前Item实体的managedObjectClassName。原Item metaclass只有defaultSortDescriptors覆盖，返回timestamp降序；defaultPredicate来自NSManagedObject的PasteCore category并返回nil。主审已将类地址、继承和方法表、selector及具体指令绑定，未沿用子审最初的未知值作猜测。

泛型工厂按实体名、类默认排序/谓词、batch20构造并返回typed NSFetchRequest。Item wrapper已实际用于索引记录、原生/本地Item读取、通用Item fetch及菜单计数；原有ID/list/history谓词、空输入、错误和投影尾保持。

物理实体名Item、UUID和字段/关系声明保留。当前模型用includeTypedItem=true绑定专用类；前current模型与旧6个候选全部显式false，迁移/替换算法保持。仅核对源定义，未执行model hash、旧库迁移或typed fetch。

| v12有限清单 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 85 | 90 | 94.44% |
| 合计 | 154 | 159 | 96.86% |

关闭3214a8/329754/3298a0共享类型与工厂的3条有限差异，非3个独立产品bug或完整原函数迁移。余5条差异及2项未知。完整原实体/泛型所有NSManagedObject类型/DI/ABI、ItemMetadata图、FRC/currentCollection/list观察和SDK写入弱owner仍未闭合。

979项源码/静态检查通过，新增12项；9原片段、6selector、11条ARM指令和本地SDK typed fetch/count接口绑定。9旧测试核实际false分支旧模型/7候选，或比较真实factory替换前后prefix/tail；初967十一处旧形状/hash断言和后续旧模型比较错误已修，日志保留。一个低模型只读复核未发现错接、候选丢失或无真实消费者。

2份生产修改、1份新增、231份不变；官网9文件、1.0.2、HEAD和function-map不变。未编译、运行框架/应用、访问数据库、联网、提交或发布。

[机器证据](p0-p1-repair-round63.json) · [补丁](p0-p1-repair-round63.patch)
