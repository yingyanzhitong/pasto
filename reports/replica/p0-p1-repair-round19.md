# 第十九轮：原生搜索协调器、焦点与查询交付

当前有限差异修复 **52/145（35.86%）**：P0 **44/64（68.75%）**，P1依赖 **8/81（9.88%）**。本轮关闭00e74c的真实子调用/布局、040054的活动焦点策略、2f7d60的清空Undo策略、2f7744的正常FilterBrowser mode0顺序四条已证有限差异。仍余93条差异和2个未知入口；不是完整函数、模块或全产品完成度。

搜索栏直接持有同一原生field/coordinator，不再通过NSHostingView子树查找输入框。原有NSViewRepresentable、Binding焦点和requestedFocus转接已移除。setActive先更新alpha及两层canAcceptFocus，再进入原nil duration/easeOut嵌套动作；active且popover未显示、有window时请求textView焦点，inactive执行协调器reset、额外公开query，再释放first responder。上两轮的原生标签和toolbar布局动作接在其后，调用顺序有实际消费者。

保留Core SearchField的onClear(false)接口；SearchBar桥按原040c64忽略这个参数并选mode1。非空query清空时先更新内部query、记录空快照、绘制、发布，再清空建议；mode1不额外清Undo，关闭mode0才清。相同query不再重绘或发协调器回调，mode0仍执行历史reset。FilterBrowser有live owner时也先交协调器再发布state，无owner保留既有本地fallback。

额外核实了原模型订阅：03e9bc经03fe8c过滤空query；非空才经03ff40先做03e658的焦点/关闭判断，再交mode1协调器。当前同步订阅保留这条非空门，计时器的空query继续由onDismiss清理，没有提前走协调器一次。重复公开query仍交真实searchQueryChanges subject；对相同text/filters不重复写SwiftUI字段，保留实际查询订阅及debounce的交付。非空外部输入遇到空协调器时可能先关闭再继续该次输入，这是原链的有限重入顺序，未擅自加取消门或改成异步。

383项Python源码/静态检查通过，另增13项。此前370项中2项按原生输入所有权和重复query交付更新，其余不变；原344项未修改。绑定26个原C片段、3段共72字节ARM数据及227个生产文件摘要。本轮改4个已有UI生产文件，其余223个不变；Core清空接口、历史实现、原生标签栈、网络代码、版本及全函数台账未改。

保留边界：mode1全部suggestion/builder/restoring/IME/重入语义、完整SearchBar/FilterBrowser生命周期、wrapper默认约束与阴影、延迟工作项取消及原responder父合同尚未全部证明。SwiftUI挂载后焦点重试、UUID显式focus和text/filters模型拆分是Pasto集成适配，不宣称原ABI或完整初始化一致。未编译、运行Swift/AppKit或应用、联网、提交、推送或发布；官网等仍仅本地。

P0面板生命周期与焦点继续in_progress，下一步处理原延迟工作项、取消门和剩余父链，再处理P1常规模块。

[完整记录及文件摘要](p0-p1-repair-round19.json) · [源码与测试补丁](p0-p1-repair-round19.patch)
