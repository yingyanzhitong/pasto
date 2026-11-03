# 第一百零三轮：图片原生读取、尺寸与显式刷新

原3bd9cc从捕获Item.data读取31b218解出的有序表示，逐项尝试NSImage，命中时再次调用同表示的37d5c4后构造返回值。原3bd740/3bd784的尺寸来自当前rawPreview image metadata，缺失或非图像metadata返回zero，并非实际NSImage尺寸。Pasto此前先从完整DTO payload解图，尺寸来自保存的DTO字段，真实native工厂也先resolvedItem。

新增公开image/size getter与不触发KVC的hasNativeEntity门。native type1进入允许item:nil的image内容，共用原preview chrome，初始与取消直接读同handle，preferred size直接读当前metadata；原缩放算法保持。值输入保留旧Store订阅和force reload；native child不再由Store缓存缺项/类型变化自动关闭或重载。父ItemPreviewViewModel/header仍观察实体并在删除时关窗，不能把局部child契约写成整个预览无observer。

原3e5cf0取消路径调用3bd9cc重读，原3e5dd4提交当前ZoomableImageView图像后关闭编辑/重置配置并更新UI，不调用3bd9cc。当前native取消显式重读，提交保留当前旋转画布，不重新解码刚写入的PNG/JPEG。图片task取消、完整editingConfiguration/Undo/debounce与OCR调度仍未按此宣称完成。

21原片段、20实际ARM调用、3个完整直接调用清单绑定，含原child构造与提交/取消的不同读取路径。1558项Python源码/Mach-O静态检查通过，18项新增。3生产文件修改，244个本轮前摘要保持，9精确增量；14既有方法及7共享源不变。2历史测试/工具只逆隔离该增量，新测试直接使用当前源码。新增首轮3处重复token/分支定位错误日志保留，纠正测试后全绿，未据失败回滚生产代码。

v27保留v26全部177条/161组，新增并修三个独立有限合同：P0 70/70、额外P1 110/110，合计180/180（100%）。原native工厂和writer不重复计数，也不升级完整函数。这不是Pasto总体完成率；Link正文/完整factory、files/card、图片异步/Undo、坏图/完整codec、删除fault、模型/DI/ABI/UUID桥、组/Stack/选区及04430c/0f733c仍开放，目标继续。

未编译、构建、安装、运行应用/框架/CoreData、联网、提交、推送、标签、发布或部署。官网9本地文件、版本1.0.2、HEAD和function-map保持。静态源码检查不作为实际功能或性能实测。
