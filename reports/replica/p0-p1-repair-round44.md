# 第四十四轮：P1 索引恢复前置合同

本轮沿原全量/恢复链补三个已确认差异：

- history token使用原固定indexHistoryTokenData标准UserDefaults槽，不再按store identity分区或在身份缺失时跳过保存。secure archive、首次catch-up、通知流及consumer成功后才推进token保持。旧分区值不迁移、不删除，本轮没有读取或写入真实UserDefaults。
- reset调用实际CSSearchableIndex实例的deleteAllSearchableItems并await完成，再清本地缓存，SDK错误继续传播。Pasto仍有每目录命名索引隔离，此操作仅清该实例，并非系统所有索引。原query命名空间/owner生命周期另行保留。
- native索引按ID的context.fetch NSError记录localizedDescription后返回空数组，并在记录投影/错误返回后defer reset。nil-ID全量快照fetch错误、DTO解码和ObjC异常不并入此新catch；既有前置reset及owner-context/DTO适配保留，原完整异步context调度/default request factory/FRC仍未迁移。

初始化时在原生数据读取、SDK删除/写入及observer安装前补isIndexingAvailable门。但共享worker Task已经创建，原actor isRunning/worker安装与stop/wait生命周期仍不同，所以2efccc只记partial，不计修复分数。

从原Mach-O类型反射/相对keypath/format6指针链及原函数补齐恢复状态证据：IndexingState严格五字段schemaVersion、totalItems、indexedItems、oldestTimestamp、invalidItems；最后一项不是sourceID，indexedStoreID是单独Config<String?>。固定key分别indexingState与indexedStoreID，state通过JSONDecoder/JSONEncoder保存。Date是外部绑定，解析imports符号为Foundation.Date，不把bind ordinal误当本地指针。此状态模型、schema/health/cursor恢复分支尚未实现，不计新增完成。

| 固定有限差异清单 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 41 | 81 | 50.62% |
| 合计 | 110 | 150 | 73.33% |

关闭36dc00、36e4f4、2e267c三条旧有限记录；所有full-function标记保持false。余40已确认差异及2未知；完整state/active/stop/cancel/error/owner/ack/FRC及typed-preview回退继续待修。

714项源码/静态检查通过：新增16项，纳入6项既有history检查；1旧测试只更新固定key/无身份门断言。绑定27原函数片段、实际deleteAll selector/fixup链、本机SDK及token字面；覆盖fetch与非fetch错误边界、reset/await顺序、token成功推进，以及原状态字段/Config键。Python key场景仅为源码语义fixture，不是执行UserDefaults。新测试先出现分支locator误定位/非唯一两次问题，失败日志保留并修正，最终全绿。修改3生产文件，229生产文件未变。

未运行Swift/ObjC/CoreData/CoreSpotlight、defaults、应用或迁移；未编译、构建、安装、联网、提交、推送或发布。官网9文件、版本1.0.2、HEAD及function-map保持。

证据：[JSON](p0-p1-repair-round44.json)、[补丁](p0-p1-repair-round44.patch)。
