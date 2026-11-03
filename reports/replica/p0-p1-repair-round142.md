# 第一百四十二轮：分组菜单三态与单次批量分配

继续P0修复→P1检查→P1源码修复。141已接分组定位当前归属，本轮核对实际菜单选择状态及动作，未把已证缓存producer重新计迁移数。

原09e8a8对构造时捕获的完整项目数组逐项读取31bc94的当前type2 owner，以NSObject equality匹配目标。匹配数等于输入数时state=1（含空输入0==0），部分非零匹配state=-1，其余0。实际ARM的cset/sbfx/csinc及x7状态参数到21bafc已绑定，后者调用NSMenuItem.setState。09f240→09ee9c点击仍转发捕获完整数组与目标，并不因已经勾选而取消归属。原目标行还调用3ecffc→3ed158绘制12pt分组颜色图标。

Pasto原主分组菜单只有普通Button，没有三态也没有分组图标。现统计原生owner匹配数，旧值沿现有store.pinboardOwner桥；使用本地SDK中macOS13起支持的multi-source Toggle，项目最低macOS14。全部/无匹配用一个assignment binding，部分匹配用false的assignment binding加constant(true)表达mixed；仅assignment有setter，避免每个选中项目各触发一次完整批量分配。setter忽略控件请求的布尔值，始终按原动作向捕获target分配完整items，点击原on状态也不改成unassign。Label复用已有OriginalPinboardHeaderIcon的12pt本地色点绘制器，shared=false，未另造绘图样式。

仍是明确的SwiftUI宿主适配：本轮证明源码状态/动作与既有原绘图器接入，未运行SwiftUI/NSMenu、未宣称像素或完整生命周期验收。只处理本地不共享组；CKShare标志排除。原创建/取消固定/菜单尾、集合缓存与setter持久化实现保持，generic集合错误、原DI/fault/所有菜单构造父合同继续待证。

1生产文件2精确增量，其余246文件不变。绑定9原片段、10 ARM字、5实际调用、本机SwiftUI接口；6旧方法、5共享源（含原绘图器）不变。新增16项源码检查，完整2214项源码/Python/Mach-O检查全部通过。首次2历史快照失败及1旧Button调用位置查找错误已保存日志；快照只逆隔离本轮2增量，旧拓扑测试改查Toggle及唯一批量setter，保创建/取消固定原顺序。3既有测试工具7模式9替换，未弱化旧业务尾或执行编译/框架。

v51保209记录187组，仅在既有09e8a8追加第9个额外已修合同，不扩函数分母。P0 77/77（100%）、P1 132/132（100%）、总209/209（100%）只是已确认有限差异修复率；完整P1父合同及04430c/0f733c未闭合，整体迁移率未知，目标继续。

版本1.0.2、HEAD、function-map及官网/README下载9份改动保持。仅本地源码修改与检查；未编译、安装、运行应用/系统框架、联网、提交、推送、发布或部署。
