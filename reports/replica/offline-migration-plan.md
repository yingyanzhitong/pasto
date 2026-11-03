# Paste → Pasto 离线迁移目标

建立于 2026-10-29，目标进行中。发布基线为 `050e6878` / `v1.0.2`；以下工作均留在本地，不随该版本发布。

## 最新执行范围（2026-10-30）

用户最新指定执行顺序：**先修复P0，再检查P1，最后修复P1**。P0当前已确认81条有限差异及额外消费者/异常日志副作用已修；P1五模块当前入口检查后，两处新增搜索分支已按原生metadata/typed empty分支修复。继续P1具体父合同与一个未知的源码复查及必要修复，不声称全P1/原全函数验收；P2/联网排除，不编译、构建、安装、运行、提交或发布。

只读阶段结果冻结在[第二十八轮报告](p0-p1-review-round28.md)：暂定清单654/656有有限比较结论（99.70%），其中145条差异尚待修复、2项未闭合。该比例不是迁移完成度。修复前218个生产文件已另存 `.local/p0-repair/phase-1/before`，保留用户此前全部改动。

本阶段以已确认有限差异为修复分母；v92对齐字体traits/切换/规范化原descriptor读取及懒失败回退，选区union/逐run变换/saved-range weak Undo与实际toolbar消费者核复用。250记录218组/17额外合同：P0 81/81、P1 169/169、总250/250（有限100%），见[第188轮](p0-p1-repair-round188.md)。2804项源码检查覆盖通过，2源3增量/245不变；unknown0f733c及编辑/OCR其他实际父合同继续，不冒全函数完成。

## 范围与执行方式

按真实功能调用链批量比较反编译证据与当前源码，先查用户操作所依赖的生产入口，再查分支、错误、状态、持久化和消费者。完整已有实现直接复用；共享方法一次核对、绑定所有真实调用处，避免重复重写。旧文件摘要变化只触发方法复核，不直接判为实现缺失。

当前对照 P0 与 P1 源码及原合同，复用不变证据，修复已证差异并做无需编译的代码测试。禁止 Swift/ObjC 编译、构建、安装、运行应用、UI/MCP/跨应用测试，以及提交、推送、版本标签和发布。代码测试明确标为源码级检查，不冒充应用功能回归或原二进制差分执行。

后续P0闭合审计须把未完成项对应到具体未实现或尚未证明的输入、输出、分支、错误及副作用；仅有运行/ABI验证限制不新增差异记录，也不能用符号存在或库存扫描代替行为证据。

不处理 iCloud/CloudKit、远程账户/共享协作、联网预览、网络遥测及收费授权。既有联网代码保留，不运行、不删除；混合方法只核对本地分支，不凭关键词把整个方法排除。跳过 `0x100ac35f8`、`0x100ac746c`。品牌、兼容数据标识、未用颜色优先和面板内分组删除等用户明确要求继续保留，不为模仿原版而撤销。

## 优先级与模块 Todo

下表是当前阶段Todo。唯一in_progress为P1源码修复；当前079430有限本地差异已修，04430c源码合同已核实复用；继续0f733c输入/消费者与具体父合同，完整迁移不冒称通过。当前五模块入口检查结果保留，两处搜索额外合同130已源修复，normal证据与129发现依据不删。P2排除，有限100%不是整体目标完成率。

以下长段为此前实现阶段历史，不作为本阶段新增修复计数：

同一时间仅一个模块为 `in_progress`。快捷键、复制、数据和采集已完成有限批次核对；模型、DI、ABI、原 applier 邻项消费及错误边界仍排队待证。已修复采集许可前写盘、设备覆盖、时间与 Stack 生产事件顺序，第九轮修复搜索 Esc 并复核面板生命周期，第十轮补搜索上限，第十一轮补双流/结果/排序，第十二轮补索引历史日期并纠正卡片定位与普通选组入口归类，第十三轮补Command+G定位和pendingFocus恢复，第十四轮补筛选候选顺序和完整query节点双向交付，第十五轮复用网格导航并补本地键盘监听/事件flags/清理，第十六轮区分指定ID重建并将ack从搜索完成前移到索引完成，第十七轮补已证实的指定ID100条分批；第十八轮确认索引状态依赖缺失的持久层身份和实体变更流，第十九轮补第一持久存储 identifier 提供者及原两非空身份比较分支；第二十轮补本地历史通知/变更合并/token成功推进和串行SDK消费；第二十一轮拆开查询 Task 与串行索引消费，普通实体变化不再替换 query，索引错误不清查询结果；第二十二轮补有序输入ID逐100 live fetch，缺项/空结果仍推进输入区间，去掉Set/UUID预过滤压缩位置；第二十三轮沿真实work pointer确认删除服务并补独立100条有序删除，SDK前不再UUID过滤；现继续 P0 数据与事务基础，搜索模块保留待继续。切换模块不表示上一个模块已完整迁移。

| 优先级 | 模块 | 状态 | 核对重点 |
| --- | --- | --- | --- |
| P0 | 已确认差异修复与阶段收口 | completed | 81条已确认有限差异及mixed/current-device/raw local log增量已修，五模块当前入口已复核；独立telemetry已证且排除，compat/constructor/error文字/运行ABI限制分列，不冒全函数验收 |
| P0 | 快捷键与选区 | pending | applied optional native拖放/同步preview索引/嵌套组/惰性同Item标识已接；0679ac→ActiveSelection→已定位sink现已证NSUserActivity跨设备Handoff更新，排除仅该子链，不接OSD或相邻关闭回调；其他可能间接消费者、super/responder/完整重入待证，不称全选区完成 |
| P0 | 复制与直接粘贴 | pending | native及真实mixed输入逐条读同entity/legacy值；purelegacy API保旧，copy/drag旧值格式各自保留、聚合尾一致；combined targets保序重复，native仅recency标记不覆盖legacy。验证/合并在write/count后catch内，非内容复制前置。raw-data异常empty输出已核，本地命名level3日志与empty已接；全constructor/精确error文本/无效required关系不冒完整ABI等价 |
| P0 | 数据与删除安全 | pending | 已接List图、属性/refresh、Optional timestamp与旧显示日期兼容；ItemData关系/替换及native读取、旧库必需关系迁移policy已接；capture同事务data→preview→source→原生timestamp并抑制二次替换；恢复按倒序逐项Date→原生setter再清理/refresh/save，相同timestamp不重写；commit内不reset；仅save失败诊断/逐项校验/rollback后抛原错误，callback失败直接退出，异常桥限save。无share输入不克隆。删除输入已接appliedItems，全量刷新无选区保护，普通增量在应用数据后交付空/幸存选区；有效source安装已接epoch/首快照；已复核无share有效local history/group的Native Date/容量/first-refresh有限链；已接原生Sequence/事务交接，prepare在writer/count后的错误域，native/mixed targets保同对象与顺序；保留完整原实体/DI/ABI父链与跨进程context生命周期；未执行CoreData迁移/refresh，不称原厂全模型 |
| P0 | 剪贴板采集与格式保真 | pending | native查重同实体、incoming替换与必要metadata、hit保device、miss先device后content/preview、pending且无content插入对象重试已接；miss当前device按serial identifier首条查询/hit不变/miss原type2与机型provider，旧name/UUID归档helper保留。剩余按实际可达错误/输入核证；已存在坏compat metadata严格拒绝以保护旧组是兼容边界，不能泛化当作所有native主路径未实现；151已将原willSave同体接入实际Item共享基类，native writer更新Date门对齐；不混同无timestamp字段的ItemData模型 ；155补Item required createdAt及真实awake，与history timestamp分离；旧日期关联迁移保留、不伪造当前时间 |
| P0 | 面板生命周期与焦点 | pending | 已接首次native窗口/订阅、Published/真实Stack消费、show当前content高度/display=false和两frame写、原动画包装与强捕获；保留完整原子类/DI/重入/返回表示与原生布局/焦点边界，不因切批标模块完成 |
| P1 | 当前五模块入口检查批次 | completed | 搜索/分组/Stack/编辑/OCR当前入口已有有限比较；后续新确认差异另入修复表，不能外推全模块验收。04430c已在174核实复用；unknown仅0f733c |
| P1 | 源码修复 | in_progress | 字体descriptor读序/失败回退3合同已修，选区union/run变换/saved-range weak Undo与toolbar实际路径核实复用；2804源码覆盖绿，250/250有限100%。继续编辑config/VM任务/OCR实际父合同及unknown0f733c，新P0先修，P2网络排除 |
| P1 | 搜索与筛选 | pending | query/model/弱回调、源/Task/Undo/anchor、Menu/List生命周期、filter标题及原生图标、description协议与query数组格式已接；unknown0f733c及其他实际父合同继续，不因ABI/运行限制冒差异，CKShare协作排除 |
| P1 | 分组及本地分组迁移 | pending | List插入校验/class defaults及List/Metadata willSave本地updatedAt已接；作者syncApply只读guard保留。155轮创建日期改动保留13旧候选/helper保持，实际model hash/迁移及完整Syncable类族/DI/创建父合同仍待证 |
| P1 | Stack 与批量使用 | pending | native队列/行/coder/拖动getter和真实关闭owner→清content→fresh empty session已接，旧偏好queue只留编解码不恢复。SwiftUI/ARC外持/重入/全DI及Nib布局父合同仍开，不冒全同 |
| P1 | 文本与富文本编辑 | pending | native读写/工厂、weak异步交付、Editable held正文及字体descriptor读取/回退已接，选区union/run变换/saved-range Undo及toolbar current-range核复用。继续构造/config/VM任务、具体codec/fault父合同，P2样式排除 |
| P1 | 图片与 OCR | pending | 四叶是原Spotlight worker消费者、空格join；系统选区复制是VisionKit自动overlay，当前有限合同复用。新增整图OCR菜单换行输出/旧ID门为独立便利动作，无已证持久化损失；不冒完整文字交互/父生命周期通过 |
| P2 | 本地预览与界面 | pending | 用户已排除本轮复查；文本/图片/文件/链接本地预览、卡片、菜单、布局与交互状态 |
| P2 | 偏好与本地隐私 | pending | 用户已排除本轮复查；默认值、历史保留、暂停、排除应用、快捷键设置与兼容解码 |
| P2 | 离线归档导入导出 | pending | 用户已排除本轮复查；类型与版本、损坏数据、路径、事务、内容及组关系保留 |
| P2 | 本地系统入口 | pending | 用户已排除本轮复查；登录 Helper、本地系统动作及依赖注入；不调用联网或 MCP 验收 |

## 历史全范围记录（不再作为当前总进度）

每个模块必须列出原地址、当前符号、合同、实际调用处、源码/伪代码摘要、差异及源码测试。逐地址采用“合同已对齐 / 已修复待继续核对 / 有差异 / 待证 / 用户指定适配”，不能把一个修复覆盖的父链全标完成。只有范围内合同和消费者闭合才完成模块；未知项继续追踪，不用结束一批替代目标完成。

- 已批量扫描地址 **81,134 / 81,134 = 100%**，只代表库存检查。
- 历史标记已迁移 **1,648 / 81,123 = 2.0315%**，当前部分迁移 582；包含过期证据，不是当前产品完成率。
- 最近一次历史人工批量对照 802 个唯一地址：642 可复用、18 有差异、142 待证；未自动沿用为本轮当前证据。
- 最新扫描检查 2,239 条映射，322 条历史完整标记源码摘要一致、267 条文件变化待方法复核、1,059 条未记录该类摘要；SDK 复用报告有 960 条摘要一致。这些类别可交叠，均不自动增加完整计数。
- 当前二十三轮去重复核 515 个原地址（515 / 81,123 = 0.6348%），包括第六轮 70 条全部输入未变的旧合同复用、第七轮 38 条可逆源码差异证明下的未变叶子方法复用，以及第十轮 31 条输入均未变的搜索旧合同复用；不表示全部重新人工逐行对照，全库存 317 条候选也不全部计入。历史已计数方法复核不重复增加迁移计数，当前 partial 为 582，没有升级完整标记。
- 最新进度与下一批入口见 [第二十三轮删除服务记录](offline-migration-p0-round23.md)，此前证据见 [第二十二轮](offline-migration-p0-round22.md)、 [第二十一轮](offline-migration-p0-round21.md)、 [第二十轮](offline-migration-p0-round20.md)、 [第十九轮](offline-migration-p0-round19.md)、 [第十八轮](offline-migration-p0-round18.md)、 [第十七轮](offline-migration-p0-round17.md)、 [第十六轮](offline-migration-p0-round16.md)、 [第十五轮](offline-migration-p0-round15.md)、 [第十四轮](offline-migration-p0-round14.md)、 [第十三轮](offline-migration-p0-round13.md)、 [第十二轮](offline-migration-p0-round12.md)、 [第十一轮](offline-migration-p0-round11.md)、 [第十轮](offline-migration-p0-round10.md)、 [第九轮](offline-migration-p0-round9.md)、 [第八轮](offline-migration-p0-round8.md)、 [第七轮](offline-migration-p0-round7.md)、[第六轮](offline-migration-p0-round6.md)、[第五轮](offline-migration-p0-round5.md)、[第四轮](offline-migration-p0-round4.md)、[第三轮](offline-migration-p0-round3.md)、[第二轮](offline-migration-p0-round2.md) 与 [首轮](offline-migration-p0-round1.md)。每轮单列迁移计数、当前复核和差异消除比例，禁止用入口覆盖率或扫描率充当 Pasto 完成度。

## P1 修复批次（复查后）

1. 搜索控件、输入顺序和应用/设备/分组候选native来源已接；完整optional-source/异步availableFilters父合同继续保留，下一索引内容投影/延迟闭包。
2. 搜索内容投影、单分组/可选设备/延迟内容、SDK更新标志及错误边界。
3. 搜索索引持久IndexingState、availability/active、reset/取消/ack及列表数据来源与观察。
4. 分组菜单/归属/创建顺序和Stack类别图标；保留未用颜色优先、面板内删除等用户适配。

每批优先复用已有原函数实现，按共享生产链修一次、绑定真实调用处；分母更新为v8的152（含本轮新增两条确证缺口），不把审查条数或库存数量算修复数。
