# 第四十六轮：P1 索引断点续传

真实启动现在先读取一次已保存的五字段状态，校验 schema 与双方非空来源身份。未完成状态（indexedItems < totalItems）保留现有索引，直接以 oldestTimestamp 查询严格早于游标的 ID；不运行已完成状态健康探测，也不清空索引。来源/版本不符、缺状态及健康探测为空继续原清理路径，显式全量重置优先于恢复。完成态探测非空或错误保留的既有分支不改。

每个新 pass 保留旧 indexed/total，仅在 indexedBefore < 1 时从 total 扣除本轮无效 ID；invalid 重算，当前批次 Date 初始为空。nil 游标仍为无界查询，保持原 timestamp < cursor，不添加等值时间 UUID 分页规则。ID 查询为空时在新状态构造/保存前返回，保留旧状态。100 输入 ID 分批、实时记录读取、SDK 成功后更新 live.count 和本批最老 Date、正常完成 indexed=total 与上一轮逐字一致。

| 固定有限差异清单 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 44 | 81 | 54.32% |
| 合计 | 113 | 150 | 75.33% |

关闭旧 efba0/f2280 的共享冷启动持久恢复策略，两条不是两个独立 bug，也不表示全部异步函数已迁移；上轮 f00dc 不重复计分。剩 37 条已确认差异及两个未知入口，完整原函数/优先级分类仍未闭合。

746 项源码/静态检查通过，新增 15 项：18 个原片段摘要、clear 异步描述符相对地址至 f3a60→e267c、单次状态读取、真实分支与 SDK 调用处、空输入、nil/严格时间边界、计数规则、显式 reset 及前批次代码不变证明。Python 决策 fixture 明确只验证源码合同，不执行 Swift 或原生数据库。初 731 项有 5 个旧源码形态断言失败，日志保留；两份旧测试按新 helper/参数更新并冻结旧 before:nil 证明后 731 通过，新增后 746 全绿。仅一份生产文件改变，232 份不变，无新增生产文件。

继续待修：原独立 isRunning、stop/wait、观察安装、取消及失败重试、SDK weak owner/ack、FRC/实体/DI/ABI 与类型预览回退。现有 catch 仍将 needsReset=true，不能宣称同进程中断恢复已对齐。Pasto 的独立索引 namespace、旧 key/本地 UUID/标题及通用实体适配继续保留说明。

没有执行 UserDefaults、CoreData/CoreSpotlight 或应用，没有编译、构建、安装、联网、提交、推送或发布。官网九文件、版本 1.0.2、HEAD 和 function-map 不变。

[机器证据](p0-p1-repair-round46.json) · [本轮补丁](p0-p1-repair-round46.patch)
