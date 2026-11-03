# 第一百四十七轮：Stack 关闭所有权与会话队列

按P0修复→P1检查→P1修复继续。上一轮修表拖动许可，本轮追真实AppCoordinator创建和关闭父类，不重复只看孤立close/dealloc的旧结论。

早期84轮正确保留“不能由close单独推断销毁”的缺证。本轮找到原0a9534实际显示/关闭调用者：0a85d8只在协调器+d8为空时创建Stack controller，217e4c保存完成闭包并showWindow。真实闭包0a9998→0a86c0弱加载协调器后，ARM先读旧+d8、写零，再释放旧controller。原StackWindowController的父类确为PasteUI.WindowController，两个实际metadata+108槽均指2182a4，因此2184dc的动态close确实到该父逻辑。非模态分支先super.close，再调用completion、清completion、清contentViewController；真实setContentViewController: stub与selector已绑定。084f14归档构造明确从空snippets开始，083d18析构释放snippets，不再靠猜测推断会话队列。

此前Pasto hideStack只close，仍保留窗口、controller、NSHostingView、observer和全局队列；stackIDs每次变化还写入偏好，启动又恢复旧队列。现实际hideStack先关窗，再清controller owner，清contentViewController及实际NSHostingView、窗口/表引用和observer，最后释放会话队列；再次show走既有创建分支，得到空会话并重新订阅。状态去掉偏好队列读写，避免关闭时引入原版没有的保存/错误弹窗。旧偏好stackItemIDs编解码字段保留以读旧文件，未删除旧文件或历史记录；方向偏好仍保存，所有采集/插入/反转/消费/恢复方法不变。

Pasto将view及queue放在SwiftUI facade，故用显式清理适配原内容控制器所有权；本轮不宣称两个架构的全部ARC、缓存、外部持有、重入、modal/sheet和直接系统关闭路径等价。原全模型/DI以及04430c/0f733c继续待证，不扩大P2布局。

1生产文件3精确增量、246不变；14原片段、18 ARM字、真实父类与两个dynamic槽、真实content清理selector、12旧方法及6共享源已绑定。新增12源码检查，完整2290项通过。首轮6处旧全文件/构造摘要失败日志保留；5旧工具8模式精确逆隔离新session增量，原历史业务断言和原证据不改，当前新增检查直接读实际代码。

v56保旧213记录191组及9额外合同，新增0a86c0有限合同修至214记录192组：P0 77/77（100%），P1 137/137（100%），总214/214（100%）。仅已确认有限差异清单，完整模块与两个未知未闭，整体迁移率仍未知，目标继续。

版本1.0.2、HEAD、function-map及官网/README下载9文件保持。未编译、构建、安装、运行应用/框架、联网、提交、推送或发布。
