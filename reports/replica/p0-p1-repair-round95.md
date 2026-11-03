# 第九十五轮：普通预览与弹出窗脱离保留原生实体

本轮继续P1编辑/预览调用链。原Space从069778当前selection取末项，06bb3c经applier可选lookup得到实体，与对应可见cell交02964c；选区reveal的075e3c同样先可选取实体，再检查可见cell。02964c把实体强持在Popover.item并交3c25dc构造预览；029a80脱离窗口时从同字段读取该实体再次构造预览，无UUID或历史缓存重查。原item ivar偏移+0x48、实际存取指令和12个真实调用已绑定。

Pasto现在让Popover持有ClipboardRestoreItem，内容factory收同句柄。Space、卡片上下文菜单、Stack上下文菜单及reveal回调交同一输入，普通窗口与popover都将它传入预览factory；脱离/编辑窗口复用Popover所存输入。reveal使用可选restoreItem，缺项沿原beep门返回，并在anchor之前取实体。当前reveal此前将ClipboardCollectionEntry传给ClipboardItem形参的源码类型不一致，也改为统一句柄参数；全部实际调用处均已清点，不声称编译验收。旧值/旧UUID Stack入口保兼容句柄，registry身份继续用UUID适配。

1428项源码/静态检查通过，新增13项；旧1415项也已单独通过。绑定11原片段、12调用、7指令和ivar字段；Popover关闭通知/几何/编辑切换及原编辑窗口7个方法、5份共享源码不变。4个生产文件修改，其余243个保持。3个历史测试/工具仅对15个精确源码增量做可逆隔离；首45失败、随后1个旧Space断言失败日志保留，修改历史范围隔离后全绿。未跳过测试或覆盖旧证据。

| 已确认有限差异 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 70 | 70 | 100% |
| 额外P1 | 96 | 97 | 98.97% |
| 合计 | 166 | 167 | 99.40% |

本轮补已有实体/预览父合同，不增加完整函数计数。原06bb3c在缺可见cell时还有异步index重试，执行时重新从applier取实体；当前呈现/anchor路由尚不等于此全合同。它与Popover已捕获实体后脱离窗口不同，不能混作UUID重查理由。完整registry/router/DI/ABI、非文本观察写回、投影错误、组关系通知和缓存外观、泛型UUID元数据同步、optional不可用卡片、3544dc与Stack/选区寿命及04430c/0f733c仍开放。

主智能体修改，复用1个既有低模型智能体只读核真实输入链及当前调用。未编译、执行框架/数据库/应用、联网、安装、提交或发布；官网9文件、版本1.0.2、HEAD与function-map保持。

[机器记录](p0-p1-repair-round95.json) · [源码补丁](p0-p1-repair-round95.patch) · [有限差异清单](p0-p1-difference-backlog-v20.json)
