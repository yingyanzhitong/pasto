# 第十九轮：真实持久存储身份

本轮按 P0 数据与持久层优先级继续，只做源代码迁移和 Python 源码/证据检查；未编译、运行应用或原二进制、执行 Core Data/Spotlight 功能测试、联网或提交。

## 已修复与生产调用

原 `36e3ac → 36e3c4` 返回 coordinator.persistentStores 第一项的 identifier，没有存储或 identifier 时返回 nil。已在 ClipboardPersistence 加入对应只读 getter，由 ClipboardStore 转发，搜索 update 把身份放入 Request 的相等性和待处理快照，来源变化不会因内容未变而被跳过。

原 `2f00dc` 只有在前后身份都非 nil 且不等时视为来源变化；新的非 nil 身份在后续索引前保存，nil 不覆盖旧值。当前 worker 接入同样的比较和重建触发，使用真实持久存储身份，保留原来的冷启动重建。getter 不创建 UUID、不保存数据，也不使用每次写入都会改变的 revision。

这只闭合了来源身份读取和内存比较分支。原身份与 IndexingState 是持久化的，且通过 actor/async provider 调用；Pasto 当前仍为 MainActor 同步提供者和内存状态，不声称重启复用、完整全量恢复或异步执行器等价。

## 下一批依赖

已读原 `36f7b8 / 36f968 / 36f9e8 / 370fc4 / 371030` 的本地持久存储通知流：NSNotificationCenter 以 coordinator 为 object、queue=nil 注册 NSPersistentStoreRemoteChangeNotification，yield AsyncStream，终止时移除观察。此 RemoteChange 是本地 Core Data 接口，不能按名称误排除为联网；当前缺完整事务/token 消费，未添加孤立观察者来冒充迁移。

继续核对 `36e4f4 / 36e5cc / 36eb54 / 36fa2c` 的本地历史事务读取、token、插入更新删除合并及成功消费，再连接完整索引状态。其余 P0/P1/P2 差异仍保留，目标继续。

## 检查和进度

- **179/179** 项 Python 源码、原片段摘要、真实消费者和台账检查通过；新增 6 项，含防止 nil 误判及丢失身份的源码反例。
- 本轮核对 **11** 个地址，其中 1 个与上一轮重合；新增 **2** 条 partial，总计 **526**，没有升级完整标记。
- 当前累计去重复核 **471 / 81,123 = 0.5806%**。
- 历史完整标记 **1,648 / 81,123 = 2.0315%**，含过期证据，不能当作当前产品验收完成率。
- 库存检查 2,183 条映射，严格复用候选 317；既有 12 条证据地址缺失问题保留。

[逐函数合同及当前源码摘要](offline-migration-p0-round19.json)。
