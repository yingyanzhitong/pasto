# P0/P1 源码修复：第二十八轮

仍按先修P0、再检查P1、最后修P1。原019790在generation匹配的显示完成中先恢复旧系统背景，再发布isVisible=true、聚焦搜索并调用onDidShow；019e2c在关闭完成、清screen和closing后发布false。Pasto此前只有native窗口状态和回调，缺少该Published链。

现在UIController发布isPanelVisible（初值false）；两动画完成门内按原位置写true/false，AppMain保留AnyCancellable并直接消费sink传入Bool。原0a8378会在visible时撤销、hidden时注册Stack快捷键：AppCoordinator descriptor ca20f4→field descriptor d40a34、metadata fab198、32项8字节offset vector共同将0x128绑定_pasteStackShortcut，0xf0绑定_activationShortcut。代码只交stackHotKey；普通toggle仍按原0a5300的native isVisible/closing判定，不误改为Published。

| 当前有限差异 | 已修复 | 分母 | 比例 |
| --- | ---: | ---: | ---: |
| P0 | 53 | 69 | 76.81% |
| P1历史依赖 | 8 | 81 | 9.88% |
| 合计 | 61 | 150 | 40.67% |

旧019790有限Published差异消除；新纳0a8378有限真实消费者一条，v7分母150，旧149记录保留。剩P0 16、P1 73，共89条有限差异及2未知；比例不等全原版函数或全部应用完成率，完整函数迁移仍false。

468项Python源码/静态检查通过，新增10项，98个旧测试文件未改。绑定9个原C片段、2460字节数据（428条机器指令）和2个实际Combine dyld导入；字段记录及8字节向量逐项绑定，不用4字节解读猜字段。2旧生产文件变化、225个不变，无新增生产文件。

原0a56f4在首次显示前才懒建MainWindowController并订阅Published；当前UIController仍提前构造，订阅在启动配置后建立，初始false会额外重注册Stack。这一时点及完整DI/原控制器图尚未迁移，保留0a56f4。录制、--no-global-hotkey、无效快捷键和状态提示为既有Pasto策略；面板打开时改偏好的完整生产链仍待比，不宣称原所有注册路径完成。已计019790仅普通本地完成发布/焦点/回调有限域，不推广为完整类迁移。

继续P0面板生命周期与焦点，其他P0父合同保留，P1独立检查和修复仍排队。未编译、构建、安装、运行应用/框架、联网、提交、推送或发布；官网9文件、1.0.2、HEAD与全函数台账不变。见[JSON](p0-p1-repair-round28.json)、[补丁](p0-p1-repair-round28.patch)及[v7差异清单](p0-p1-difference-backlog-v7.json)。目标仍进行中。
