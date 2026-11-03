# P0 / P1 第十八轮代码复查

2026-10-30。本轮仅比较本地源码、原反编译片段、Mach-O和已有模型证据；保留已落盘改动。未修改218个生产文件、迁移台账或版本，未编译、构建、安装、运行应用、联网、提交、推送或发布。

| 当前暂定清单 | 结果 |
| --- | ---: |
| 有明确有限比较结论 | **634 / 646（98.14%）** |
| 有限合同一致 | 485 |
| 明确差异记录 | 140 |
| 用户指定适配 | 9 |
| 未闭合 | 12 |
| P0 | 263 / 265（99.25%） |
| P1新增独立地址 | 371 / 381（97.38%） |

固定v3清单646项，9个共享地址只计一次。本轮重审12个已有未闭合地址，净增4项有限结论：2项有限一致、2项差异。所有记录full_function_migration_verified仍为false。此百分比是当前清单的比较进度，包含尚未修复的差异，**不是Pasto迁移完成率**；差异记录也不等于独立bug数。原版全量优先级分类与9个暂缓边界仍未闭合。

## 确认的内容投影差异

3724f0的正常多项纯文本分支现在有具体输入证据：给定两个有效短文本pasteboard items `pasto alpha`、`pasto beta`，原版逐项读非nil plain string，按顺序以ASCII空格连接成`pasto alpha pasto beta`。Pasto采集虽然保存了全部raw items，但ClipboardItem.plainText取首个可读文本，Entry直接把它交给SDK textContent，因此当前只传入`pasto alpha`。

生产链两侧均已绑定：原371998把rawType5传入content闭包，经3753f8→372440→375480→3724f0；当前captureWithInsertionResult→Store/Persistence→liveEntries→Entry→searchableItem。ARM在3731d4调用37c9a8逐项读取，3732a8/2ac装入一个空格的小字符串，3732b4调用dyld真实绑定的Swift joined(separator:)。有效非空结果不进入损坏数据或空内容fallback。

这是源代码和指令推导出的内容差异，没有运行原应用、Swift或CoreSpotlight查询；不据此声称已经测得具体搜索排名/命中差异。富文本、链接、文件、图片、OCR和完整错误域不由此判全量完成。

## 历史token缓存策略差异

36e4f4的token持久化输入已追到实际工厂：CDSearchIndexerDataSource metadata明确coordinator+0x70、context+0x78、_historyTokenData+0x80、historyToken+0xb8。构造器使用c43258 keypath，其相对getter/initializer分别到3707a8/371394，二者创建固定`indexHistoryTokenData`键；默认Config依赖最终取得standardUserDefaults。

当前observe以首persistentStore.identifier拼接`pasto.search.history-token.<identity>`，缺identity时不持久化。给定相同默认偏好存储及两个不同本地store身份，原固定槽与当前按身份分区策略不同。此结论比较的是缓存分区规则，**不是把软件改名或自有偏好前缀当bug**；不推断token失效、历史丢失，完整依赖覆盖、取消、错误及通知生命周期仍未全证。

## 补齐的有限一致

- 024274：只限所有相关历史记录均未软删除、普通有效历史项各关联0或1个有效分组，且计数/确认/清理/提交成功的路径。原History count最终使用timestamp != nil；确认后369328 fetch，363004清timestamp，list为空时经3646ec deleteObject，有list则保留。当前eraseHistory删除history-only无组项，保留有组项并清isInHistory，Persistence增量删除被移除实体。两侧历史成员资格及保留/删除结果有限一致。当前SQLite.timestamp仍保存createdAt，独立inHistory字段表达成员资格；这里使用Pasteboard的Date/nil适配语义，不能写成当前数据库timestamp会变nil。softdelete、无context、保存失败、多组/损坏关系及完整菜单门控不覆盖。
- 355874：只限非空query成功完成且返回0 ID。新增原360774→360808证据明确零ID才subject.send(nil)，355a98再映射为Just(emptyArray,emptySet)，switchToLatest交付空值。当前成功空found写identifiers后onUpdate，visibleItems为空、normalizeSelection清除不可见选择。不是拿两个无关的空输出判等；初始构造nil、空query的历史/分组列表、pending旧ID、错误/取消以及223430的callback Optional均排除。

## 仍未闭合

建议链0403f4/041190和setter2e1b54已补owner、CoreDataSuggestionDataSource(viewContext)注入及context生产者，但仍未闭合对应当前按需provider的同域输入、生命周期与最终菜单行为。当前MainActor provider到show无await，不能编造跨挂起取消竞态。

223430/2234e0/22be98已知reload、重读dataSource、selection与bounds/layout动作；仍缺UI sink Optional与当前具体事件的精确映射，不能把subject nil直接等同其param_1 nil。

| 优先级 | 未闭合地址 |
| --- | --- |
| P0 | `Paste:0x1003594e4`, `Paste:0x100368250` |
| P1新增独立项 | `Paste:0x1000403f4`, `Paste:0x100041190`, `Paste:0x10004430c`, `Paste:0x100044aec`, `Paste:0x1000f733c`, `Paste:0x100223430`, `Paste:0x1002234e0`, `Paste:0x10022be98`, `Paste:0x1002e1b54`, `Paste:0x1002f7d60` |

## 验证与证据

292项Python源码/静态证据检查通过（既有284项加本轮8项），0失败、0错误。检查完整原片段/当前字面引用摘要、实际keypath与metadata字段、Swift joined的导入和调用、正常清历史保留/删除链、真实零结果producer及不变生产文件。例子是源码绑定的派生输入输出，不是应用功能回归或原二进制差分执行。

- [逐地址记录](p0-p1-review-round18.json)
- [metadata、偏好键和文本连接指令证据](p0-p1-review-round18-static-proof.json)
- [固定清单v3](p0-p1-review-scope-v3.json)
- [执行计划](offline-migration-plan.md)

此前115条差异/109组仍是历史快照，不代表当前140条记录的完整分组。本轮所有差异只记录，没有修改生产实现。
