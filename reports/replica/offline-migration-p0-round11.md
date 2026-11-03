# 离线迁移第十一轮：搜索双流、结果保留与时间排序

2026-10-29。只做已有反编译代码/原二进制静态读取、源码修正及 Python 源码检查。未编译、构建、安装、运行 Combine/Spotlight/应用或原函数、联网、修改用户历史、提交或推送。

## 对照后落实的修正

**搜索输入和列表切换是两条流。** 原 `0x10007e194` 的搜索条件在 main RunLoop 防抖 120ms 后去重，传给 SearchVM；`0x10007daa8` 独立防抖 120ms，再 prepend 一个空 query、去重，并把非空条件映射到同一 searchVM。与 selectedList 形成 CombineLatest 后，`0x10007eac0` 令 searchVM 优先，空时回到所选列表。不能只在索引 worker 里延迟一次。

Pasto 现安装并持有两条独立 weak 订阅，保持上述 debounce/prepend/removeDuplicates 顺序。原始输入节点仍即时用于搜索框显示；索引只接收已送达的 query，卡片列表只使用已生效的上下文。数据维护刷新不会重新发送输入或重置防抖。删除、拖拽、Esc、关闭后 history 恢复/超时也读已生效上下文；上下文切换取消旧的面板内删除确认。这样不会在 120ms 窗口里，以新输入的搜索条件操作旧列表。原生对象图与两条流的实际时序仍没有运行验收。

**换查询时保留现有结果。** 原 `0x10035ff00 → 0x100364960 → 0x1003646a8 → 0x1003600a0` 取消旧任务并安排新任务，开始时不清结果 subject。结果由 `0x100360808` 在查询完成后替换。Pasto 原来 update 立即清 identifiers，现移除这次提前清空；已有 pending/request 检查继续阻止旧查询发布。

**取消与失败分开处理。** 原 `0x1003601e0 / 0x1003602fc` 明确识别 CancellationError，取消直接退出保留原结果；其他错误记录并走空结果处理。现无新 pending 时，只有非 CancellationError 才发布 error/清结果；取消不再作为普通搜索失败显示。每 query Task、原 logger、后台投影与切 MainActor 的完整对象/执行器合同仍为 partial。

**搜索按历史时间排序。** 原 `0x100360808` 以 identifier IN 构造 ItemEntity fetch，经 `0x100329754 → 0x1003298a0` 使用类的 defaultSortDescriptors。`0x10031f2a4` 明确为 timestamp、ascending=false。Pasto 搜索结果原按 updatedAt 排序，编辑文本/标题可能改变位置；现通过原有 `isInHistory / createdAt` 兼容字段投影历史时间，有时间在前、时间倒序，无历史时间在后，不额外编造 tie-breaker。自有非可选日期与原 nil timestamp/Core Data 关系仍有适配边界，不能据此计为完整原函数。

## 静态字节与检查

两条实际位置 `0x10007dcb8`、`0x10007e5f0` 均为 mov w0,#120，随后同样调用 `0x100bf915c`；解析真实 dyld 声明链确认它绑定到 Foundation RunLoop Scheduler Stride.milliseconds。原 defaultSortDescriptors 的 timestamp 小串由 `0x10031f2f8` 的 MOVZ/MOVK 序列确认，`0x10031f320` 为 mov w3,#0。另从真实 ObjC stub 读取 selector slot，确认 defaultSortDescriptors。全部原片段摘要、字节、指针说明与当前源码快照见 [机器记录](offline-migration-p0-round11.json)。

**117 / 117** 项 Python 源码、台账与静态证据检查通过，新增 **13** 项。覆盖双流/原操作顺序、反例拒绝错误延迟/漏初始空值/漏去重、输入原子发布、数据刷新不重置防抖、可见/删除/拖放/关闭消费者、换查询保留结果、取消/失败分支、原排序字节与时间字段投影。此前 Esc、关闭 timer 和删除作用域的检查已随更强的原上下文证据更新；旧轮报告作为当时快照保留，不改写成当前编译或运行验收。

## 边界与总进度

本轮核对 **26 个原地址**，其中一个曾核对的父入口因投影改动重新复核；新增 **5 条 partial**，partial 合计 **439**，新增完整迁移 **0**。十一轮去重累计 **342 / 81,123 = 0.4216%**。历史完整标记 **1,648 / 81,123 = 2.0315%** 仍含过期证据，不是当前软件全量完成度。

仍有确定差异：`0x10007d9c8` 的用户选择列表入口先清搜索再选组，当前 chooseBoard 同时承载用户操作和闭窗 create/restore 程序路由，不能机械统一清 query；需要分清实际消费者再迁移。索引 contentModificationDate 的真实 witness、原 Task/DI/FRC 生命周期与缺项日志、optional/多组/UUID 投影也继续待证，本轮未凭猜测修改索引日期来源。目标保持进行中。
