# 第二十轮：本地历史事务到索引消费

本轮继续 P0 数据与持久层迁移，只做源码修改、原伪代码/机器码比对和 Python 检查。不编译、运行应用或原二进制、执行 Core Data/Spotlight/UI 回归、联网、提交或推送。

## 原合同与修改

原数据源读取安全归档的 NSPersistentHistoryToken，规范化保存后先追赶历史，再安装以 coordinator 为 object、queue=nil 的无界本地通知流。每次按 token 读取事务；没有 token 用 distantPast，读取错误上抛。空事务直接返回，非空事务即便没有相关项目变化也交给消费者。

已补 OriginalSearchHistory 并接入 ClipboardPersistence、ClipboardStore 和 ReplicaSearchIndex。开启本地历史与变更通知，独立 Item.key 保留删除 tombstone 值。通知终止时移除观察；取消静默，普通消费失败记录诊断并保留旧 token，消费成功才取最后事务 token 安全归档保存。没有来源身份时仍观察，只不写持久 checkpoint。

变更按事务原顺序合并：插入清除同项的更新/删除；更新若已有插入则保留插入，否则归入更新，并清除删除；删除清除插入/更新。只输出非空组，顺序为插入、更新、删除。原类型为 PasteCore.ItemEntity，当前独立实体适配为 Item，原 identifier 适配为既有 key；没有冒用原厂数据模型。

真实消费者在同一个 worker 串行执行：插入/更新读取数据库当前对象，缺项跳过；删除按存储 namespace 删除 SDK 条目。SDK 成功后才更新内存并完成消费，错误回传到历史流，token 不推进。首次全量及指定 ID 重建也读取数据库当前值；历史流生效后，普通查询不再用界面快照覆盖索引增量。

## 检查

- **194/194 项** Python 源码、原片段摘要、静态绑定及台账检查通过，新增 15 项。
- 集合检查从实际 Swift 源码提取受限 set 操作，在 Python 中穷举长度 1 至 5 的全部三类事件组合，与原决策规则比较；另测多 ID、缺失标识和错误修改反例。这是源码投影检查，不是 Swift 或 SDK 执行。
- 原 changeType/changedObjectID/changes/executeRequest:error:/existingObjectWithID:error: selector 均沿真实 Mach-O fixup chain 到达字符串；原三个输出 tag 0/1/2 及两个 store flag=true 已绑定机器码，实体类名绑定原 ObjC 元数据。
- 调整原测试的请求捕获作用域，避免新历史队列的 await 误充请求的第一个 await；更新惰性分批反例的当前变量名，保留原测试意图。

## 总进度

- 本轮复核 25 个原地址，20 个首次计入当前目标，新增 25 条 partial；partial **551**，完整标记没有升级。
- 当前累计复核 **491 / 81,123 = 0.6053%**。
- 历史完整标记 **1,648 / 81,123 = 2.0315%**，含过期证据，不是当前产品验收完成率。
- 映射 2,208 条，严格复用候选 317；既有证据地址缺失 12 条保留。

## 仍需继续

原 actor/private context/泛用 DI 与当前 MainActor、自有实体和偏好键仍不同；原全量 IndexingState、schema、可用性和健康探测尚缺。索引与 query 仍共享 worker，历史消费可能等当前 query 退出，后续需分离。指定 ID 目前一次 fetch 全部目标实体、SDK 才按 100 分批；原逐输入批次 fetch、OCR 和 active/取消规则继续待对齐，普通增量未冒用这个局部上限。

为了保留自有实体删除标识增加了轻量迁移选项，但未执行既有数据库升级验证；不声称数据库兼容或功能回归已通过。继续 P0 模型、事务错误/Undo 与索引状态依赖，其它模块目标保留。

[逐函数合同、当前源码摘要及静态绑定](offline-migration-p0-round20.json)。
