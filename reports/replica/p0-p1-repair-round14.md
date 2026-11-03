# P0 → P1 源码修复：第十四轮

| 范围 | 已修有限差异 / 固定差异分母 | 进度 |
| --- | --- | --- |
| P0 | 41 / 64 | 64.06% |
| P1（P0依赖） | 5 / 81 | 6.17% |
| 合计 | 46 / 145 | **31.72%** |

本轮消除 `2ff310` 的有限事务边界差异；仍有99条差异及2个未知入口。不是完整原函数、模型或产品完成率。

## 本轮修改

业务commit直接在同步context.performAndWait中运行本次Transaction的callback与增量写入，保持withExtendedLifetime跨操作、保存及返回。callback出错直接传播，跳过后续变更检查和保存；不再通过带reset/rollback的读取适配。

只有callback成功且context.hasChanges时尝试保存。原链302b78直接调用operation，随后才进入2ff9c8→308968→30844c→35e614→save:。当前复用已有f_1002ff9c8桥，范围只包context.save；NSError经Swift Error传播，捕获的Objective-C异常保留name/reason，不将整个业务操作包成保存异常。

read、revision、search和初始化图/日期回填仍使用原有perform回滚适配，方法内容未改。失败后Store不发布新的值快照；这不代表所有托管对象通知都未发生，也不证明后续读取或框架隐藏行为与原版完整等价。

## 恢复克隆分支的边界

原克隆支路有两入口：目标CKShare projection有值时直接进入fetch，或来源Sequence中存在满足共享条件的项。来源predicate先要求Item.list、rawType2与可读取的CKShare。普通目标及全部来源均无share时，两入口均不成立，原函数直接Array(sequence)返回，不创建新实体。

根审补齐了目标Optional快路径，纠正“只有contains入口”的子审表述和一处范围字面笔误，并将4个实际ARM范围、2个真实Sequence导入另行绑定。共享participant细节继续排除，不为普通离线历史新增克隆，也不声称该分支只涉及跨账户。

## 验证与剩余工作

326项源码与原始数据静态检查通过，新增8项。修改1个生产文件，其他223个与本轮备份一致；6个旧测试改为检查真实commit路径和保存局部异常桥，保留容器身份、永久ID错误传播、条件保存与成功后发布断言。原C及8段ARM数据、2个Sequence导入已核；没有编译或执行框架。

当前继续P0快捷键/选区，先核Carbon注册接口及select-all/导航。数据模块保留原实体/Sequence、恢复/删除父合同、跨进程context生命周期及归档身份，不因切换模块标为完成。

未编译、运行应用/CoreData、联网、提交或部署；真实错误后的pending对象和实际存储未做运行验收。版本与全函数台账不变，官网、README和Actions仍仅保留本地。

[完整记录与源码绑定](p0-p1-repair-round14.json) · [源码补丁](p0-p1-repair-round14.patch)
