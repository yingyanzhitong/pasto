# 第四十二轮：P1 定向索引更新标志

原定向重建2f2ca8传force=1，ea770存续体0x118，eaa10交给e1bac，最终e3ce8把低位写入CSSearchableItem.isUpdate。本轮实际reindexTargets每批live fetch后用true构造SDK对象，builder在expiration后/return前赋值。普通快照与既有history值适配显式false，未根据名称猜改独立原history worker；该父链继续保留。

绑定11原函数片段、实际ARM的AND w2,w19,#1与BL、setIsUpdate: selector真实format6可达指针，以及本机SDK中macOS10.11即提供的属性。没有增加动态桥或OS可用性门；原5000字符限制、其他属性/namespace、batch和错误/ack队列保持。

| 固定有限差异清单 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 30 | 81 | 37.04% |
| 合计 | 99 | 150 | 66.00% |

关闭2e1bac/2e3ce8/2ea770/2f2ca8/2f26a8五条旧flag合同，均属共享调用链，并非五个独立bug或完整函数迁移。余51差异及2未知；eager内容、optional设备/单分组和索引持久状态/availability/owner/ack、原history worker等父合同仍开放。

670项源码/静态检查通过（新增10项），含目标flag被误改false的反例、普通原路径0、batch顺序、原ARM/SDK证据及属性/队列未变检查。仅1生产文件改变、230未变；1旧测试只更新builder签名，身份语义断言不变。未运行CoreSpotlight/CoreData/Swift/ObjC/应用，不编译、构建、安装、联网、提交、推送或发布；官网9文件、1.0.2、HEAD和function-map不变。

证据：[JSON](p0-p1-repair-round42.json)、[补丁](p0-p1-repair-round42.patch)。继续P1搜索与筛选。
