# 第四十八轮：索引错误、监听与取消

按原 f2468/f2a30，索引失败只记录错误并返回至 delegate ack，不额外设置 needsReset；显式全量重置与来源身份变更仍可请求清理。删除只服务该旧错误策略的 journalCompleted 变量。成功清理之后、读取初始 native ID/写 SDK 之前即安装变更监听，保持原 f00dc/f14cc 顺序；后续普通请求不因失败快照尚无 observer 而自动再跑全量。清理之前失败的完整重启策略仍待独立活动状态迁移，不能把本轮算整条错误生命周期完成。

指定 ID 按原 ea78c 先过滤空 String，保留重复和顺序，再按 100 输入 ID 分批。Task 已取消时在下一批取数前正常退出；SDK 回调错误仍向上返回并记录，不能把 SDK 返回 CancellationError 也无条件吞掉。已成功批次与缓存保存尾部不变，独立 isRunning 门仍缺，三条 target cancellation 记录不关闭。

本轮补真实原类 descriptor/accessor/20 项 field-offset vector：isRunning=0xf0、ocrTask=0xf8、changeObserverTask=0x120。原 stop 立即清 active，取消/清 observer，不等待 observer；再取消并等待 OCR task。**纠正旧报告把等待对象泛称为旧全量索引 worker 的解释。**成功初始化保持 active=true，失败才清 false；当前串行 worker 句柄不能代替该状态。真实 OCR 队列/重试/stop 等仍需继续迁移，不虚造一个等待当前全量 worker 的实现。

| 固定有限差异清单 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 49 | 81 | 60.49% |
| 合计 | 118 | 150 | 78.67% |

关闭 f2468/f2a30 两条共用错误 flag 差异；另复核真实 c3ec18→f3cdc→f2648→f1c30，复用上轮系统 reindex 无 UI requested 门修复关闭 f3cdc。三条不是三个独立 bug；未重复增加已关闭的两个 delegate 入口。监听/target 取消和空值修复不另外扩大完成数。剩 32 条差异及两个未知入口，完整父合同/全部原函数仍未闭合。

780 项源码/静态检查通过，新增 18 项；30 原片段、原 class descriptor/accessor/offset vector 与真实 full callback descriptor 已绑定。检查错误不触发 reset/额外调度、显式重置保留、观察与取数实际顺序、空 ID/重复与批次边界、局部取消、SDK 错误传播、ack 恰一次及未改的状态/查询/Token 链。Python 决策 fixture 只证明源码合同，不执行原生任务或 SDK。初 762 有六处旧形态断言失败及一处旧定位错误，保存日志；五份旧测试按新合同更新或冻结历史全方法证明，并继续验证当前 flag/target 尾/ack，修后 762 与新增 780 全绿。

主审沿用用户授权的低模型只读子审核生命周期，再独立读取字节重绑字段偏移，校正子审及旧报告泛化。仅一份生产文件改变，232 份不变，无新增生产文件；官网九文件、版本 1.0.2、HEAD 与 function-map 不变。未编译、运行应用/原生/数据库、联网、提交、推送或发布，搜索模块仍为唯一 in_progress。

[机器证据](p0-p1-repair-round48.json) · [补丁](p0-p1-repair-round48.patch)
