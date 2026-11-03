# 第二十轮：关闭态使用原版全局恢复通知

当前有限差异修复 **53/145（36.55%）**：P0 **45/64（70.31%）**，P1依赖 **8/81（9.88%）**。本轮只关闭021518通知范围与交付的有限差异，仍余92条差异及2个未知入口；不是完整函数、模块或全产品完成率。

原385984使用scheduled NSTimer，385af0析构会invalidate。当前本来就使用10秒单次Timer，UIController.deinit、重开和两条通知路径也已显式取消。此前“需要迁原延迟工作项”的计划不应被理解成改为Dispatch；这部分有限合同已经一致，未替换Timer、未添加冗余包装，也未据此加分。

真正差异是021518的两条NSNotificationCenter.publisher均以object=nil直接订阅，而Pasto的DidCreate使用queue.main observer、DidRestore仅订当前store私有subject。现在恢复生产者在Undo清理后，以恢复store为object发出原名pasteboardHistoryManagerDidRestoreItem；关闭态统一用两条object=nil publisher直接交付，AnyCancellable在同一取消入口清理。恢复上下文门、选择history、timer回调及取消仍复用现有实现。

原通知名由ARM初始化器与Mach-O字符串字节验证，创建/恢复名称长度分别为37/38。保留旧didRestoreItem subject用于现有本地音效，置于全局通知之后；关闭态只监听全局通知，不订两路导致重复。音效源码没有修改，未推断其与原全部消费者的先后完全一致。

“另一个manager对象发出恢复事件时，原object=nil仍接收、旧store subject忽略”是源码合同反例。当前AppMain通常只有一个主store，MCP在另一进程；本轮没有声称已复现真实多store UI故障或跨进程广播。错误线程事件也没有被静默搬到main，仍保留MainActor边界。

393项Python源码/静态检查通过，新增10项。3个旧测试文件按真实通知producer、AnyCancellable取消及单个新增声明调整：恢复失败仍继续Undo/通知的断言保留，存储/联网实现仍逐字核对，未为满足旧字符串而保留死observer。绑定18个原C片段、两段共104字节ARM初始化器与75字节通知名、全部227个生产文件摘要。改3个旧生产文件，其余224个不变。

保留边界：ClosedStateManager DI/所有权图、完整context/Trash映射、回调重入和恢复父合同仍未闭合；新增全局通知不代表这些已经完成。未编译、运行Swift/AppKit或真实通知、联网、提交、推送或发布。版本、全函数台账与官网9个下载修复文件保持原值。

P0数据与删除安全转为唯一in_progress，继续历史恢复/清理、删除确认与邻项消费；面板模块保留pending及既有部分证据，不标完成。

[完整记录及文件摘要](p0-p1-repair-round20.json) · [源码与测试补丁](p0-p1-repair-round20.patch)
