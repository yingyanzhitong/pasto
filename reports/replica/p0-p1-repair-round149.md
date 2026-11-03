# 第一百四十九轮：迁移 List 原生插入校验

按P0修复→P1检查→P1修复，修复148轮新确认的329980缺口，未跳过真实model/class入口而只改两个创建helper。

新增PastoListEntity及PastoListMetadataEntity并绑定当前model，保物理实体名、属性、关系、约束、UUID和旧存档。List默认metadata.index升序，Metadata默认index升序，两者都走已有generic fetch factory的class defaults与batch20；原共享父类的awakeFromInsert先super再写primitive createdAt也接入两类。原Syncable真实instance方法表无validateForInsert override，因此本轮super校验对应NSManagedObject校验；其willSave及其它父合同仍未声称迁移。

真实validateForInsert覆盖非deleted/metadata nil/context存在门，以SDK公开的原String桥构list:<id>。同context performAndWait查询已有metadata（默认升序、limit1、offset0）；有则仅附着，不重写其id、index或日期。无则同context取完整有序metadata，尾项index+1，空集合-1+1=0，普通Swift有符号加法保溢出trap；先计算再分配同context Metadata，再设identifier/list/index、附着关系。全部分支最后try super.validateForInsert，不吞父类错误，不照抄Ghidra永远true。

原32aee0的另一段被Ghidra误删的ARM错误分支也已核：fetch失败释放Swift错误并读取真实swiftEmptyArrayStorage。因此两个查询按原退空；与父校验失败向上传播分开。原metadata sort key index、父awake key createdAt、真实父类/方法表、原19条NSError等证据与新增21 ARM字均绑定。没有根据无直接caller推定不可达。

分组FRC producer和optional getter同步改用实际PastoListEntity，原query谓词、初始fetch/快照/cache/delivery/错误逻辑不变。旧makeList/insertPinboard/synchronize helper完整保留：它们已有的预填metadata/id/index/日期是现存兼容路径，不把本轮钩子接入冒称整个创建父链与原版全同；已有metadata按原校验语义不重写。

新includeTypedLists只为当前model注册两类；新增上一模型false候选，原九个legacy候选全部显式false，原迁移匹配/映射/临时目录/replace算法尾部完全相同。只证源码候选保留，未执行CoreData model hash或真实数据库迁移。

4生产文件8精确增量，243文件不变；17原片段、原148合同、3真实类表、21新增ARM字/真实empty-array导入、2本机SDK声明、10旧方法与5共享源已绑。新增16源码检查，完整2306项通过。首轮3旧文件/改动集合快照失败留日志；4旧工具7模式7替换只逆隔离已审本轮增量，旧业务断言不变，新测试直接核实际model/validator/producer。编辑脚本最初在无尾逗号的最后legacy项中止，按原baseline校验前3增量后续接完成，未重取baseline、未reset源文件，恢复记录保留。

v58不加函数/组，只修v57已有329980一条：215记录193组/9额外合同保持，原pending记录摘要与repair保留，其余记录原样。已确认有限差异修复：P0 77/77（100%），P1 138/138（100%），总215/215（100%）。完整原模型/DI/ARC/Syncable willSave、旧创建兼容与两个unknown仍开放，整体迁移完成率未知，目标继续。

版本1.0.2、HEAD、function-map及官网/README下载9文件保持。未编译、构建、安装、运行应用或框架/数据库、联网、提交、推送或发布。
