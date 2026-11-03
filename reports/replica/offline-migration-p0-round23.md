# 第二十三轮：沿真实工作指针迁移删除服务

本轮继续 P0 本地历史到索引的消费链。只做源码、原反编译/机器码对照和 Python 检查；不编译、运行应用或原二进制、执行数据库/SDK/UI 回归、联网、提交或推送。

## 原调用链

原 `2e6dc4 / 2e7034` 使用的 `100c3e910` 相对工作指针指向 `2ec058 → 2e243c`。SDK 调用机器码进一步指向 ObjC stub `100c00fc0`，沿真实 fixup chain 解析 selector 为 `deleteSearchableItemsWithIdentifiers:completionHandler:`，因此确认这条链是删除服务，不是猜测的插入/更新参数路径。

原服务按输入数组每 100 个字符串切片，成功才经 `2e7480 / 2e74e4` 推进下一批；错误经 `2e7770 / 2e77d4` 返回父调用者。删除输入没有先去空、转 UUID、排序或去重。原串行队列还分别使用等待前任务与等待工作 Result 的 Task，本轮没有将它们宣称为已完整迁移。

## 已修改

新增独立 deletionBatchSize=100 和 deleteIdentifiers 服务，历史删除与快照清理都交给它。每批按输入数量计算半开区间，在同一 worker 中 await SDK 完成后再继续。SDK 接收原始字符串加 Pasto 的兼容 namespace，保留输入顺序、重复、空值及非 UUID 字符串，不再先 compactMap(UUID) 压缩输入。

只有本批 SDK 成功后才清理本地 cache；UUID 转换仅用于既有 UUID cache 的键，不影响已提交的 SDK ID。错误抛回历史消费，停止本请求后续批次，既有 token 仍不推进；worker 可继续处理另一个排队请求。插入/更新分支保持当前代码，未把删除服务的局部上限套给它们。

## 检查和进度

- **215/215** 项 Python 源码、原片段摘要、指针/selector 绑定、删除窗口投影及台账检查通过，新增 6 项。
- 删除投影覆盖 0、1、99、100、101、199、200、201、301 个输入，含重复、空串和 opaque ID；反例确认改为 UUID 过滤时检查失败。它是源码投影，不是 Swift/SDK 实际执行。
- 四个真实 work descriptor 的相对指针、原 100 立即数/批次推进指令和 SDK selector 均绑定原二进制摘要与字节。
- 本轮复核 **18** 个原地址，14 个首次计入当前目标；新增 **17** 条 partial（其中 3 条是上轮已审的路由缺口接入），累计 partial **582**，没有升级完整标记。
- 当前累计去重复核 **515 / 81,123 = 0.6348%**。
- 历史完整标记 **1,648 / 81,123 = 2.0315%**，含过期证据，不代表当前产品验收完成率。
- 映射 2,239 条，严格复用候选 317；既有证据地址缺失 12 条保留。

## 仍需继续

当前串行 worker 与原 get_value/get_result 双 Task 任务链、执行器及优先级仍不同。原 SDK 服务 weak owner 不存在时返回 Bool 标志，当前 helper 持有 self、返回 Void，完整生命周期分支尚未对齐。

下一批沿 `100c3eb68` 数据源观察任务和其变更闭包，核对实际 insert/update/delete 分派、force/isUpdate 和 OCR/active；继续原串行请求与取消、完整 IndexingState、P0 模型/事务/Undo/applier 及其它 P0/P1/P2 范围。未闭合部分不计完整迁移。

[逐地址合同、当前源码摘要和静态绑定](offline-migration-p0-round23.json)。
