# 第一百四十五轮：原始 Stack 归档输入与单元格 coder

继续P0修复→P1检查→P1修复。144已修默认快照同步交付，本轮从原始资源/构造消费者继续，不以无直接caller或无当前工程Nib推断原方法不可达。

本机/Applications/Paste.app仍为6.6.6，ARM64切片SHA256与本次反编译底稿871f0035…完全一致。资源包含两个顶层Stack Nib，格式为NIBArchive v1而非plist；用普通Python按对象、键、值、类表静态解码，不调用NSKeyedUnarchiver或AppKit。198对象的table归档在NSTableViewArchivedReusableViewsKey中沿13→60→62→63包含9034字节的嵌套模板，内有84对象；NSClassSwapper声明_TtC5Paste21PasteStackSnippetCell、原类NSTableCellView，并将imageView/textField分别连到NSImageView/NSTextField。真实ObjC类元数据、initWithCoder: selector及objc_msgSendSuper2/父类导入也已绑定。085324→086658的原row provider实际makeView并cast该Cell后0519f8更新，不只是孤立类名出现。

原051bd8调用super.init(coder:)并返回父类结果；Pasto同入口fatalError。现先初始化Pasto额外需要的native category图标provider，再super.init(coder: coder)，保父类nil/错误传播，不自行创建outlet、不加约束、不更换子视图。provider闭包延迟读取原生rawType并复用既有category图标；无native输入走unknown兜底，仅为新coder本地适配，原有程序化/custom-provider构造和旧值入口不改。

本轮只迁移该coder函数及其原真实输入证据，未把原NIB、运行时class-swap映射、布局或资源加载器搬入Pasto，未声称当前生产Nib路径可用。Search TextView的04430c与此Stack类不同；两个Stack资源里没见它，不能由此证明其不可达，也不升级04430c/0f733c两个未知。

1生产文件1精确增量，246文件不变；8原片段、9 ARM字、selector/2真实导入、原cell类元数据及完整归档表边界已绑。4原构造/更新方法和5共享消费者不变。新增16项源码检查，完整2262项源码/Python/Mach-O检查全部通过。首次1历史全文件改动集合快照失败保留日志；3旧测试工具5模式6替换仅逆隔离本轮coder增量，原业务断言保持。未编译或执行归档/框架。

v54保旧211记录189组/9额外合同，新增051bd8有限差异1条源修至212记录190组。P0 77/77（100%）、P1 135/135（100%）、总212/212（100%）仅已确认有限差异修复清单；完整Stack/Nib加载、模型/DI/生命周期与两个未知仍未闭合，整体迁移率未知，目标继续。

版本1.0.2、HEAD、function-map及官网/README下载9份改动保持。原Paste安装包和资源只读，Pasto源码仅本地修改；未编译、安装、运行、联网、提交、推送、发布或部署。
