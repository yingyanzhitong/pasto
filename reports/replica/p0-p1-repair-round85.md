# 第八十五轮：选区的可选实体读取

上一轮为实质进展：分组菜单捕获输入已修复并通过1271项检查。本轮追查原选区生成方式，发现跨P0/P1差异后先按P0修复，再继续P1消费者。

从原ItemCollectionView class metadata 0x100f91308的真实dyld链指针读取+0x108，目标为22a930。它直接返回cellSelectionManager保存的数组，未排序。06e1f8逐项读取该数组，以已应用索引调用1b9698，再经AnyObservableCollection的+0x28可选ID槽、type-erased闭包及FetchedResultsCollection可选查询3544dc解析实体；只有非nil才追加。绑定13个原函数片段、3个真实链指针、6条B/BL和6条getter/可选查询/nil循环指令，未执行原应用。

此前Pasto已应用选区调用required渲染或required恢复入口。ID仍在已应用列表、但context对象读取失败/类型不符时，原版跳过该项，Pasto可能触发fatalError。本轮新增Reference.restoreItem及Entry.item/restoreItem的可选入口；两个applied选区getter及ownerless选中ID适配用compactMap保持输入顺序并跳过nil。可选恢复入口只检查同context对象及类型，持实体供恢复时使用；普通required/indexed方法和可见renderer方法体逐字保留。

复制/批量粘贴、菜单和Stack多选仍走原有实际路由及writer，没有替换为新测试入口。单项paste(itemID:)的既有ID-only兼容回退未改，继续作为开放边界；不能把本次批量选区合同当作它的完整等价证据。原getter返回数组的证据也不等于所有原选区mutation/observer与当前orderedSelectionIDs已完全配对。ClipboardItem载荷投影、原生实体/DI/ABI及Stack永久删除后失效仍开放。

1285项Python源码/静态检查通过，新增14项。首次仅1处旧来源应用测试仍要求required renderer路径失败，已改为验证实际Entry.item→Reference.item→同一来源投影；另2个历史工具/测试仅隔离5个精确增量，原历史证据不改。4个生产文件修改、241个保持，无新增生产文件，无schema/Package修改。

| 已确认有限差异 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 70 | 70 | 100% |
| 额外P1（不重复计P0） | 96 | 97 | 98.97% |
| 合计 | 166 | 167 | 99.40% |

v20保留v19全部166条/150组，新增并修06e1f8的可选选区有限合同；因同时影响P0/P1，仅按P0增加一次分母与修复数。3544dc及两个未知04430c/0f733c仍开放，不是完整P0/P1或全产品迁移率。

主智能体复核，复用1个低模型只读审查，无子智能体写入。官网9文件、1.0.2、HEAD与function-map保持。未编译、构建、框架/数据库/应用执行、联网、安装、提交或发布。

[机器记录](p0-p1-repair-round85.json) · [源码补丁](p0-p1-repair-round85.patch) · [有限差异清单v20](p0-p1-difference-backlog-v20.json)
