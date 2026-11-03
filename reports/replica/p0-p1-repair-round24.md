# P0/P1 源码修复：第二十四轮

本轮闭合同一UIState内缺少集合来源重建的有限差异。原 `036ee0 → 067c84` 会在模型发布后更换applier；新applier的items为空、首快照标志未置位，`1b9b78` 下个accepted快照发nil变化描述，经 `223430` 执行full reload。排队工作经弱旧applier加载，正常旧目标销毁后不继续drain。

Pasto 新 `replaceCollectionModel(state:)` 校验真实owner后更换epoch，清旧pending/scheduled数据、清applied items、重置首快照，再通过原update排入新来源数据。有效distinct查询交付、显式chooseBoard及失效board回退均已接入；普通store/search数据刷新与选区/SwiftUI重画不直接重建。旧epoch检查先于清scheduled标志，可阻止旧queued callback消费或取消新队列。换UIState的已有路径也清applied items。

来源替换本身不清selection、pending-neighbor，不移动焦点、不立即滚动，也不强制同步drain。既有accepted data→布局→full/incremental选择→weak owner/onUpdate邻项链复用。即使新来源与旧来源IDs相同，下个首快照也执行full，恢复原选择首项和滚零规则。

| 当前有限差异清单 | 已修复 | 分母 | 比例 |
| --- | ---: | ---: | ---: |
| P0 | 47 | 64 | 73.44% |
| P1 依赖 | 8 | 81 | 9.88% |
| 合计 | 55 | 145 | 37.93% |

本轮新增 `Paste:0x100067c84` 一条有限修复，完整函数/模型仍未证明。余P0 17、P1 73，共90条差异及2未知。654/656只代表冻结的历史有限比较覆盖，不作迁移完成度。

源码合同反例：有效的两个nonempty查询均选同一搜索模型，accepted结果IDs仍为A、B且用户原选B，没有额外重入/旧applier强引用/邻项覆盖。原模型发布后新首快照full会选A、滚零；旧Pasto同state、same IDs空diff跳过full而保留B。新代码按安装事件重置，accepted首快照full。该反例不是原生运行或事件队列复现。

430项Python源码/静态检查通过，新增10项；2个旧测试文件按真实source安装与清items更新，未回滚已有修复。测试开发遇到两次body定位不含算子链/误取predicate closure，日志分别保留；修正测试定位后全部通过，生产代码未为这些错误改写。2旧生产文件变化、225个不变，无新增生产文件。主审绑定21个原C片段和340字节机器范围，并复用已绑定的上一轮正确模型路由；对子审仅验证可核片段/源摘要，不采instructions=0的反汇编摘要为机器证明。

Pasto仍使用共享UIState和值投影，epoch桥没有冒称原AnyCancellable/泛型DI对象图逐项迁移。旧applier有额外强引用或替换发生在callback重入时，原旧onUpdate是否还能交付未全面闭合；startup、History optional映射、query清理失效board导致的双安装以及同组重选是否原也发布均保留。未以推测添加去重规则。首个provider emit的具体内容不由首快照标志推断。

下一批“P0快捷键与选区”为唯一in_progress，处理鼠标、双击和长按是否读真实applied集合；数据与删除安全转pending保留完整模型/事务和取消边界，不标模块完成。基线/证据在 `.local/p0-repair/phase-24/`，见[JSON](p0-p1-repair-round24.json)和[补丁](p0-p1-repair-round24.patch)。未编译、构建、安装、运行应用、联网、提交、推送或发布；官网9文件、版本1.0.2、HEAD与全函数台账不变，目标继续有效。
