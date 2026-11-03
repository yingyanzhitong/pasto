# P0 / P1 第十六轮代码复查

2026-10-30。仅比较本地源码、原反编译片段、Mach-O、SDK与原应用资源；没有编译或运行应用，没有联网、提交或发布。保留已有改动，218个生产文件、迁移台账及HEAD摘要保持不变。

| 当前暂定清单 | 结果 |
| --- | ---: |
| 有明确有限比较结论 | **625 / 646（96.75%）** |
| 有限合同一致 | 483 |
| 明确差异记录 | 133 |
| 用户指定适配 | 9 |
| 未闭合 | 21 |
| P0 | 262 / 265（98.87%） |
| P1新增独立地址 | 363 / 381（95.28%） |

固定v3清单646项，9个共享地址只计一次。本轮重审13个未闭合地址及1个已有差异解释，净增7个有限结论：5项有限一致、2项差异。修正旧解释不计为新增闭合。此百分比是当前清单的比较进度，包含尚未修复的差异；不是Pasto迁移完成率或原版全部P0/P1分类完成率，差异记录也不是独立bug数。所有full_function_migration_verified仍为false。

## 本轮结论

- Stack单元更新0519f8→051d2c→31eba8：原先读取条目的rawType，按类别选择imageNamed资源；当前真实AuxiliaryViews消费者从来源应用读取rawIcon，缺省用doc.on.clipboard.fill。确认图标来源策略差异，没有执行图形渲染或像素比较。
- 索引worker初始化2f00dc：原读取合法IndexingState，检查schemaVersion与完成计数，完成且非空时通过CSSearchQuery探测索引；健康非空结果沿用状态。当前needsReset初值true，首次drain删除当前domain再重建，初始化选择策略不同。原metadata确认五字段为schemaVersion、totalItems、indexedItems、oldestTimestamp、invalidItems；探测串直接从同源Mach-O读取。本结论不把supplied state的存储后端或完整actor异步生命周期冒称已证明。
- 更正040054旧解释：isActive分支调用03e7d0只是取得lazy searchField，再向window请求makeFirstResponder；它没有关闭SearchBar。仅inactive分支才调用2f7d60(0)重置输入/history。当前结束编辑设置focused=false，没有对应主动恢复请求。差异状态保留，但撤回此前“原关闭、当前保留非空搜索栏”的描述；没有推断最终系统焦点结果。
- 0407f8的有效TextKit2布局域（对象存活、manager可用）从layoutViewport、caret line geometry到convert坐标有限一致；对象缺失、none及全部窗口清理域不外推。
- 04371c的标签属性及canonical en/zh-Hans占位值有限一致。直接解析原bundle的Localizable.strings并验证原应用arm64摘要匹配冻结二进制，值为Search/搜索；其他语言及完整locale fallback不计一致。派生资源字典仅作线索。
- 308c8c的有效deviceRGB归一化RGBA域按乘255无符号截断再ARGB打包，与当前实际来源颜色链有限一致；不覆盖扩展色域和非归一化输入。
- 3c05d4在可解码有序pasteboard-items域只取首项，按flatRTFD/RTFD/RTF优先、同项plain回退，再投影编辑字体/粗斜体/下划线/删除线；当前真实预览消费者有限一致。完整缓存、会话提交及容器损坏不外推。
- 3c7c4c在实际source icon调用的128×128目标域，取bestRepresentation、分别限制宽高，创建8位4通道alpha bitmap、设置/恢复context并draw，有限一致；不扩张到所有目标尺寸或绘图像素。

## 仍未闭合的原因

建议任务041190：当前MainActor任务从同步provider到menu.show之间没有await。取消分支动作缺失本身不能证明“下一次查询在provider完成后抢占导致旧窗残留”；调用者会取消/隐藏或启动替换任务。保留unknown。

2f7d60：是否应清undo/history取决于原调用者isActive门；当前view卸载及Coordinator生命周期也影响最终状态。不能仅凭当前缺少显式reset确认可复现的同触发差异。2f7c14和2f7370的完整回调槽及消费者仍待映射。

P0三项仍为024274清历史完整计数与事务域、3594e4事务repository缓存及context模型映射、368250固定History创建和错误消费；P1还有18项。原版边界分类9项暂缓仍保留，未用本轮固定分母掩盖范围未闭合。

| 优先级 | 未闭合地址 |
| --- | --- |
| P0 | `Paste:0x100024274`, `Paste:0x1003594e4`, `Paste:0x100368250` |
| P1新增独立项 | `Paste:0x1000403f4`, `Paste:0x100041190`, `Paste:0x10004430c`, `Paste:0x100044aec`, `Paste:0x100051ec8`, `Paste:0x1000f733c`, `Paste:0x100223430`, `Paste:0x1002234e0`, `Paste:0x10022be98`, `Paste:0x1002e1b54`, `Paste:0x1002f7370`, `Paste:0x1002f7c14`, `Paste:0x1002f7d60`, `Paste:0x1002fc0ec`, `Paste:0x100355874`, `Paste:0x10036e4f4`, `Paste:0x10037063c`, `Paste:0x1003724f0` |

## 验证与证据

275项Python源码/静态证据检查通过（既有266项加本轮9项），0失败、0错误。检查包含完整原片段/当前引用摘要、真实消费者、同步任务无挂起点、原bundle资源与二进制配对、metadata字段、原getter与实际焦点分支及计数。它们不是应用功能回归，也不证明全部原函数已经迁移。

- [逐地址记录](p0-p1-review-round16.json)
- [静态证据](p0-p1-review-round16-static-proof.json)
- [固定清单v3](p0-p1-review-scope-v3.json)
- [执行计划](offline-migration-plan.md)

此前115条差异/109组清单是历史快照，不等于当前133条差异的完整分组。本轮所有差异只记录，没有修改生产实现。
