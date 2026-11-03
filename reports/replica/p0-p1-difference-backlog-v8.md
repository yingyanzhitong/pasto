# P0/P1 有限差异清单 v8

保留 v7 的 150 条记录和 137 个组，补纳两条新确认的本地搜索重试合同，合为一个共享重试策略组：

| 原地址 | 有限合同 | 实际消费者 |
| --- | --- | --- |
| 0x1002e39b4 | CSIndexErrorDomain 且 code=-1000/-1003 才为瞬态错误 | retryTransientIndexErrors 的每次失败分类 |
| 0x1002e7914 | whole-operation 最多三次尝试、1秒/2秒连续时钟等待、成功清计数、瞬态耗尽加计数、普通/睡眠错误传播 | 系统 target delegate 的整个 reindexTargets pass |

当前分母 152：P0 69、P1 新增 83；保守分组 138（P0 64、P1 74）。两条属一个真实调用链，不是两个独立 bug。原 wrapper 自身的帧分配不作为业务合同；797c/7a14/7e4c 才提供实际重试分支。全量 delegate 也使用原 helper，但当前该外层 reset retry 仍未接，不把 helper 接入 target 等同全部 caller 已完成。

v7 与历史 review-scope 不改写；该扩表不代表完整原版 P0/P1 分类已闭合。修复状态由 round50 overlay 给出，完整函数标记仍 false。

[完整机器清单](p0-p1-difference-backlog-v8.json) · [本轮证据](p0-p1-repair-round50.json)
