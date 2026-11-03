# P0 → P1 源码修复：第四轮

| 范围 | 已修有限差异 / 固定差异分母 | 进度 |
| --- | --- | --- |
| P0 | 32 / 64 | 50.00% |
| P1（P0依赖） | 5 / 81 | 6.17% |
| 合计 | 37 / 145 | **25.52%** |

本轮新增2条有限合同：事务内operation显式参数交付、receiver所属仓储惰性缓存。仍有108条已证差异和2个未知入口；这不是全函数或产品完成率。

- 业务修改闭包、增量写入与有变更才保存进入同一performAndWait；提交返回后再读取revision和发布状态。
- 每次提交新建Transaction，绑定同一context并惰性缓存ManagedRepository；真实增量写入复用该实例，容器寿命保持到perform返回。
- 新建Item先取得永久ID，成功后才写key和字段；失败抛错并阻止保存与状态发布。该地址之前已有有限修复计数，本轮不重复计入。
- 原寄存器链已厘清：operation输入是repo getter的receiver；owner的+0xa0状态来自另一捕获字段。修正了旧子报告全局缓存/隐藏返回参数解释。

177项Python源码、原片段与ARM64数据静态检查通过。2个生产文件改变，217个与本轮备份相同；未编译、安装、运行应用/框架、联网、提交或发布，台账与版本不变。

完整DI、原实体Sequence、repository witness、Undo及保存失败状态仍未闭合，2ff310和37ade4不计完成。first-fetch后的refresh虽有原证据，具体谓词/排序尚未绑定，未猜测移植。

[逐地址与最终源码绑定](p0-p1-repair-round4.json) · [本轮源码补丁](p0-p1-repair-round4.patch)
