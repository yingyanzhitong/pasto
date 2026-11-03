# P0/P1 源码修复：第三十轮

当前仍先修P0，再集中检查P1，最后修P1。本轮对齐原0192b0/019a84的显示frame、动画包装和完成持有方式。原show读取当前content.frame高度，以NSScreen frame定位并setFrame:display:false；父show之后先把window.frame交给content，再把原点改为0、负content高度。旧Pasto经positionPanel使用持久偏好高度且display=true，直接写负原点frame。

现在show按原输入与两次frame写入。显示/关闭均调用已有21cadc包装，显示0.15、四控制点0.2/0.8/0.2/1；关闭0.2、原21cf38 easeInEaseOut支持方法。完成回调按原capture store/objc_retain证据，显示强持controller/window、关闭强持controller/content；保持transitionGeneration门。显示完成去掉原代码不存在的额外clips写，关闭仍按parent close、清screen/closing、发布false、恢复clips顺序。

| 当前有限差异 | 已修复 | 分母 | 比例 |
| --- | ---: | ---: | ---: |
| P0 | 56 | 69 | 81.16% |
| P1历史依赖 | 8 | 81 | 9.88% |
| 合计 | 64 | 150 | 42.67% |

本轮修复既有0192b0/019a84有限差异2条，分母仍150；新支持21cf38不重复增加函数/迁移数。剩P0 13、P1 73，共86条有限差异及2未知；完整函数迁移仍false，此比例不是全原版函数或应用完成率。

492项Python源码/静态检查通过，新增12项。6个旧测试改为真实动画包装/强捕获completion，保留旧generation门和handoff先于动画等要求；初次1个旧集成断言仍定位NSAnimationContext字面而报错，精确更新后通过，生产未为旧断言回退，初始日志保留。绑定12个原C片段、190字节数据（41条机器指令），setFrame:display:真实selref/string与false实参及两objc_retain调用分别核对；2旧生产文件变化、225个不变，无新增生产文件。

源码反例：当前content高度360而持久偏好332时，原show使用360并display=false，旧Pasto使用332且display=true，当前按原处理。回调原强持窗口/内容，旧weak在外部owner释放时可丢失完成副作用，现按实际capture角色保留。该记录是源码合同案例，不是运行或动画复现。

明确保留原子类/字段ABI、DI graph、screen/reentry、返回表示、coder/context生命周期和真实native布局/渲染未闭合域；面板内删除确认取消和dismiss monitor是既有产品交互适配。原21cadc/21cd10/21ce98算法继续复用，未因局部接线将其他父合同升级。

下一批P0数据与删除安全唯一in_progress，处理实体Sequence、恢复事务与归档身份；面板转pending保留父合同，不标模块完整。未编译、构建、安装、运行应用/框架、联网、提交、推送或发布；官网9文件、1.0.2、HEAD与全函数台账不变。见[JSON](p0-p1-repair-round30.json)、[补丁](p0-p1-repair-round30.patch)及[v7差异清单](p0-p1-difference-backlog-v7.json)。目标仍进行中。
