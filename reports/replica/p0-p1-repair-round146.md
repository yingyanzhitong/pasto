# 第一百四十六轮：Stack 表视图窗口拖动许可

按已授权的P0修复→P1检查→P1修复继续。本轮检查实际Stack表格，确认一处原函数差异并修复。

原0a0b2c的PasteStackTableView.mouseDownCanMoveWindow经actor守卫后恒返回true，已绑定原ARM四个指令字；原Stack Nib也明确声明这个专用类。Pasto的实际OriginalStackTableController创建普通NSTableView。为避免把父类默认值当猜测，用纯Python只读解析本机26.2/25C56 AppKit共享缓存：NSTableView九张完整方法表没有该override，父NSControl十五张完整方法表中的同名BOOL getter（B16@0:8，IMP1849df83c）是mov w0,#0; ret，即默认false。缓存UUID、映射、24张方法表摘要及getter八字节均绑定；不执行框架，也不泛化到所有系统版本或动态注入。

新增无存储状态的私有OriginalStackTableView子类，明确覆盖mouseDownCanMoveWindow为true，并接入实际tableView创建处。保留公开NSTableView类型、原frame、所有配置和行选择false。原windowDidLoad与当前生产链已经开启isMovableByWindowBackground，因此不重复改窗口逻辑。无自定义构造器，继续继承frame/coder初始化。

仅1生产文件2精确增量，246文件字节不变；6原片段、原Nib、4 ARM字、24张系统静态方法表、12旧方法及4共享消费者已绑定。新增16项源码检查，完整2278项通过。首次一项旧构造方法摘要因已授权类型替换变化而失败，日志保留；3旧工具5模式6替换仅逆隔离本轮两个增量，旧断言内容不变。本轮测试读取实际生产子类与producer，不使用逆隔离规避本轮修复验证。

v55保留旧212记录190组和9额外合同，新增0a0b2c一条修复，至213记录191组。已确认有限差异清单：P0 77/77（100%），P1 136/136（100%），总213/213（100%）。这不是完整P0/P1功能迁移率；窗口子视图命中、实际拖动/焦点、完整归档加载、DI/模型/释放父合同及04430c/0f733c两个未知仍开，整体完成率未确认，目标继续。

版本1.0.2、HEAD、function-map及官网/README下载9文件保持。未编译、安装、运行应用或系统框架、联网、提交、推送、发布或部署，原Paste与系统缓存均只读。
