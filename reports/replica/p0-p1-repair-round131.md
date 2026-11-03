# 第一百三十一轮：搜索raw getter异常续行与两个未知的元数据

上一轮属于实质进展：修复两处P1原生索引/空内容差异，2048源码检查通过。本轮继续按P0修复→P1检查→P1修复的阶段推进。

确认原3724f0经31b218读取data，raw getter抛Objective-C异常时31b218记录本地level3日志并返回非nil空表示，搜索再进入已有typed-preview fallback。Pasto旧search reader在外层exception catch直接nil，跳过恢复。本轮将既有主copy readItems的decoder body原文移至共享readRepresentations；仅把取诊断对象的调用换为同步lazy resolver参数。主copy仍用原MainActor per-data关联logger，背景搜索在自己的private context.performAndWait队列调用同helper。ObjC异常some([])继续project/nativeText；普通nil/无效raw仍nil，外层fetch、关系及投影错误处理保留。

背景读取每次新建private context和data对象，命名wrapper仅异常时创建，无跨队列managed object或全局缓存；它并非原实体存储字段布局，精确日志对象构造/销毁时机和error插值文本保持明确适配。此处仅闭合实际raw getter异常→typed fallback副作用，未冒称原3724f0全部诊断/错误树已迁移。

另对两个未知新增静态证据：实际Mach-O category chained pointer指向NSTextView/PastePlatform，relative method与selector引用解析为setText:，类型编码v24@0:8@16，ObjC IMP为0f72a4。该声明返回void，但没有把它直接连到Swift helper0f733c，因此未擅改当前Int0接口，也不把Ghidra return0当依据。原搜索框普通构造是程序化TextKit2；独立0444b0→04430c coder链设置默认字段并super.init(coder:)。未找到可靠原archive资源图，不能推断无人引用；可见Pasto构建也不当原资源证据。两个unknown保持。

2源文件3精确增量，245文件不变；13原片段、3实际调用、10ARM字、11不变方法、6共享源与真实ObjC category/导入/relative指针绑定。共享decoder主体仅诊断resolver替换的原文等价已检。14新增检查，完整2062源码/Python/Mach-O静态检查通过。首79历史hash/形状失败、2error，3旧测试工具8处精确逆隔离后通过，原proof与初失败日志保留；新检查读取实际当前实现，未编译或执行系统框架。

v42完整保留201函数记录179组，为既有3724f0附已修额外异常分支，不因同函数再扩分母。P0 77/77、P1 124/124、总201/201（100%）仅已确认有限差异，整体Pasto迁移率未知。目标继续处理具体P1源合同，完整父合同与两个unknown尚未完成。

仅本地修改；未编译、构建、安装、运行应用/框架、联网、提交、推送、打标签或发布。官网9文件、版本1.0.2、HEAD与function-map保持。
