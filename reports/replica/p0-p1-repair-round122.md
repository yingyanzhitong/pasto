# 第一百二十二轮：采集原生查重与选区订阅用途

继续先修P0。本轮把recordCapture从“按state.items中的nativeChecksum匹配，再按UUID取得实体”改为“按checksum查询原生仓储，保留命中的同一实体”。查询继承Item默认排序与batch，limit=1、offset=0；checksum为nil不查询，原生fetch失败或空结果返回nil。原错误处理按真实32af1c分支核实，不能把Ghidra移除的错误块当作不存在。

命中后通过返回实体的本地key定位值缓存，后续替换data、生成preview、写来源及历史timestamp继续使用同一capturedTarget，不再按UUID重查。缓存缺项时投影该同一对象后加入state；非capture导入比较及已有内容更新分支原文保持。未增加异步等待、计时器或额外save。

保留的明确缺口：命中实体但state无该项时，ClipboardPersistence.item仍必须解码旧content，并检查时间/data/source等列；坏key或兼容blob会在更新前抛错。这是接下来的具体P0任务，尚未以新默认值覆盖、丢弃旧多组成员或冒称完整模型等价。

选区订阅的真实sink也已绑定：0b1110/14实际构造0b26ac回调地址，sink经0b26ac→0b1c94→af2cd0更新NSUserActivity.userInfo及needsSave；af2958初始化NSUserActivity并设置eligibleForHandoff=true。它是跨设备Handoff activity更新子链，属于既有排除范围。相邻0b11ac是另一路关闭回调，仍负责无预览窗口时恢复外部应用，不能一起排除。本轮该本地回焦点代码保持原文；不据此声称全部选区消费者已闭合。

18原片段、10真实调用/尾跳、9错误分支ARM字、2回调地址构造及3真实selector绑定。2生产文件4个精确增量全部可逆回本轮基线，另245文件不变；10方法及7共享源保持。既有低模型只读复核命中身份、可选值/throws调用及兼容投影残余，未编译或运行框架。

20新增检查，合计1916项源码/Python/Mach-O静态检查通过。首次4失败是历史cache谓词和整文件/方法摘要；3历史测试及1逆向链工具精确隔离本轮增量后，第二次有1个历史工具误将二进制资源按UTF8读取。限定只对Swift源逆向归一化后全部通过。11处测试适配及全部失败日志保存，原proof不改，新检查读取真实当前代码。

3214c8及3611b0已在台账内，本轮补消费者合同不重复计数。v38保持P0 73/73、P1 124/124、总197/197（100%），仅为已确认有限差异，不代表整体P0或Pasto迁移完成。当前唯一in_progress为P0采集；P0源码合同闭合后再检查P1、修P1。

改动仅本地；未编译、构建、安装、运行应用/框架、联网、提交、推送、打标签或发布。官网9文件、版本1.0.2、HEAD与function-map保持。
