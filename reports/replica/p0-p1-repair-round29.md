# P0/P1 源码修复：第二十九轮

当前仍先修P0，再集中检查P1，最后修P1。原0a56f4先检查modal，modal只activate并返回；非modal且controller为空才创建MainWindowController、设置回调、订阅可见状态，然后show。上轮Pasto仍在启动时创建面板并订阅，初始false提前重注册Stack。

现在native面板和NSWindowController延至loadPanel首次调用，先缓存对象，再配置现有native视图、委托/快捷键/resize及外观，最后真实panelDidLoad hook安装可见订阅。以后返回同一缓存，不重复订阅。启动、外观更新、AppMain key/visible/目标检查、隐藏未加载窗口及选区/焦点探测均不读取创建式getter；modal gate先于首次加载。显式公开panel访问保持兼容加载行为。

MainWindowController metadata f8f818的superclass slot f8f820已通过LC_DYLD_CHAINED_FIXUPS绑定AppKit NSWindowController，descriptor ca0490也单独绑定。显示/关闭改用对应父SDK调用，现有代次门、公开可见状态和关闭通知继续复用。该证据不依赖Ghidra显示类名。

| 当前有限差异 | 已修复 | 分母 | 比例 |
| --- | ---: | ---: | ---: |
| P0 | 54 | 69 | 78.26% |
| P1历史依赖 | 8 | 81 | 9.88% |
| 合计 | 62 | 150 | 41.33% |

本轮消除既有0a56f4首次native控制器/订阅有限差异1条，不增加分母，不因父SDK接入再给0192b0/019a84计分。剩P0 15、P1 73，共88条有限差异及2未知。完整函数迁移仍false，此比例不是全原版函数或应用完成率。

480项Python源码/静态检查通过，新增12项。5个旧测试按真实SDK父调用和非创建式visible/responder guard精确更新；删除/preview原合同先与phase29-before逐方法校验，再只允许指定guard差异，保留更早冻结报告。初次3项失败为旧“方法逐字不变”断言，生产未为旧断言回退，日志保留。绑定7个C片段、2208字节数据（523条机器指令）及真实dyld superclass；2旧生产文件变化、225个不变，无新增生产文件。

保留：ReplicaUIState、搜索/偏好服务仍eager；callback和transition标量仍由UI facade持有，NSWindowController加loadedPanel缓存只是有限所有权适配，并非原子类/字段ABI。完整MainView/DI context、post-show router、factory/hooks重入、coder、controller/window nil生命周期、可见时偏好变更和原动画/布局仍待证。继续P0面板show/close原参数与捕获合同，不把有限lazy修复称整个模块完成。

未编译、构建、安装、运行应用/框架、联网、提交、推送或发布；官网9文件、1.0.2、HEAD与全函数台账不变。见[JSON](p0-p1-repair-round29.json)、[补丁](p0-p1-repair-round29.patch)及[v7差异清单](p0-p1-difference-backlog-v7.json)。目标仍进行中。
