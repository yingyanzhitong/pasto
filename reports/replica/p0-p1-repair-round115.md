# 第一百一十五轮：原生复制内容与恢复目标

按最新指定顺序，回到P0复制链路修复。原38222c逐个使用供给的Item读取rawType与内容，再读取sourceApplication/bundleIdentifier，保输入顺序和重复；image经383d90进入383df4，plain经31bcdc读取data并投影。本轮让真实native复制入口直接执行该链，避免先resolvedItem解整份值归档或按UUID重查目标。混合/旧值/ID及识图入口仍保兼容路径。

原图片路径先准备目录，再加载ItemData，随后在formatter需要时才读取当前sourceName和可选timestamp；nil时间仍使用当前Date。保留原有文件格式、错误、聚合实现和Pasto品牌适配。Native processor聚合后半段经严格重构比较与旧纯函数完全相同。

写入尾抽成共用方法：marker、准备恢复事务、实际剪贴板写入、记录changeCount、保存恢复时间；保存失败吞掉后继续清Undo和发送DidRestore。除准备调用改为闭包外，尾部与前轮原文严格一致。Native历史准备持有输入同对象，不再按UUID重查或以值缓存membership拒绝；所有目标的原生timestamp已写后才投影缓存，缺失位置只跳过值投影，context保存仍执行。旧值与ID-only可用性检查保持。metadata基线验证/revision合并等仍是本地兼容适配，未称完整原厂事务迁移。

Controller复制选区及Stack行复制现在直接传句柄，performCopy成功后收起流程不改；Stack预览仍值适配。11原片段、25实际branch、6selector和3callback指令绑定；37a144以ADRP+ADD把37b620交给2ff310，非直接BL37b620。38222c经中间helper读取data，不伪造直接调用。5共享源与12方法保持，6生产文件14精确增量，241文件不变。

26新增检查，最终1781项Python源码/Mach-O静态检查通过。首次8失败5error为历史结构/签名/hash检查；12历史测试及1链工具共29处精确隔离本轮增量，逆推全部回baseline，无旧证据摘要替换。首失败日志与摘要保留。新26检查读取当前生产代码。既有低模型只读复核native guard/缺缓存投影/legacy门与context保存，无明确新增源码缺口；未编译或执行框架。

v37原样保留194条/176组，新增38222c及383df4两有限P0合同同processor链保守计1组；已有37a144/37ade4恢复目标与cache门额外修复不重计。P0 72/72、P1 124/124、总196/196（100%）；分母仅已确认有限差异，整体完成百分比仍未知。

继续P0完整复制/数据/fault/context/save/选区/焦点父合同，之后检查P1再修P1。模型DI、兼容blob、跨进程/跨context、全部codec/错误/重入、Stack预览及04430c/0f733c仍未闭合。P2及联网排除。未编译、构建、安装、运行、联网、提交、推送、标签或发布；官网9文件、1.0.2、HEAD及function-map保持。
