# 第五十七轮：分组创建与关系类型

新建分组现在进入既有托管事务：先插入ListEntity、设置identifier/name，初始化Pasto必需的metadata/date，再尝试永久ID，之后才执行属性编码、写rawAttributes和rawType2，最后构造并追加同UUID的值模型。后续synchronize可读取pending新行并复用，不重复创建List。

原版永久ID失败没有中止创建。主审从ARM确认false分支释放Swift错误，清x21后与成功路径合流到JSON编码，当前用try?保留此行为；属性编码错误仍向外传播，已插入对象不额外rollback/delete。本轮不推断原CoreData框架的最终回滚或保存行为。

公开pinboardOwner getter本身与目标列表消费者都只接受rawType2。旧JSON的nil普通组类型仍在写入/发布前规范为2，托管投影读真实类型，0/1不再被nil兼容门接受。Int64采用exact Int16转换、未知0，避免65538截断为2；完整任意64位值往返仍属模型适配边界。

| v12有限清单 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 74 | 90 | 82.22% |
| 合计 | 143 | 159 | 89.94% |

关闭3条旧有限记录368560/31bc94/3250f0，分母不变，余16条差异和两个未知。并非三个完整原函数；原实体/default、metadata创建、父回调/DI/ABI及框架运行结果仍未闭合。P1分组成为唯一进行中模块，搜索完整父合同保留待核。

915项源码/静态检查通过，新增16项；绑定6原片段、4真实selector、5条ARM指令和_swift_errorRelease导入，SDK头声明includesPendingChanges默认YES。旧899项无需改动保持通过；新914最初有1断言/2定位错误，修正后通过，进一步补getter自身的严格判断并重新绑定proof，最终915通过，日志均保留。只读低模型复核了正常事务/同ID复用及legacy类型，主审未添加原版没有的假设UUID碰撞guard。

3份生产文件修改、230份不变；官网9文件、版本1.0.2、HEAD、function-map不变。未执行CoreData/SDK/应用、编译、联网、提交或发布。

[机器证据](p0-p1-repair-round57.json) · [补丁](p0-p1-repair-round57.patch)
