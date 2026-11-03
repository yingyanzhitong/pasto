# P0 → P1 源码修复：第十三轮

| 范围 | 已修有限差异 / 固定差异分母 | 进度 |
| --- | --- | --- |
| P0 | 40 / 64 | 62.50% |
| P1（P0依赖） | 5 / 81 | 6.17% |
| 合计 | 45 / 145 | **31.03%** |

本轮继续补真实数据模型与事务父链，未将局部修改提前计作完整父差异消除。仍有100条差异及2个未知入口；不是完整函数或产品完成率。

## 本轮修改

实际Item.timestamp改为可空Date。读取时以其是否存在决定isInHistory；历史移除写nil，恢复写日期。原删除函数363004的rawType1确实显式清timestamp；rawType2解除owner关系，已有timestamp继续保留。原模型资源也确认timestamp为optional Date。

本地localCreatedAt保存Pasto旧显示日期，避免已移出历史、仍在分组中的内容失去日期。它是兼容字段，不声称原厂具有同名属性。旧inHistory保留为迁移输入和兼容镜像，读取不再将其作为历史状态权威。recency更新仍不重编码二进制内容。

迁移识别四种旧模型，包含上轮已有List的nonoptional timestamp模型。源码检查确认关闭新开关后旧模型factory主体与备份等价。初始化在现有锁与同一个context事务中先填List图，再仅对缺localCreatedAt的旧Item保存原日期，最后对原inHistory=false的记录清timestamp；成功才更新revision并保存。没有清空或重写原内容blob。重复启动跳过已回填的行。

commit不再在业务callback前reset context，保持本次托管对象连续性。原操作成功且有changes才save的顺序保留；当前perform异常rollback、原父函数只跳过save的差异仍待处理，未计整个事务完成。读取/revision/search的外部存储适配本轮未改。

## 审查更正与验证

原361ec0先经364108反转数组，再正向循环取Date。不能漏掉该转换而把当前反向遍历判错。361690有直接Array(sequence)返回的路径，clone只适用于其门、fetch/filter及创建条件都满足的分支，当前尚未闭合该门的完整语义；未按猜测重写所有恢复。

318项源码与原始数据静态检查通过，新增13项。修改1个生产文件，其他223个与本轮备份一致；3个旧测试更新模型/初始化条件和reset合同，原迁移保护、业务保存顺序及内容不重编码断言保留。源码审查未发现受支持路径下的具体数据丢失缺陷，但没有执行CoreData。

未编译、运行应用、迁移真实用户存储、联网、提交或部署；nullable schema的实际inferred mapping、事务失败和refresh效果未验收。既有额外成员关系、软删除等适配仍保留，原实体/Sequence/克隆/完整错误语义继续排队；版本与全函数台账不变。

[完整记录与源码绑定](p0-p1-repair-round13.json) · [源码补丁](p0-p1-repair-round13.patch)
