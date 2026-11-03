# 第九十四轮：预览原生实体通知与删除关窗

本轮继续P1编辑链。新定位的原版实际消费者07c994从viewModel metadata+0x88取得publisher，sink经07d078交07b8cc。07b8cc先读实体isDeleted：删除时取消标题编辑011d28，再对所属window执行performClose；非删除才调用011e00更新标题、分享及分组外观。原model 3c2780发布实体，不代替UI过滤删除。正文3c04f0的删除忽略门与此不同。

重要证据纠正：上轮依反编译伪代码认为3c25dc初始化Published(nil)，该判断已被ARM推翻。3c261c把输入实体x0存到sp+8，随后零参数只是给类型metadata accessor；3c263c又把sp+8原实体槽作为Published.init输入。metadata fc2da8+0x40绑定ItemPreviewViewModel描述符，+0x88实际槽fc2e30指向3c2438。原初始实体发布与真实sink现已绑定；旧报告保留为历史，本报告覆盖其nil解释。

Pasto的ClipboardRestoreItem新增原生变更订阅，强持实体及context，以context和objectID匹配insert/update/delete/refresh；交匹配到的实体，不先读取删除标志，不投影，不另做UUID查询、异步或去重。原生header初始值和后续通知共用弱捕获消费者，先检查物理删除，删除时取消标题编辑并关所属窗口；非删除才读取当前投影，复用既有标题/share/pin显示代码。两个真实预览factory均传input。正文观察器、提交和分组动作保持不变。

1415项源码/静态检查通过，新增14项；旧1401项也已单独通过。绑定15原片段、14实际调用、12指令及2个dyld链指针，8个原动作/方法和5份共享源码保持。2个生产文件修改，其余245个不变。2个历史测试/工具仅对6个精确增量做可逆隔离；首轮25失败/2错误及测试辅助定位/导入逆变换错误日志保留，辅助已修，新测试闭包定位问题也已修。没有删除、跳过旧测试或覆盖旧证据。

| 已确认有限差异 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 70 | 70 | 100% |
| 额外P1 | 96 | 97 | 98.97% |
| 合计 | 166 | 167 | 99.40% |

本轮为已有实体/编辑父合同的部分迁移，不增加完整函数计数。普通popover尚未传input，header仍走Store.$items适配；独立pinboards订阅、纯分组关系通知、非文本更新、投影错误、完整Published模型/DI/ABI、3544dc和Stack/选区生命周期及04430c/0f733c继续开放。没有完成原版全范围或运行验收。

主智能体修改，复用1个既有低模型智能体只读核ARM纠正、真实消费者与引用寿命。未编译、执行框架/数据库/应用、联网、安装、提交或发布；官网9文件、版本1.0.2、HEAD与function-map保持。

[机器记录](p0-p1-repair-round94.json) · [源码补丁](p0-p1-repair-round94.patch) · [有限差异清单](p0-p1-difference-backlog-v20.json)
