# 第五十一轮：全量重置重试与清理顺序

full delegate 的真实请求现在带独立 resetsIndex 标志，在 await 前 capture/清零且优先于普通初始化。整个 resetIndex 包在原瞬态重试中，定向 pass 仍有独立边界，普通 startup 不额外加 retry。reset 在 active 时先 stop（目前仅活动状态/observer部分），写 nil state、等待 SDK clear 成功后，才进入正常初始化。初始化的活动保护/失败清 false 已抽入实际 initializeIndexIfNeeded，SDK clear 成为实际 clearIndex，清理失败不提前激活、不额外排全量请求。

原 nil-state 初始化本身还有一次 clear，继续保留。主审直接读取原 Mach-O 证实：c3ec18→f3cdc→f2648→f1c30/f1ca0 是整个 operation；c3ec20→eb754→e7838 是调度嵌套 operation 的 wrapper；c3ec28 和 c3eb50 都→f3a60→e267c，分别是启动前和 nil-state 初始化 clear。子审把 c3ec18 与 c3ec28 混同而推断只有一次 clear，未采纳；成功 ack 的续体不证明 operation 内部没有启动链。四个 descriptor bytes 和对应原片段已绑定。

| v8 有限差异清单 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 57 | 83 | 68.67% |
| 合计 | 126 | 152 | 82.89% |

只关闭旧 f201c 的启动前清理失败返回/无额外 reset 请求有限差异。全量重置与重试改动也推进其他父合同，但原 OCR task cancel/await 尚缺，f1c30/f1ca0/f2648 完整 stop/reset 不计完成。剩26条差异及两个未知；完整 observer 替换、SDK weak owner/释放后ack、FRC/实体/DI/ABI/并发重入继续开放。

833 项源码/静态检查通过，新增16项，绑定26原片段、4真实descriptor和前轮重试证据；覆盖嵌套闭包的实际目标、错误不启动、whole-reset重试、全量请求合并、单次初始启动、nil-state后续清理和未改的target/SDK内容/查询/retry算法。Python流程fixture不执行Swift/SDK。初817项有10处旧断言失败和13处旧定位错误，日志保留；8份旧测试重新绑定真实initializer/clear的消费者，或允许新增full-request标志，同时继续检查原合同，没有构造虚拟合并源码蒙混通过。修后817及新增833全绿。

仅一份生产文件改变，232份不变，无新增生产文件。未实际sleep、原生/数据库/应用执行、编译、联网、提交、推送或发布；官网九文件、版本1.0.2、HEAD与function-map不变。搜索P1仍唯一in_progress。

[机器证据](p0-p1-repair-round51.json) · [补丁](p0-p1-repair-round51.patch)
