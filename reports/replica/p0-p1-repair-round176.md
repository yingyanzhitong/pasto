# 第176轮：分组筛选的字符串标识、原生名称与查询状态缺口

日期：2026-11-01。遵循P0修复→P1检查→P1修复；P0共享源与上一轮富文本owner修复保持。本轮修复分组筛选身份/名称，并确认同一筛选ViewModel的查询状态仍缺迁移，不以局部修复代替整个函数完成。

## 已实现

原候选及建议保留String分组identifier；原006e80对同一tag/String增删过滤节点。此前Pasto的候选/已恢复token解析都转UUID，拒绝非UUID并改写可解析值的大小写，再由queryNode输出uuidString。现Selection.pinboard存String，两处解析及queryNode编码原样交付；顺序、重复、空值及非UUID不在这里额外过滤。现有查询节点存储格式不变。

原2ddc10在group5调用应用安装的名称resolver；真实07d0e0在07d358将07d740写入1057920，回调07d950→07d78c通过ListsReading+20(实际witness→368060→368080)按原String找首个List并读name。缺失resolver/对象时回到原输入String；空名称仍是成功返回。当前改为复用tabListTarget(identifier:)读取原生名称，缺项返回原identifier，替换旧Pinboard值缓存/“Pasto”回退。

原32aee0在Ghidra删除的32af20错误块释放fetch错误并返回空数组，后续首项为nil；当前原生read的try?→first同样使名称查询失败回到原identifier，没有另加弹窗。当前Group5默认本地resolver有限名称合同已修；不外推全部caption、图标或可变全局resolver的任意替换。

20原片段、7索引机器范围、真实global安装指令/方法表指针/name selector及errorRelease导入绑定。7相邻方法和7共享源不变。原005e1c候选初值空、MainActor Task强持model、本地provider分别消费错误的加载子链可复用；042908→04493c不支持coder并trap，当前fatalError对应支持边界，这两项不新增修复计分。

## 新确认尚未修复

原005e1c初始化model自己的Published query，006e80从这个快照增删后先写model，再调用onQueryChanged；03f044传入041e08→041860，弱读原SearchBar，缺owner直接返回，存在才进入coordinator的2f7744(mode0)。

当前ReplicaFilterBrowserModel只存sections；真实行从state.hasSearchFilter和state.toggleSearchFilter读取全局query，缺toolbarOwner还会直接applySearchInput修改全局状态。若弹窗打开后外部查询改变，原模型继续从自己的初始/已编辑query生成提案，当前会从新全局query生成另一提案；回调owner缺失的边界也不同。因此006e80只完成String身份子链，**仍为待修，不计整个有限函数已修**。下一项直接迁移model query及实际弱SearchBar回调，见filter-model-query-gap.json。

## 验证与进度

2生产文件5精确增量，245文件保持。新增18项源码/机器码与协议模型检查通过；完整2590项静态检查通过，失败0、错误0，审计后18项再通过。首轮2590中3失败是旧UUID门/整份文件快照断言，日志保留；原标识断言改为当前String行为，历史文件比较仅逆本轮精确增量。4旧文件10模式精确重放，247生产逆恢复/历史幂等通过。逆变换曾把新行当旧id.uuidString前缀，已用完整换行锚定；生产代码未因测试失败更改。

v80新增2条记录、1个组，其中2ddc10有限名称合同已修，006e80查询所有权仍待。230记录204组/12额外完成合同保持：P0 81/81（100%），P1 148/149（99.33%），合计229/230（99.57%）。另1项未知0f733c不计入这个已确认差异分母。该比例不是全量迁移完成率，目标继续进行。

应用版本1.0.2、HEAD、function-map及官网/下载9文件保持；仅本地修改，无联网、编译、构建、安装、应用/框架执行、提交、推送或发布。
