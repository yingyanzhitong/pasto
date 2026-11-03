# 第一百零四轮：区分图片工具栏与通用旋转入口

本轮是有证据的只读复核，未修改应用代码。真实ARM函数参数绑定揭示两条路径：右工具栏3e75e4通过ADRP+ADD将3e51b4传给07abf4弱引用分发，左3e7604传3e53a0。两个handler更新现有rotation配置、按±90旋转当前画布、刷新提交状态并注册反向Undo；函数完整调用清单不含通用任务创建。当前quarterTurns步进、画布更新与反动作在有效默认配置子域可复用，原UndoManager归属、配置可选键与VM任务不据此宣称相同。

另一路3df818通用adapter进入3e4a54：成功生成旋转图后取消旧pendingCommitTask并替换任务、注册反角Undo。实际async相对描述符c46218指向3e77a0，再到3e5ef4；c46238指向3e6bb4。三条MOV指令组装400000000000000000 attoseconds，即400ms。sleep成功/错误完成均检查Task.isCancelled；非取消后weak-load owner，清任务槽，再读取当前canvas提交，而不是捕获旧图。原commit/cancel函数本体不触及该pending槽；析构只release，不能说自动cancel。

因此不应因当前toolbar没有400ms任务就给已有按钮增加延迟。本轮保留该实现，明确后续要追踪通用adapter的实际Pasto消费与原配置/Undo/VM取消状态，再按对应入口实现，不能用按钮作为未经证实的替代消费者。

22个原函数片段、15处实际ARM调用、2个toolbar函数参数、2个真实async relative descriptor、5个完整调用清单与6个当前方法摘要绑定。1570项Python源码/Mach-O静态检查通过，12项新增。247个生产文件及210个历史测试/工具保持本轮前摘要；没有历史测试调整、生产增删或函数台账升级。

有限修复清单v27保持180/180（100%），其中P0 70/70、额外P1 110/110；本轮只读核对不增加修复数或分母，也不冒充整体迁移完成率。通用旋转、原UndoManager/完整configuration/任务、Link/files/card、错误/codec/删除fault、原生模型/DI/UUID桥、组/Stack/选区与04430c/0f733c继续开放。

未编译、构建、安装、运行应用/框架/CoreData、联网、提交、推送、标签、发布或部署。官网9个本地文件、版本1.0.2、HEAD、function-map和v27清单保持。测试仅为源码/静态核验，不是任务计时、实际Undo或功能运行验收。
