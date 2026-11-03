# P0 / P1 第十五轮代码复查

2026-10-30。本轮仅比较代码、原片段/ARM静态证据和Python源码测试，保留所有已落盘改动；未修改生产源码或迁移台账，未编译、运行、联网、提交或发布。

| 当前暂定清单 | 结果 |
| --- | ---: |
| 有明确有限比较结论 | **618 / 646（95.67%）** |
| 有限合同一致 | 478 |
| 明确差异记录 | 131 |
| 用户指定适配 | 9 |
| 未闭合 | 28 |
| P0 | 262 / 265（98.87%） |
| P1新增独立地址 | 356 / 381（93.44%） |

固定第十四轮清单，不扩充分母；9个共享地址去重一次。复查31个已有未闭合地址，净增23个有限比较结论：21项有限一致、2项明确差异；另外8项仍未闭合。所有记录的full_function_migration_verified继续为false；比较进度不代表迁移完成率，差异记录也不是独立bug数。

## 本轮证据与结论

- 捕获manager的37aa10经getter取得Pasteboard后读取+0x38；原metadata/字段偏移向量明确该字段名为pollTimer（syncTimer在+0x40）。004ab8把存在值反转成paused。Pasto在有效已注册状态上读取pollTimer==nil，计时器两种状态有限一致；不覆盖weak owner消失及原lazy cache缺失路径。原helper没有执行poll动作。
- 录制器构造的shortcut Optional首值、nil error/monitor、validator包装及onDetect安装，与当前真实Binding→StateObject工厂→界面state/error消费者有限一致，不覆盖后续录制/验证流程或枚举机器ABI。
- 重命名父回调06e0dc真实转交3bae08，沿已有明确差异：原能用空白输入清空已有title，当前prompt将其当取消。该记录指向shared_difference_origin=3bae08，不重复声称一个新独立bug；owner释放路径不外推。
- 042fc8的textView focusRingType原raw2为Exterior，当前.none为raw1，确认不同。与第十四轮scroller初始化的焦点环赋值是两个地址，不能把raw2说成关闭焦点环。
- 搜索delegate刷新、super菜单nil/非nil返回、菜单过滤、filter chip构造、结束编辑和undo/redo快捷键分派补齐有限结论；TextKit2有效配置及附件provider的真实创建链已绑定。frame初始化本来就是unimplemented trap，不再当作一个正常构造器推测。
- 本地history的Optional.next输出位置、流结束/取消门、unbounded策略、消费后再取下一事件、fetch/空批次/consumer成功后推进token等有限合同已核实。37063c读取失败转nil与当前try?相同，但原identifier与当前KVC key完整成功值域映射仍未闭合。
- 清历史动作的repository consumer已接通：eccd58+0x10→eccda0，+0x38→369308→369328；后者获取固定History并fetch，再交363004清timestamp/保留分组或删孤立项。确认计数域、soft-deleted模型及全部事务错误仍待证，保持unclosed。
- 更正2f7c14角色：它是undo/redo后的状态替换与多回调分发，不是History构造器；当前restore/display/publish与其opaque callback slots尚未逐一对应。

## 未闭合地址

P0仍为3项：

| 地址 | 待证合同 |
| --- | --- |
| Paste:0x100024274 | 已补清历史实际调用链：024274→3c5408按History fetch predicate执行count；确认后3c5624→2ff310→0ad648经repository witness进入369308/369328，取固定History并fetch关联项，再经363004清timestamp/保留关联组或删除孤立项。当前clearHistory/eraseHistory承担对应职责；确认计数域、soft-deleted/无context输入及完整事务错误与当前模型尚未闭合。 |
| Paste:0x1003594e4 | 原 transaction 容器在 repo 缓存为空时，以容器 context 构造 Repo 并缓存其五字段 existential；命中时复用缓存 Repo。当前 ClipboardStore 持有长期 ClipboardPersistence，后者持有 NSManagedObjectContext 并在 perform/commit 中复用。 |
| Paste:0x100368250 | 原先按固定identifier fetch既有History，缺失才插入ListEntity，设置name/identifier，申请permanentID后JSON attributes及rawType=1。当前history由State.preferences与Item.inHistory表达，没有对应ListEntity创建consumer；完整创建/失败副作用尚未证明映射。默认保留周为用户指定值，不将这一已授权偏好差异单独冒称完整构造适配。 |

P1另有25项：

0x1000403f4, 0x1000407f8, 0x100041190, 0x10004371c, 0x10004430c, 0x100044aec, 0x1000519f8, 0x100051ec8, 0x1000f733c, 0x100223430, 0x1002234e0, 0x10022be98, 0x1002e1b54, 0x1002f00dc, 0x1002f7370, 0x1002f7c14, 0x1002f7d60, 0x1002fc0ec, 0x100308c8c, 0x100355874, 0x10036e4f4, 0x10037063c, 0x1003724f0, 0x1003c05d4, 0x1003c7c4c。

完整搜索建议/输入归一化、结果applier、索引worker、创建/解码、富文本预览、图像缩放等父合同继续保留具体缺口；未接线setter0f733c仍未知。清单全量性仍未闭合，上一轮9个边界暂缓项不自动变为完成。

## 检查与产物

266项Python源码及静态证据检查通过（包含上轮257项和本轮9项），0失败、0错误。218个生产文件与本阶段起始摘要一致；function-map与HEAD保持不变。检查绑定完整原片段、当前字面引用与文件摘要、metadata/返回指令、repository witness及统计；不代表编译或应用回归通过。

[逐地址记录](p0-p1-review-round15.json) · [字段与分派证据](p0-p1-review-round15-static-proof.json) · [固定清单v3](p0-p1-review-scope-v3.json)。第十二轮115条差异/109分组是历史整理，并未覆盖当前131条记录。
