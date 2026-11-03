# 第一百五十九轮：原始 NSData 的 nil 桥接

沿编辑失败后原生对象重读核对共享raw getter，发现P0分支差异：原31bc34→31b1bc读rawPasteboardItems后调用Foundation Data._unconditionallyBridgeFromObjectiveC(NSData?)，当前Pasto则guard as?Data，nil时人为抛CocoaError而提前返回nil，搜索无法继续空表示诊断和metadata回退。

从原31b1e8真实BL及bf4a34的dyld链，绑定精确Foundation桥接符号。只读解析本机Foundation MachO、完整导出trie的10步路径，定位桥接实现；其nil参数分支真实返回空Data的零payload及C000表示，再返回调用方，不是抛错。本机cache UUID/映射/导出trie摘要、实现88字节、OS版本和SDK可空NSData签名均绑定；没有加载或执行Foundation/原应用。

当前shared raw reader在既有ObjC异常边界内读NSData?并调用同SDK桥接，不再人为拦截nil。空Data进入原codec得到空表示，复制和延迟搜索继续现有empty、诊断及typed-preview回退；真实ObjC异常仍原命名level3日志→空数组。主复制wrapper、替换/旧迁移及codec/搜索消费者不改。非法类型/完整required关系图与其它OS/ABI仍父合同，不以nil桥接推广所有损坏输入相同。

1生产文件1处改动，246不变；3完整邻方法和5共享源不变。绑定5原函数片段、真实Paste import与Foundation export、nil分支和SDK。8新增定向检查通过，完整2390项静态检查通过。首次4失败含旧nil提前失败假设及历史摘要约束；已保日志。旧raw语义测试直接更新为同SDK桥接且无CocoaError，保ObjC异常/empty/投影顺序；历史literal-move与其它旧摘要仅隔离精确新增量。共4旧工具/测试9模式10替换，247生产逆增量恢复和旧调整精确重放通过，新增检查读当前实现。

v66新增31b1bc一个P0有限差异记录；保留旧223记录198组及11额外合同，现224记录199组。有限清单P0 80/80、P1 144/144、总224/224（100%）；整体迁移完成率未知。完整事务失败/原生模型/DI/ARC/observer和04430c/0f733c未知仍开，未执行真实损坏库或运行验收。

版本1.0.2、HEAD、函数映射及官网/下载九文件保持。只留本地改动，不编译、构建、安装、运行应用/框架/CoreData、不联网、不提交推送发布。
