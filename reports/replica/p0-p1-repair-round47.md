# 第四十七轮：系统索引重建入口

原 2e477c 经真实 async descriptor→2e4c4c→2e4660→2e467c，weak-load indexer 非空就调用 2f2268→2f2280，无界面 requested 门。Pasto 原先在对象仍存活但尚未收到 UI update 时直接 ack 并退出，已删除该多余条件。

现在构造临时 Request，使用当前 entries、queryNodes 与真实 store identity 并进入同一 pending worker；不写回 requested，不触发查询替换或 UI 发布。full delegate reset 继续覆盖状态恢复。全量 ID 与实际记录仍从 store 独立读取，UI entries 仅是无 store 的兼容来源；该适配不等于已证明原 dataSource 全生命周期同构。

| 固定有限差异清单 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 46 | 81 | 56.79% |
| 合计 | 115 | 150 | 76.67% |

只关闭旧 2e467c/2e477c 共用的 requested=nil 门，两条不是两个独立 bug，不升级完整函数。目标 ID delegate 同样移除了此门，但 namespace 筛选仍不同，2e48a0 不关闭。SDK write weak service owner、2e46fc/2e4928 操作后先释放 owner 再 ack，以及原 actor active/stop/wait、取消错误/FRC/实体/DI/ABI 继续开放；剩 35 条差异及两个未知。

762 项源码/静态检查通过：新增 12 项，另纳入 4 项既有 ack/重入/descriptor 检查。绑定 14 原片段与两个真实 async descriptor，验证 nil owner 立即 ack、nil requested 正常入列、实际 store 输入、查询不变、target 分支/worker/ack 不变及 Python 门决策表。主审与此前用户授权的低模型只读 agent 均复核原分支；未执行原生回调。初 746 有一处旧全方法相等断言失败，保留日志，冻结历史证明并继续比较当前 target 分支和 ack 尾后全绿。

仅一份生产文件变化，232 份不变，无新增生产文件。未编译、运行应用或原生框架、联网、提交、推送或发布；官网九文件、版本 1.0.2、HEAD 和 function-map 不变。目标继续进行，搜索模块唯一 in_progress。

[机器证据](p0-p1-repair-round47.json) · [补丁](p0-p1-repair-round47.patch)
