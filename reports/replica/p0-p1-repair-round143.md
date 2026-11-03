# 第一百四十三轮：复用搜索与分组集合的成员缓存

按P0修复→P1检查→P1修复继续。本轮复核分组generic集合错误/更新来源，发现成员Set缓存合同尚未迁移；不因初次fetch、ID查询回退等已一致分支而重复修改。

正向绑定原355198两条真实导入为NSUpdatedObjectsKey和NSRefreshedObjectsKey。原366c6c/366db8分别经36be08/36be40过滤ListEntity/ItemEntity，再投影objectID与成员Set交集；真实ObjC class_ro/name指针也已解析，不凭函数名猜类型。当前有效本地FRC模型下，各typed请求的成员ID交集已排除其他实体，读取相同更新/refresh来源，保留该已有实现；完整原模型/fault/DI身份不因此升级。

原366b38先清pending，以3699b8比较待发布ID数组与当前数组；只有不同才更新IDs并36bf0c重建成员Set到+40，之后无论是否相同都send snapshot。原366c6c/366db8在没有pending时复用+40成员Set，有pending时临时根据pending IDs重建，不能用旧缓存漏掉新成员/空快照。Pasto此前每次objectsDidChange都Set(ids)，没有这层缓存。

现搜索和分组collection均持有objectIDMembership；flush仅数组顺序变化时重建，观察无pending时复用，有pending时按其IDs重建。保相同IDs仍发布updated IDs、同成员但顺序不同仍重建、空pending不能退回旧成员、清pending和更新cache都先于subject.send。UUID/itemReferences展示投影仍逐次按原本地adapter执行，未将不同层的值投影偷换成缓存；FRC初始化/ID辅助查询回退、差分delegate与调度接口均不改。消除一处额外Set构造，不宣称实际时延测试。

1生产文件3双站点模式共6精确增量，其他246文件不变。绑定17原片段、8 ARM字、2实际调用、2通知键真实导入和2ObjC类元数据；10旧方法、整个difference delegate及3共享源不变。新增16项源码检查，完整2230项源码/Python/Mach-O检查全部通过。首次2旧共享/全文件快照断言失败已留日志；2历史测试工具3模式5替换只逆隔离本轮缓存增量，不改旧业务断言。未编译或执行框架。

v52保旧209记录187组/9额外合同，新增366b38缓存有限差异1条源修至210记录188组；两collection及pending消费者共一个缓存修复，不拆多条bug。P0 77/77（100%）、P1 133/133（100%）、总210/210（100%）均为已确认有限差异修复率。原dispatcher/上下文队列、完整模型/DI/fault/lifecycle和两个未知04430c/0f733c仍未闭合，整体迁移率未知，目标继续。

版本1.0.2、HEAD、function-map及官网/README下载9份改动保持。仅本地源码/报告和源码检查；未编译、安装、运行、联网、提交、推送、发布或部署。
