# 第四十九轮：独立索引活动状态

原 isRunning 独立于任务句柄：初始化在 false 时置 true，成功续体保持 true，初始化失败续体才清 false。Pasto 已将这条状态接入真实路径，不再以队列 worker=nil 或 observer 缺失代替停止。已运行的普通请求不重复读恢复状态、安装 observer 或跑全量；只有获准且 inactive 的初始化进入这些步骤。初始化成功后才处理定向写入，所以后者失败不会清掉服务活动状态。

首批/后续批次实际检查 isRunning 与当前 Task 取消状态，停下或取消都正常退出；已成功批次计数和最老时间仍保存，snapshot 最终 indexed=total 只在活动且未取消时执行。原 24 个片段、两个真实 async descriptor 与前轮实际 class field-offset vector 均已绑定。

原 target delegate 经 2f2690→2f26a8→c3ec00→f3c8c→f2ca8→ea770，不走全量 reset/start。只读子审发现初稿共用初始化入口会让 inactive target 启动全量；已补 pendingMayInitializeIndex：UI/retry/full 请求置 true，target 不新建也不抹掉已有 true。drain 在 await 前 capture 并清零，只在获准块内初始化；inactive target 直接正常结束并 ack。两轮实际源码复核及请求合并 fixture 验证了这个边界。

full delegate 及时清 active、取消/清 historyTask，再安排 reset，使等待 SDK 的旧批次在下个边界停下；不取消或等待串行 worker。原 stop 仍需取消并等待 OCR task，当前未加假 OCR 字段冒称已接通。原 OCR 队列、observer 替换、reset 前后时序、SDK retry/backoff、weak service owner/释放后 ack、FRC/DI/实体/ABI 与并发重入继续开放。既有本地缓存及 namespace 适配保留，不能用有限索引行为证明全部内部状态相同。

| 固定有限差异清单 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 54 | 81 | 66.67% |
| 合计 | 123 | 150 | 82.00% |

关闭 2f20a0/2f2214 两条有限活动状态差异和 ea78c/eaa10/eaea4 三条共享 target 活动/取消差异，不是五个独立 bug，也不是完整函数迁移。其余 27 条差异及两个未知继续保留。

800 项源码/静态检查通过，新增 20 项，覆盖原状态字段/分支、真实初始化和请求类型门、合并请求、不活动 target、SDK 错误后的状态、full stop、不完整 snapshot 的完成保护，以及未改的查询/五字段 JSON/Token 编解码。Python transition fixture 不执行 Swift/原 actor。初 780 项有 11 处旧源码形态断言失败和两处旧定位错误；请求类型变化又有两处旧 update/retry 全方法断言，日志均保留。五份旧测试按当前 guard/请求标志更新或冻结历史全方法，同时继续核当前成功批次尾、SDK flag 和 ack；修后 780 与新增 800 全绿。

仅一份生产文件改变，232 份不变，无新增生产文件。官网九文件、版本 1.0.2、HEAD 与 function-map 不变；未编译、运行应用/原生/数据库、联网、提交、推送或发布。搜索 P1 仍唯一 in_progress，目标继续进行。

[机器证据](p0-p1-repair-round49.json) · [补丁](p0-p1-repair-round49.patch)
