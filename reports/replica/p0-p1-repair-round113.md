# 第一百一十三轮：共享记录投影的分组类型门控

原31bc94读取Item.list，nil返回nil；非nil再经3250f0检查rawType==2，否则丢弃该owner。Pasto native预览和搜索记录投影已限制type2，但ClipboardPersistence.item只检查identifier能否转UUID，就会设置pinboardOwnerID并插入pinboardIDs，普通Store读取可能与索引/原生菜单不一致。

本轮仅在共享item投影的identifier读取前补rawType2条件。该方法供snapshot read/search/searchNativeItems、item observation、restore handle值适配和native unassign cache-miss回退使用，因此同步修正这些消费者的native owner判断。归档中已有pinboardIDs继续保留，nil-owner只清ownerID；不改旧有效多组成员、不加schema/迁移标记，也不删blob保存。

当前reader仍把native owner插入归档集合，而非替换。若直接删除compatibility content写入，重读可能复活旧成员；需要单独核清旧成员/原生关系优先级，不能以简单清空旧数组制造表面一致。本轮不宣称完成存储架构或性能迁移。

2原片段、3实际branch、5ARM字绑定。1生产文件1精确增量，246生产文件、4共享源及7消费者方法保持。10新增检查，1731项Python源码/Mach-O静态检查通过；2历史工具/测试仅逆隔离后续增量，无本轮失败，未改旧证据摘要。既有低模型只读确认真实消费者和旧归档风险。

31bc94/3250f0已计入v35，修复另一个value适配消费者不增加地址数或台账版本：P0 70/70、P1 122/122，总192/192（100%）保持。该分母是已确认有限差异，整体迁移及完整父合同仍未完成。分组兼容/模型DI/fault/save回到pending，继续Stack原生记录删除后的处理、渲染与owner生命周期；两未知04430c/0f733c保持。

未编译、构建、安装、运行应用/框架/CoreData、联网、提交、推送或发布。官网9个本地改动、1.0.2版本、HEAD和function-map保持。
