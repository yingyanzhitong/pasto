# 第六十二轮：索引委托 owner 与完成回调顺序

原版先释放本次索引操作持有的indexer，再切到无actor executor的续体调用SDK acknowledgement。当前nonisolated委托任务只持weak target、IDs和SDK回调；独立helper强取indexer并等待实际队列操作，helper返回后，外层任务才调用SDK回调。缺owner直接结束helper，仍会回调。

队列内保存的closures现在只恢复checked continuation，成功/错误都能结束等待；drain主体和batch/reset/raw IDs/retry/OCR保持原样。其他队列任务仍可能独立持有indexer，本次只移除delegate操作的捕获范围，不要求对象立即析构。

| v12有限清单 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 82 | 90 | 91.11% |
| 合计 | 151 | 159 | 94.97% |

关闭全量2e46fc和定向2e4928的两条共享有限顺序差异，余8条差异及2项未知。单独的2e20b8 SDK写入前弱owner合同继续开放，不能用这次delegate weak target充当其修复。完整原actor/DI/ARC/ABI及运行时调度尚未验证。

967项源码/静态检查通过，新增10项；11原片段、18条ARM字和weakLoadStrong/release/task_switch三个真实导入绑定。9份旧测试跟进真实enqueue或冻结历史hash继续核当前方法；初957的7断言/10定位失败日志保留，后续定位错误已修，最终967全绿。主智能体与一个低模型只读复核未发现本次新增的漏回调、双resume或reset/target/OCR接线遗漏。

1份生产修改、232份不变；官网9文件、1.0.2、HEAD和function-map不变。未编译、运行框架/应用、访问数据库、联网、提交或发布。

[机器证据](p0-p1-repair-round62.json) · [补丁](p0-p1-repair-round62.patch)
