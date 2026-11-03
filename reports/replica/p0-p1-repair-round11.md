# P0 → P1 源码修复：第十一轮

| 范围 | 已修有限差异 / 固定差异分母 | 进度 |
| --- | --- | --- |
| P0 | 37 / 64 | 57.81% |
| P1（P0依赖） | 5 / 81 | 6.17% |
| 合计 | 42 / 145 | **28.97%** |

本轮补齐已计父地址 `069fe0` 的E/Shift-E及真实生产消费者，不重复计分。仍有103条已证差异和2个未知入口；这不是完整函数或产品完成率。旧比较结论覆盖仍为654/656（99.70%），不能当迁移完成率。

## 本轮实现

Command+E使用集合已显示快照中的有序选择，缺失项跳过。先收集全部可编辑内容（原类型1/2/4/5），空结果提示；否则按原顺序逐项进入已绑定的Router显式窗口流程。

新窗口先登记registry和编辑标记，再创建内容、连接结束/状态回调并开始编辑。显式WindowTransition同步设置delegate、fittingSize、contentVC、makeKey、orderFront，随后运行呈现回调：居中后按已登记窗口数×30级联，仅夹右/底边。路由返回后文本设置首响应者；Color/Image/Link的该焦点witness为空操作，不重复开始编辑。关闭先释放contentVC，再移除transition保活引用；registry继续使用既有关闭观察清理。

Command+Shift+E先查系统能力，再筛选可编辑的文本项；空结果返回false且不提示，非空经同一编辑路由后启动MainActor任务。ContinuousClock等待500毫秒，成功和取消/错误后均继续发送 `showWritingTools:`，target/sender均nil。没有强行绑定某个文本视图，保留系统响应者解析。

## 证据与边界

从生产构造的metadata/witness两槽追到实际Router conformance，再到显式窗口方法；四类Editable的末槽也已绑定，文本最终为 `214474` 的makeFirstResponder。窗口show、orderFront、onPresented、返回后焦点的时序由原代码及机器码核实。

macOS26能力门采用SDK的 `@frozen` 单payload、唯一empty case形状，结合UnavailableReason的VWT单payload空tag构造和真实Availability比较导入，静态推论为 `.available`；没有将literal1当源码case序号。15.2–25检查NSText selector，更早返回false。现代SDK26+才覆盖FoundationModels分支；旧SDK缺框架时的保守false是适配，不声称完全等价。

285项源码/原始数据静态检查通过，含24项新增检查，旧测试未改。本轮改3个现有生产文件、新增2个实际接线组件，其余218个与备份一致。泛型Route/Scene/DI、显式orderOut(false)、编辑标题按钮、非nil sender及完整会话未据此宣称迁完。

未编译、安装、运行Swift/AppKit、联网、提交或发布。实际编辑、窗口尺寸、AI能力及系统响应者行为未做运行验收；版本与全函数台账不变，官网等仍仅保留本地。

[完整记录与源码绑定](p0-p1-repair-round11.json) · [源码补丁](p0-p1-repair-round11.patch)
