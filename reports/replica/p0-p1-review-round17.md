# P0 / P1 第十七轮代码复查

2026-10-30。本轮仅比较本地代码、完整原函数片段、Mach-O、SDK和原模型资源；保留已落盘改动。未修改218个生产文件、function-map或版本，未编译、运行应用、联网、提交、推送或发布。

| 当前暂定清单 | 结果 |
| --- | ---: |
| 有明确有限比较结论 | **630 / 646（97.52%）** |
| 有限合同一致 | 483 |
| 明确差异记录 | 138 |
| 用户指定适配 | 9 |
| 未闭合 | 16 |
| P0 | 262 / 265（98.87%） |
| P1新增独立地址 | 368 / 381（96.59%） |

固定清单v3与646项分母，9个共享地址只计一次。本轮重审12条记录：11条旧未闭合、1条旧结论更正；净增5个有限比较结论（1项有限一致、4项明确差异），另将旧36fa2c的有限一致改为带同源差异的解释，后者不增加比较完成项数。差异记录数不是独立bug数；比较进度包含尚未修复的差异，不等于Pasto迁移完成率，原版全部优先级分类仍未闭合。全部full_function_migration_verified保持false。

## 本轮结论

### 搜索输入与撤销回调

原03f574的ARM调用参数和2f7274的存储明确四个callback槽：+0x48经041bb8到0406ac构造富文本；+0x28经041ba8到040284应用文本/选区；+0x18经041ba0到0401ec发布query；+0x38经041bb0到0403b0/0403f4更新建议菜单。结论来自实际寄存器与完整桥函数，未按Ghidra参数序号猜槽。

- 2f7370只在新旧nodes不同、且rawNodes不等normalizedNodes的重绘分支确认顺序差异：原构造/应用文本后发布query，最后处理建议；当前propose先publish，再清建议并重绘。**已规范化普通输入在两侧均发布并返回true**，不属于上述差异。撤回子审把相等分支当内部重绘/返回false的解释，不推断最终文本必然不同。
- 2f7c14成功undo/redo结果的原顺序为构造、显示、发布、清空建议context；当前restore首步dismissSuggestions后才构造、显示和发布。只确认调用时序，不声称最终系统状态或选区必然不同。
- 2f7d60保留未闭合：原040054仅inactive分支调用mode0 reset，不能把所有当前结束编辑或view卸载都当同一触发并指认缺清理。

### 实体身份与历史变更

本轮使用Python plistlib静态解析原应用bundle的v5Paste.momd/VersionInfo.plist与v10.mom归档UID；没有实例化Core Data模型或运行应用。VersionInfo指定v10，实际ItemEntity类为PasteCore.ItemEntity，identifier为String属性，timestamp可选，list为可选to-one关联；当前独立模型实际为Item/key，key由item.id.uuidString写入。

- 37063c成功读取原ItemEntity.identifier并返回String；当前历史读取Item.key。此前已证有效空库首次普通文本的原identifier为文本MD5，当前为UUID，本轮补齐真实写入→历史读取→applyHistoryChanges消费者，确认该身份表示差异继续传播。缺对象/读取失败转none的有限合同仍保留。
- 更正36fa2c旧报告：原按ItemEntity类型名过滤、insert/update读identifier、delete读取tombstone的identifier；旧描述误写成当前Item/key。集合归约顺序规则仍有限一致，但生产身份值不能整体说相同；沿用360d9c同源差异，不因字段/实体改名本身报一个新产品故障，也不推断当前索引失效。

### 值拷贝与Stack摘要

- 2fc0ec已从opaque value-witness调用追到真实方法：cad06c单例描述符指向fc1560 metadata模板，模板前word指向fc14e0 witness表，+0x10为37582c初始化拷贝。该方法保留content/imageData闭包及环境，不执行内容求值；faafc实际调用后把值交给协议数组，后续builder才消费content。当前Entry只携带已物化text，实际searchableItem直接读取textContent。该记录沿用371998/2faafc的能力差异，**不是要求迁移编译器ABI，也不是声称Swift没有值拷贝**。完整metadata初始化与ARC生命周期未外推。
- 051ec8补有限一致：成功生成有效preview的文本（原始NSAttributedString.length即UTF-16长度≤500）、有效URL、单个有效文件URL，真实采集/分类→Store preview生成→codec→Stack消费者的摘要结果对应。损坏或未知metadata、缺URL、任意导入preview、多文件标题及所有编码失败仍不覆盖。

## 未闭合与撤回的推断

- P0清历史已获得更强原模型证据，原最终History count谓词为timestamp != nil；rawType2才使用list == %@。但当前isDeleted与isInHistory可并存，尚未绑定原对应删除操作如何改变timestamp/list，不能直接把当前软删除对象当原普通非nil timestamp对象，故024274仍未闭合。
- 3594e4的事务repository缓存与当前长期context生命周期不同，尚无同域业务副作用结论；368250固定History创建的永久ID/编码失败及当前隐式历史模型映射仍缺证。
- 044aec/04430c的字段初值和super转发可见，当前生产入口是usingTextLayoutManager:true；SDK分别声明该入口与frame:textContainer:，没有提供内部派发实现。既不根据缺显式Swift调用宣称不可达，也不推测必经当前override。Coder静态资源负检索同样不能证明外部归档不可达。

| 优先级 | 未闭合地址 |
| --- | --- |
| P0 | `Paste:0x100024274`, `Paste:0x1003594e4`, `Paste:0x100368250` |
| P1新增独立项 | `Paste:0x1000403f4`, `Paste:0x100041190`, `Paste:0x10004430c`, `Paste:0x100044aec`, `Paste:0x1000f733c`, `Paste:0x100223430`, `Paste:0x1002234e0`, `Paste:0x10022be98`, `Paste:0x1002e1b54`, `Paste:0x1002f7d60`, `Paste:0x100355874`, `Paste:0x10036e4f4`, `Paste:0x1003724f0` |

## 验证与证据

284项Python源码/静态证据检查通过（既有275项加本轮9项），0失败、0错误。覆盖完整原片段和当前引用摘要、原模型UID/字段、真正的copy witness和callback指令、规范化相等分支防误判、用户范围与生产文件不变。它们不是应用功能回归、原二进制差分执行或完整迁移证明。

- [逐地址记录](p0-p1-review-round17.json)
- [原模型与Mach-O证据](p0-p1-review-round17-static-proof.json)
- [固定清单v3](p0-p1-review-scope-v3.json)
- [执行计划](offline-migration-plan.md)

此前115条差异/109组是历史快照，不能当作当前138条记录的完整分组。原版9项分类边界暂缓继续保留。本轮所有差异只记录，没有修生产实现。
