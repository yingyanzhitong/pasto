# P0/P1 源码修复：第二十七轮

当前仍先修P0，再集中检查P1，最后修复P1。本轮显式选区滚动不再主动enqueue并同步drain未来快照：原228c78写SelectionManager后将选区末端数值索引传22c9c4，后者只读当前layout/clip并滚动，交集卡片即时成功回调；Pasto旧revealSelection却先update/drain，再按ID找目标，改变了同一输入里的数据和选择。

现在revealSelection先核真实owner，在applied项中找端点，不发布/排空新数据。成功完成回调仍携带原请求索引；selectionDidReveal从完成时的applied数据解析该索引，再校验visible cell，交给已有popover入口。原228e1c委托+20经eb26e8→06f294→075e3c，consumer确实经1b9698读取applier。即时交集回调不会偷跑排队结果；异步滚动期间另有新快照正常到达时，回调按新applied请求索引解析，不缓存旧端点item。

| 当前有限差异 | 已修复 | 分母 | 比例 |
| --- | ---: | ---: | ---: |
| P0 | 51 | 68 | 75.00% |
| P1历史依赖 | 8 | 81 | 9.88% |
| 合计 | 59 | 149 | 39.60% |

新增075e3c有限回调来源差异1条，v6分母149；228c78只是扩充既有修复域，不重复计数，旧148条保留。余P0 17、P1 73，共90条有限差异及2未知；该比例不等全函数/全部应用完成率。

458项Python源码/静态检查通过，新增10项。1个旧测试撤回无原代码依据的“reveal必须flush”要求，previewAnchor现有适配保留；未为旧断言撤销正确修复。绑定11个原C片段和1416字节数据（352条机器指令），复用已绑定applier/delegate安装。2旧生产文件变化、225个不变，无新增生产文件。

外部selection在普通生产源码中只见applyOrderedSelection受控赋值和chooseBoard显式清空，未找到独立鼠标/键盘setter入口；不据未来投影猜改reconcileExternalSelection，也不把有限搜索当完整动态可达性证明。原075e3c尾0679ac反馈IDs及其注入生命周期、provider实体、缺项/重入、popover存在/显示和previewAnchor适配仍未完整迁移。

下一批回到P0原清单的面板show/visible/close/coordinator合同；面板生命周期与焦点唯一in_progress，快捷键与选区pending保留父合同，不标模块完成。未编译、构建、安装、运行应用/框架、联网、提交、推送或发布；官网9文件、版本1.0.2、HEAD与全函数台账不变。见[JSON](p0-p1-repair-round27.json)、[补丁](p0-p1-repair-round27.patch)及[v6差异清单](p0-p1-difference-backlog-v6.json)。目标仍进行中。
