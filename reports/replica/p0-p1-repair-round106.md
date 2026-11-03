# 第一百零六轮：分组菜单保留目标实体

原09e8a8在构建已有分组action时分配0x30 closure，+20保存输入数组、+28保存当前List对象；实际09e9d4调用_objc_retain，真实heap metadata-10指向09f20c，析构从+28读取并_objc_release。09f240加载同一目标，经09ee9c、076320、09e5a4传入3b9a78，未在点击时按标识符重查List。绑定13原片段、5实际branch、13ARM字和1个真实format6 metadata指针，未把Ghidra删除的retain/release当成弱持有。

Pasto新增opaque ClipboardPinboardTarget，由Store/Persistence在同context菜单构建时解析并强持List；Button闭包捕获它，专用State/Store重载将同对象交共享原生分组事务。事务有捕获对象时直接使用，旧UUID入口仍在原事务位置解析。原moveItems、仓库assignItems、旧orderedIDs/unassign和新建组方法5处保持；既有组新增target路径不改变已迁移的移动排序逻辑。

本轮5生产文件、7精确增量，242生产文件保持。2历史测试工具只反向隔离本轮增量，18新检查直接读取当前源；1606项Python源码/Mach-O静态检查全绿，旧1588也先独立通过，无本轮测试失败。独立只读复核确认public/internal类型边界、MainActor及两个overload静态选择；未使用Swift编译器，不声称编译通过。

有效本地组菜单为本轮有限域；工厂按UUID解析的原生List集合来源尚未完全迁移，未解析target/mixed value会保旧路径。rawType2来自当前pinboards实际枚举，未加无证据的额外类型或isDeleted门。SwiftUI菜单重建、已删除/失效对象、创建组后的原始List返回、preview-header pin、nil/unassign、完整上下文与错误生命周期仍开放。

v29原样保留v28全部181条/165组，新增并修独立目标捕获09f240一条：P0 70/70、额外P1 112/112、合计182/182（100%）。仅代表已确认有限差异清单，未升级完整函数，不能据此称整体迁移完成。两未知04430c/0f733c继续保留。

未编译、构建、安装、运行应用/框架/CoreData、联网、提交、推送、标签、发布或部署。官网9本地文件、版本1.0.2、HEAD与function-map保持。下一步继续P1分组的真实消费者和原native集合来源，P2排除。
