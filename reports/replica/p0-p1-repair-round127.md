# 第一百二十七轮：数据读取异常的本地诊断

原31b218的Ghidra输出删除了一段真实存在的异常分支。ARM证明错误非nil时，从ItemDataEntity的logger字段取命名sink，发送level3日志，消息前缀为`Unreadable pasteboard items blob: `并插值error，然后返回空数组。31b494构造时创建名为ItemDataEntity的wrapper，31b59c析构时释放；该logger与后续telemetry字段/回调不同。

Pasto此前catch到Objective-C异常直接返回空数组。本轮补同名level3日志，再返回空数组。为保持既有本地NSManagedObject模型和兼容迁移，记录器用retained关联存放在对应data对象上，首次异常创建、同对象重复异常复用；不建全局对象池。原NamedDiagnostic内部仍首次取sink时读DI并缓存，代码原文保持。正常读、缺关系、普通Swift错误、codec、模型、替换、迁移和复制尾均不改。

这是明确的兼容适配：原wrapper在实体构造时创建，本地在首次异常时创建；并未复刻原字段布局。异常name/reason已经由本地bridge保存，但Swift错误类型描述的精确插值文本未保证逐字一致，不声称整个31b218完成。后续callback另取telemetry字段并经DI，构建`source: item-data.read`字典；x25在回调前已改为字典，不能误称原entity或本地logger。最终协议/receiver仍待可靠绑定，未凭slot猜实现。

1个生产文件3个精确增量，246文件不变；7原片段、5个实际调用、32个ARM字、3个不变方法、7个共享源及本地SDK声明文本已绑定。14项新增源码/Mach-O检查，累计2012项全部通过；3个历史测试/工具7处精确逆向隔离，旧proof保留。未编译或执行Objective-C/CoreData/系统框架。

本轮是读取函数的部分本地副作用修复，不把它新增计为完整函数。v39保持P0 77/77、P1 124/124、总201/201（100%）已确认有限差异；整体迁移率未知。按P0修复→P1检查→P1修复执行，当前对P0具体源码与兼容/运行边界作最后收口。

仅本地修改；未编译、构建、安装、运行应用或框架、联网、提交、推送、打标签或发布。官网9文件、版本1.0.2、HEAD与function-map保持。
