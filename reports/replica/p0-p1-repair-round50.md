# 第五十轮：本地索引瞬态错误重试

真实 target delegate 现在按原 2f26a8→2e7914，对整个 reindexTargets 操作重试；某批写入失败后重新执行该 pass，不是只重复失败批次。分类只接受 CSIndexErrorDomain 的 -1000/-1003，总共最多三次尝试，等待 1 秒、2 秒（ContinuousClock）。成功清共享连续瞬态失败计数，只有三次均为瞬态失败才加一次；其他错误、等待失败/取消直接传播。原 threshold5 遥测仍排除，不新增用户告警。已运行服务的 active、批次顺序/重复、SDK flag、cache/ack 及 target-only 初始化门不改。

这两条原合同此前未进固定差异表。已根据原真实消费者、domain 的 ADRP/LDR→format6 导入 _CSIndexErrorDomain、ARM CMN 的两条负数比较、DI 传入 Duration(1e18,0) 及本地 Swift Duration attoseconds 缩放实现补纳 v8。旧 v7 的150条记录/137组完整保留，新增两条属一个共享重试策略组；不能凭 wrapper 帧分配当业务差异。

| v8 有限差异清单 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 56 | 83 | 67.47% |
| 合计 | 125 | 152 | 82.24% |

本轮关闭新纳入的 classifier 2e39b4 与 helper 2e7914 有限合同，不是两个独立 bug 或整函数/全部 caller 已迁移。当前只接 target 外层，原 full delegate reset 也使用该 helper，那里尚未接通。剩27条已确认差异及两个未知；全原版分类仍未闭合，历史 review scope 不改写。

817 项源码/静态检查通过，新增17项，旧800项无需修改。绑定20原片段、真实domain导入/负数立即数、SDK头及Swift Duration源码，核三次上限、1/2秒时间单位、普通/睡眠错误、计数、实际whole-pass消费者、旧batch/查询/请求类型不变及Python故障序列。fixture不执行Swift/睡眠/SDK。仅一份生产文件改变，232份不变，无新增生产文件。

用户授权的低模型只读子审另定位OCR队列。未实施也不加分；主审拒绝其重复的“SDK提交过滤空文本”误述（原完整数组写入早已ARM确证），并用Duration字段/SDK修正“2e18纳秒”为2秒。可选witness字段名、OCR service返回及写回payload继续逐链核对。完整OCR queue/stop await、observer替换、full reset/retry/SDK weak owner/释放后ack、FRC/DI/ABI仍开放。

未实际sleep、运行原生/数据库/应用、编译、联网、提交、推送或发布；官网九文件、版本1.0.2、HEAD和function-map不变。搜索P1仍唯一in_progress。

[机器证据](p0-p1-repair-round50.json) · [补丁](p0-p1-repair-round50.patch) · [v8清单](p0-p1-difference-backlog-v8.md)
