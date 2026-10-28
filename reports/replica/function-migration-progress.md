# Paste → Pasto 函数迁移进度

当前工作范围：只迁移源码和静态核对原函数合同，不编译、不安装运行、不做功能或 MCP 测试、不发布。

## 计数口径

- 原函数地址：81,134。
- 逐地址已记录的范围排除：9。
- 按用户要求跳过的反编译失败地址：2（`0x100ac35f8`、`0x100ac746c`）。
- 当前核对分母：81,123。

现有 `replica/function-map.json` 标记已迁移 1,648 个、部分迁移 414 个；其余范围内 79,061 个尚未标记完成。**台账标记迁移率为 2.0315%（1,648 / 81,123）**。

这是已有台账的标记率，不能直接视为当前源码已经重新核实的完整迁移率：部分源码摘要已过期，完整台账校验未通过，必须逐函数核对后才能刷新证据。此前 93.75% 是产品入口接入比例，不再用作本任务的迁移完成度。

## 已有迁移的批量完整度检查（2026-10-27）

截至第28轮累计逐项对照 655 个唯一地址（0.8074%），550完整、8受明确差异影响、97待证；本轮新增 13 个地址，累计确认 80 个历史SDK转发的源码直接API复用。台账 1,648 / 81,123 = 2.0315%。未编译测试或改产品源码。详见[批量报告](batch-completeness-round28.md)。

## 完整迁移判定

核对原函数的全部输入、返回、分支、错误与副作用，以及 Pasto 中实际接入的消费者。原函数对应的真实源码或系统复用合同已完整满足时可以跳过重写；仅有同名方法、相似界面、包装入口或单条分支修复不能计为完整迁移。未知及未闭合部分保留部分迁移状态。

近期补迁移：原 `0x10003738c` 的快捷键优先、Tab/BackTab 与其余输入分支，以及 `0x100037a64` 的字符串类型和单空格分支，已落到真实输入方法；快捷键编码键改为嵌套 `CodingKeys`，原公开名称保留为别名以继续复用 SDK 默认描述。完整响应链、IME 及相关父函数仍有未闭合部分，尚未更新完整函数计数。

## 本轮源码完整性核对

仅阅读成功反编译伪代码及 Pasto 源码，没有执行编译或测试。

| 原函数 | 当前源码对应 | 核对结论 |
| --- | --- | --- |
| `0x10003738c` | `ReplicaPanelContentView.keyDown` | 快捷键优先返回、Tab/BackTab 转交父类、其余输入解释三条方法分支已对应；完整响应链仍未闭合，不新增完整计数。 |
| `0x100037a64` | `ReplicaPanelContentView.insertText`、`ReplicaUIController.onSearchText` | 类型筛选、单空格忽略和真实搜索消费者存在；原 Published 写入与现有状态适配仍有差异，保留部分迁移。 |
| `0x1001e9ab0`、`0x1001e9ad8` | `OriginalShortcutValue.CodingKeys` | 已复用系统 CodingKey 默认描述；类型叶名已对应，完整运行时类型描述尚无充分证据，不新增完整计数。 |
| `0x1000ce5bc`、`0x1000ce644`、`0x1000cef84` | `PastoPinboardEntity` | 系统图标、正文符号配置和真实展示消费者存在；本轮补入原属性颜色解析、原 palette 到实际图标 tint 的路径，缺失或非 pinboard 属性保留无 tint。共享列表分支仍未闭合，保留部分迁移。 |
| `0x100322ae4` | 剪贴板归档校验路径 | 原归档实际写入的运行时类名尚未确定，不能认定归档字节及校验结果等价；不猜测替换类名，保留部分迁移。 |

本轮没有新增可确认完整的函数，台账标记迁移率仍为 **1.91%（1,549 / 81,123）**，既有完整标记仍需与当前源码逐项复核。

后续源码补迁移（同样未编译或测试）：

- `0x100018de4`：`ReplicaUIController` 接入真实 `windowDidChangeScreen` 回调。仅在当前与原弱引用屏幕均存在且不同屏时，按新屏原点、宽度及现有内容高度更新面板，再记录新屏；缺失数据和同屏均不操作。原窗口类型及完整生命周期仍待闭合。
- `0x1003e2eac`：文件预览的 Finder 操作完成后独立关闭窗口，即使当前记录已移除也执行关闭；不再被记录查询的提前返回跳过。原 VM 对记录的持有生命周期仍待迁移。
- `0x10037ae9c`：静态追踪捕获事务及保存阶段异常桥，现有有限失败/通知分支可复用，没有因未知原合同新增捕获逻辑。

上述均为真实消费者中的分支补齐或源码核对，未新增完整函数计数；台账标记迁移率维持 **1.91%**。

## 最新一轮源码迁移

- `0x1002dcca4`：补齐整查询替换、重复筛选不变、`addMode == 1` 去末项追加、其他模式按索引替换及负索引 trap 分支；真实建议选择入口使用同一方法，归一化仍由调用者执行。对照成功伪代码及其 dropLast、数组追加 helper 后，更新为源码已迁移，新增完整计数 1；不升级完整建议父链。
- `0x100077c54`：真实面板补入父类布局后依次设置 minSize/maxSize 的方法体，恢复窗口位置后接入调用；原窗口/actor 生命周期差异仍单独保留。
- `0x1003ec168`：文本预览测量改用原保存富文本，保留原先已迁移的 2000 UTF-16 截断；完整 inset 尺寸组合仍未闭合。
- `0x100312874`：按原常量将 Quick Look 请求改为 256×256；系统图标回退保持 128×128。原配置与 DI 边界仍未闭合。

本轮仅源码阅读、修改及台账计数；未解析编译、运行测试或发布。台账已迁移 **1,550 / 81,123 = 1.9107%**。既有历史完整标记的当前源码复核问题仍保留，未宣称全量验收。

## 后续完整方法迁移与复用

- `0x1003ec168`：补齐文本预览尺寸计算全部值分支。使用原保存富文本、2000 UTF-16 上限、主屏半尺寸/无屏1000×1000、原boundingRect选项、实际文本inset、横向额外20和逐维上限；移除独立最小380×240。实际文本预览工厂继续消费，新增已迁移函数1。
- `0x1002387f0`、`0x100238ab8`：现有OSD主队列延迟0.1秒、保留动作、非nil调用/nil不操作已覆盖各自完整方法合同；对照成功伪代码后复用现有实现，新增确认2。OSD父View、配置与手势状态不随之升级。
- `0x10006ba24`：补原生集合响应器`selectAll:`入口，转发已有真实选区算法，接通菜单；原对象生命周期边界继续保留，不新增完整计数。

本轮只进行源码迁移与静态完整性对照，没有编译、解析、运行测试或发布。当前台账为 **1,553 / 81,123 = 1.9144%**；既有历史证据待当前源码复核的限制保留。

## 最新批次：完整值方法与转发复用

- `0x1003c05d4`：文本预览不再只读顶层payload或现成plainText，改为完整原表示数组的首项；复用富文本优先解码、tableBlocks清理和同项纯文本回退。原文及独立编辑归一化副本由初始化/reload保存并实际消费，新增完整方法1。
- `0x100312ae4`：逐分支确认文件元数据方法现有实现完整，保留URL顺序/重复、首项大小/预览、错误归0和空数组分支，真实存储与显示已接，新增确认1；其下级缩略图动态Config服务缺口继续单列。
- `0x1001e69bc`、`0x1001e69c4`、`0x1001e69cc`、`0x1001e69d4`、`0x1001e69f4`、`0x1001e69fc`：成功伪代码、原二进制单条B指令、现有目标源码和字符/词/行/文件计数、打开按钮、暂停OSD消费者均对应，按源码转发合同直接复用，新增确认6；不为原地址另写重复包装。
- `0x100077b38`：面板已补菜单验证业务分支，关闭动作返回true，nil及其他action交父类；未新增可见关闭菜单，原窗口父类/生命周期仍单独保留，不增加完整计数。
- `0x100211e80`：字符/词/行及底栏方法重新静态复核，可复用原已登记实现，没有重复计数。

本轮新增确认完整源码迁移 **8**，累计 **1,561 / 81,123 = 1.9242%**。只读源码/原证据并修改源码及台账，未编译、运行测试或发布；完整运行等价仍未声明，历史证据的当前源码复核限制仍保留。

## 最新批次：源码转发与 Stored 方法组

- 其余13个已建立原源码目标映射的转发入口：逐项读取成功伪代码、当前原二进制B指令、目标源码及真实消费者后，复用对应完整方法。涉及日志dispatcher、快捷键按钮样式/状态hash、动态颜色/属性统计、图层刷新、标题尺寸刷新、建议匹配、共享UndoManager和错误文案。新增确认13，具体地址见`source-thunk-reuse-static.json`；其他SDK及未知入口没有随组升级。
- `0x100314ea8`、`0x1003152d4`、`0x100316f08`：现有Stored完全对应原13字段及其类型/顺序，合成encodeIfPresent、decodeIfPresent、精确CodingKeys解析直接复用。nil省略、missing/null→nil、任意坏present字段使整记录失败及未知键→nil均逐分支对应；真实五类编码解码路径消费。新增确认3，不升级外围Config、metadata枚举、description或ABI。
- `0x100036ff8`、`0x100037108`、`0x100037238`：真实面板补入接收焦点、附窗初始响应器、背景鼠标事件后的集合焦点方法；集合晚附加/移除同步自身initialFirstResponder所有权。空结果不创建原生集合的模型差异保留，暂不增加完整函数计数。
- `0x1003ec13c`聚焦转发方法的父调用点证据不足，保留候选，没有添加无消费方法或自动抢焦点逻辑。

本轮源码迁移与静态复用确认新增 **16**，累计 **1,577 / 81,123 = 1.9440%**。未编译、解析、测试、运行或发布；历史完整标记仍需按当前源码复核，不声明全量运行等价。

## 最新批次：颜色格式、焦点回退与协议转发

- `0x100206b5c`：新增实际共享颜色formatter，恢复原独立方法的小写返回、deviceRGB失败归黑、逐通道乘255后Int截断/非有限值及越界trap、读取但不输出alpha、不clamp。卡片及完整颜色预览显示/提交在调用处uppercased，移除旧重复formatter，新增完整1。
- `0x1000778c0`：删除额外集合优先级，恢复显式响应器直交父类；nil依次initialFirstResponder/contentView，返回父类实际Bool。真实show/hide/search调用消费，原actor检查桥是另一个函数；恢复完整计数1。
- `0x1003c14d0`：现有文本提交属性判定完整复用，bold/italic字体或underline/strike键存在才置isRich/stop；空及其他属性不修改标志。真实仓库文本提交据此选择RTF/纯文本，新增确认1。
- `0x100315a10`、`0x100315a24`：完整原方法仅转发Stored解码/编码及其throw；合成Codable协议入口由真实JSON/PropertyList路径消费，新增确认2，不另造包装。
- 原窗口Key/Main getter的执行器诊断、Stored部分键方法的协议槽与污染伪代码、`0x100218b08`灰度转换未确认返回分支继续保留缺口，不随已满足的可见效果升级。

本轮新增确认完整源码函数 **5**，累计 **1,582 / 81,123 = 1.9501%**。只读原证据/源码、修改源码及台账；没有编译、解析、运行测试或发布，历史证据限制与完整运行等价未验状态保留。

## 最新批次：日期显示与完整值方法复用

- `0x100309c40`、`0x100309c7c`、`0x100309cd0`：新增原相对日期、单单位缩写日期、绝对日期formatter初始化；保Void写共享槽副作用及独立once初始化。配置依次为named、approximation=false/max1/abbreviated、mediumDate/shortTime。
- `0x100309d18`、`0x100309e0c`：新增首个正year/month/day/hour/minute/second单位选择及完整三模式日期方法；无单位或组件formatter返回nil时回named。卡片原手写中文/截负时间逻辑已替换，未来日期保系统本地化，原absolute tooltip已接。Header compact输入与定时刷新仍单列未闭合，不升级父日期标签。
- `0x100218b08`：从原指令核清返回值，当前灰度方法完整复用，非RGB/灰度失败返回原颜色，成功返回转换结果，真实选区dimmed路径消费。
- `0x1003c4b2c`：空名称本地化Untitled、非空原样（不trim）的既有值方法完整复用，真实分组及History tab写回已接。
- `0x100087ffc`：预览管理器初始化入口复用已完整初始化体及空/nil默认值，真实UIController持有；仅新增此入口，不重复目标。
- `0x1000843a8`：Stack强持有实际窗口控制器，关闭通过controller.close而非仅orderOut；队列/方向不清，窗口复用保留。桥接/actor及额外监听适配未闭合，记partial，不增完整计数。

本轮新增确认完整源码函数 **8**，累计 **1,590 / 81,123 = 1.9600%**。未编译、解析、运行测试或发布；历史完整标记的当前源码复核限制保留，整体未完成。

## 最新批次：真实日期刷新和集合显示链

- `0x1003d0bb0`：真实卡片日期标签接原30秒单次弱定时器，刷新后重排，替换旧timer时invalidate。原producer已证明`sizeClass == 3`对应缩写，其他named；原Header.timestamp存在性用isInHistory适配，缺失时配置捕获一次now，后续同输入的刷新/compact变化保留同date，absolute tooltip同步刷新。移出界面/释放取消、重现重启属于SwiftUI生命周期适配，父DateLabel仍partial，不增完整计数。
- `0x1000844fc`：Stack反转及方向保存后同步调用原生表格updateSnippets，更新行数据和revision；不只等待SwiftUI更新。原Nib必备table与副本nil域等差异保留，记partial，不增完整计数。
- `0x1003e3638`：QuickLook构造器改为内部非可选URL存储、协议可选投影，保fileURLWithPath、原optional标题nil/empty和NSObject初始化；真实首路径消费者已接，独立构造业务合同升级完整1，父生命周期/actor桥不升级。
- `0x1002feb60`：日志可选URL getter的现有消费者已接AppMain停止诊断→文件捕获/恢复链，原函数只copy字段、无其他动作，复用现实现升级完整1。

本轮新增确认完整源码函数 **2**，累计 **1,592 / 81,123 = 1.9625%**。仅源码迁移和静态对照，未编译、解析、运行测试或发布；历史证据待当前源码复核与完整运行等价未验的限制保留。

## 最新批次：标题按需回退、Stack摘要和空集合

- `0x100308f88`、`0x100309008`：完整值方法及真实输入链核对后升级2。预览Header传入originalTitle而非原始legacy title；默认值改autoclosure，卡片已有非空显式标题时不提前解码默认元数据。所有raw类型标题、canonical文件数缺失1/空0/Int32trap、空白标题原样等分支保留；预览placeholder仍按原顺序先求默认值。
- `0x100051ec8`：新共享方法接入真实Stack行，按canonical metadata分别显示text.characters（含空串）、link.absoluteString、小写RGB、单文件lastPathComponent、多文件显式/默认标题，以及缺失/坏/图片/零文件的原字面Unknown。原空文本helper的比较符号已核为Comparable.<=，没有据Ghidra错误的<添加trap。metadata枚举编号和Item.rawType映射分别核对，新增完整1；cell图标/Nib/Entity父不升级。
- 原MainView持有集合及其焦点目标不依赖项目数；当前面板改为始终保留原生集合，空提示仅叠加。Native已有空数组layout分支复用，避免无结果时销毁实际初始响应器。完整MainView/SwiftUI生命周期仍不据此计满。

本轮新增确认完整源码函数 **3**，累计 **1,595 / 81,123 = 1.9662%**。未编译、解析、测试、运行或发布；历史证据的当前源码复核限制及整体未完成状态保留。

## 最新批次：元数据、分享值合同及原生Stack行

- `0x100315a38`、`0x100316004`：Stored与五类metadata的双向完整值转换复用，全部缺值默认、未知type回text、files/link的nil与empty差异、仅当前case字段写入均重核；五类真实编码/解码消费者已接，新增确认2。外围格式选择/Config和完整枚举ABI不升级。
- `0x100320cc0`、`0x1000183e0`：分享资格值方法及picker工厂完整复用。保known非files非空、files有效URL非空且全部本地可达、错误/非法raw拒绝，以及按content和representation顺序扁平后创建picker（含空输入）；真实Header消费，新增确认2，不宣称实际分享执行验收。
- `0x1003e1fec`：颜色通知恢复显示后的第二次读取Panel色值；nil callback不再做额外比较，有callback才再读色与原模型比较后回传，无editing过滤。完整独立通知业务方法新增确认1，父编辑/VM/actor桥不升级。
- `0x1000519f8`：真实NSTableCellView已接Stack行，按原可选outlet顺序更新image与两行摘要，旧右键菜单保留；图标仍独立注入适配，原四个20点命名资产及Nib布局未迁移，新增partial，不计完整。
- 颜色alpha调查已沿`3bc060→363ff0→360ff8→322504`闭合：原同样由掩码RGB payload重建metadata，先前“原应单独保alpha”的推断撤回，没有新增偏离原版的Store/UI接口。

本轮新增确认完整源码函数 **5**，累计 **1,600 / 81,123 = 1.9723%**。只做源码迁移与静态证据对照，未编译、解析、运行测试或发布；历史标记待当前源码复核的限制保留，整体未完成。

## 最新批次：Finder、链接标签与弱引用

- `0x1003bc874`：完整原Finder动作体迁到Core并接回按钮；逐项fileURL解码丢弃失败、保序/重复、无nonempty/isFileURL/reachable额外门控，空数组也调用Finder再deactivate。UI只保owner/数据源适配与独立defer关闭，新增完整1，不升级关闭父。
- `0x1003e7ddc`、`0x1003e7d00`：链接默认应用名CFBundleName查询的全部失败回退与空字符串保留，以及URL标签absoluteString/字体/颜色/四false/compression250，真实消费者完整复用，新增确认2；缺URL/原VM父不升级。
- `0x100225db8`：真实拖拽会话private weak属性的begin/end赋值与nil清理复用，覆盖原纯弱setter，新增确认1。`0x100225d0c`、`0x100225e10`的操作mask及开始记录业务值已满足，但原ObjC actor检查包装未证明，新增partial而非完整。
- `0x100312538`：NSColor类型转发入口复用已完整0x100308ea0的全部UInt64字节及alpha分支，由实际颜色卡片、Stack和预览消费，新增确认1；不把原类metadata cache helper或生成ABI计满。

本轮新增确认完整源码函数 **5**，累计 **1,605 / 81,123 = 1.9785%**。未编译、解析、测试、运行或发布；历史证据的当前源码复核限制及整体未完成状态保留。

## 最新批次：颜色底栏约束与纯值方法复用

- `0x1003e0820`：补回颜色底栏的独立容器，内部 stack 上、下、左等于容器，右侧小于等于容器，真实初始化路径激活，避免被外层 footer 强制铺满。原方法本体还有 actor 执行器检查，仍记 partial，不算整个函数完成。
- `0x100225cfc`：原纯方法 context raw0 返回 copy(1)，其他返回 move(16)，不使用 session；真实拖拽方法与 SDK 枚举全部对应，直接复用。ObjC actor 桥另保 partial。新增完整确认1。
- `0x100206ecc`：原亮度判断后返回黑色或白色，实际颜色预览赋色已满足全部值分支，复用现有表达式。新增完整确认1。
- `0x10031bcdc`：普通文本逐项投影已有实现，但原实体读取/解码边界未闭合，继续 partial。文件 footer 构造、VM读取及弱回调也不因值格式已实现而升级。

当前台账 **1,607 / 81,123 = 1.9809%**。本轮只做源码修改与人工静态对照，未编译、parse、运行、测试、安装、提交或发布；历史完整标记的源码证据过期限制仍保留，整体尚未完成。

## 最新批次：集合重复选中、链接必需值与透明度判断

- `0x100228c78`：将“现选区恰为目标单元素”的返回提前到 manager、Published、anchor、视觉和预览更新之前，删除旧的仅抑制预览判断。原滚动完成/失败及弱委托回调链未闭合，仍 partial。
- `0x1003bf65c`：链接 getter 改为返回非可选 URL，canonical 元数据缺失、损坏或非链接时恢复原失败分支，移除静默空 UI 适配；真实观察、编辑和打开按钮使用同一 getter，不修改持久数据。新增完整确认1，外围 VM/Entity/观察生命周期仍单列。
- `0x100206f0c`：成功原函数仅读取 alphaComponent 并与1严格比较；现紧凑文本背景的实际消费者已完整具备，复用现有表达式，新增完整确认1，不重复包装。

当前台账 **1,609 / 81,123 = 1.9834%**。详细逐函数边界见 `reports/function-migration/selection-link-getter-alpha-static.json`。本轮未编译、parse、运行、测试、安装、提交或发布；历史完整标记的当前源码证据过期限制保留，整体尚未完成。

集合下一段静态证据：`0x10022c9c4`（part-0190.c:229）对相交项目启动滚动时不传 completion，随后立即回调 true；离屏项目将 completion 交自定义动画。`0x100229130`→`0x100228e1c` 只在成功且弱 owner/delegate 仍存在时调用委托。不能把原异步失败链改成同步蜂鸣。待续入口为 `0x100229d4c`（part-0188.c:2835）→`0x10020b948`（part-0173.c:1705）→`0x1001f4d94`（part-0162.c:754）/`0x1001f6900`（part-0163.c:441），需继续恢复动画替换、取消与完成的 Bool 生产条件；本轮未猜写、未新增完整计数。

## 最新批次：文本观察基线、事务偏好与建议窗口定位

- 文本预览按 `0x1003c04f0` 将模型刷新与显示刷新拆开：有效记录在编辑中也更新原文/归一化编辑基线，编辑输入不被覆盖，不额外计算 canCommit；删除记录策略和原观察模型仍 partial。
- `0x1003eb8cc`：弱 owner 无效无操作；编辑时跳过两显示调用；非编辑时依次调用 `f3eb330`、`f3eb4a8`。实际观察路径已满足完整 callback，新增确认1。`0x1003ec3e0` 纯尾转发同 callback，复用实际源码，新增确认1。不升级观察父方法。
- `0x100322504` 消费链：采集预览生成移入现有 mutate，在最新磁盘状态合并后使用 state.preferences 的格式/QuickLook选择，已有 rawPreview 不重生，checksum/来源关系/owner/查重顺序保持；原多case/异步/Config与CoreData父仍 partial。
- `0x10005ad00`：建议窗口先按 fittingWidth 设置宽度、布局后读取高度；无父窗口或无对应屏幕只 return，删除额外 dismiss/escape 及 height>0 取消分支。原 anchor/通用窗口/actor等边界仍 partial。

当前台账 **1,611 / 81,123 = 1.9859%**，本轮新增完整确认2。详细证据见 `reports/function-migration/text-baseline-capture-preferences-static.json`。仅源码迁移与人工静态对照，未编译、parse、运行、测试、安装、提交或发布。历史完整标记证据过期限制保留，整体未完成。

集合动画本轮续追：原同 key 动画替换先移除旧项并回调 false；tick 按快照处理，完成先回调 true 再移除。`0x1001f8a84` 的求解含最多7次 Newton 更新、误差阈值提前返回、导数绝对值低于1e-6转二分及0/1边界。原显示链从 CVDisplayLink 线程取得 CACurrentMediaTime 后弱捕获派往 MainActor。下一项具体未闭证据是 `0x100229d4c` 传入动画结构的 from/startTime/duration 浮点布局，需要读原 arm64 指令确认；未猜写 duration，未引入只处理可见项目的临时 Bool API，本轮对此未新增源码或完整计数。

## 最新批次：物理导航键、真实滚动动画与完整预览 Pin 外观

- `0x100219df4`、`0x100219ddc`：补入原13类物理键码分类和NSEvent.keyCode转发，真实建议键盘处理使用同入口，不按字符/修饰键另猜。新增完整确认2。
- 建议导航按原算法直接写索引、更新选中/reveal，不再被独立Row.isEnabled拦截；确认键保原越上界只消费/负索引失败分支。原列表/actor及reveal几何父仍partial。
- 新增真实集合滚动动画消费者：普通选区定位不再仅直接改clip.bounds；采用原elapsed时长与六系数缓动、CVDisplayLink时钟、按key取消替换false、tick快照完成true后移除、空队列停钟。预览锚点仍以非动画立即定位。参数布局和epsilon由原arm指令确认；没有用NSAnimationContext或Timer替代。
- `0x1001f8a84`、`0x1001f8858`：拆出通用六系数值类型，独立parameter返回t，再计算Y；保任意系数/x/epsilon、最多7次Newton、导数门槛、边界、unordered及二分分支。真实滚动消费通用求解器，新增完整确认2。未把固定scroll特化冒称原全部泛型Animator。
- `0x100011e00` 的真实Pin外观改为显式owner/rawType2判filled，合法canonical pinboard属性映射原8色，否则无tint；分组发布使用传入新数组，避免willSet读旧值。不按membershipSet/legacyHEX挑色，菜单和持久数据未改。完整Header仍partial。

当前台账 **1,615 / 81,123 = 1.9908%**，本轮新增完整确认4。详细证据见 `reports/function-migration/navigation-key-scroll-animation-preview-pin-static.json`。泛型动画协议、集合完成委托/离屏回调与边界beep尚未全部整合。只做源码迁移及人工静态对照，未编译、parse、运行、测试、安装、提交或发布；历史完整标记证据过期限制保留，整体未完成。

## 最新批次：选区完成回调、建议列表滚动与预览快捷键

- 集合选择接上真实reveal完成链：相交立即成功，离屏等待动画Bool，取消不触发弱委托；越界请求保留选区后仍reveal最后有序项，按完成时requestedIndex及真实可见cell解析，失败beep，成功更新已有预览。原最终DI发布/Popover生命周期与可变delegate对象域仍partial。
- `0x100030134`：建议键盘定位改为读取本列表选区，按第一行高度扩展目标上下留白，补nil/越上界不操作及负索引失败分支。新增完整确认1。
- `0x10002fe24`：下箭头滚动步长改为第一行高度；恢复原只限制最大位置、可选document与clip reflect调用顺序。读原arm确认首行及origin来源，不再按当前选中行或统一双向clamp。新增完整确认1。上箭头值分支同时补齐，外层弱对象桥仍partial。
- `0x1003245fc`：补入完整Stored属性双case投影，pinboard色码缺省0，其余clipboard容量缺省30，保显式0/负容量/UInt64；现颜色读取真实消费。新增完整确认1。
- `0x10007bbe8`：完整预览键盘分派补CmdR重命名、Esc先取消标题；CmdE/Esc也改为原规范化raw签名，删除额外Editable入口guard。分派顺序、编辑状态、动作及返回值完整；其余交super。新增完整确认1，原ObjC actor桥和具体动作父不升级。

当前台账 **1,619 / 81,123 = 1.9957%**，本轮新增完整确认4。逐函数证据见 `reports/function-migration/selection-completion-suggestions-scroll-preview-keys-static.json`。仅源码迁移与人工静态对照；未编译、parse、运行、测试、安装、提交或发布。历史完整标记证据过期限制保留，整体尚未完成。

## 最新批次：属性Stored复用、关闭所有权与选择入口

- 属性Stored相邻六方法 `0x100324388`、`0x1003247b8`、`0x10032469c`、`0x1003244dc`、`0x1003245a8`、`0x1003245e8`：读取成功原体后，复用现三字段Attributes合成可选编码/解码、精确键解析/字符串及协议转发。字段顺序、missing/null、present坏类型整记录失败和错误传播完整，实际颜色读写/分组创建更新消费；新增完整确认6。不升级描述、witness或实体父。
- `0x10007a830`：关闭回调仅weak预览View，存活后从该View取标题取消，再可选关闭window；不再分别weak header/view引入不同释放域。`0x10007c954`纯转发复用，新增完整确认2。
- `0x10002e80c`：建议选区变更仅先清旧行、再选新行，保持相同索引false→true和越界失败；替换rows先清原选区再移除旧views，去掉额外enabled样式条件。实际select调用完整变化方法，新增完整确认1。列表更新/构造/actor父仍partial。
- 集合首尾导航按原不动画，单步保动画，参数贯穿state/controller/native。双击改为专用singleton/anchor/primary与视觉路径，跳过普通reveal/预览/beep链，保直接粘贴及实际event纯文本配置，并抑制后续primary观察重复滚动。原完整keyboard/mouse事件、manager额外字段/DI父仍partial。

当前台账 **1,628 / 81,123 = 2.0068%**，本轮新增完整确认9。详细证据见 `reports/function-migration/attributes-codable-preview-close-selection-static.json`。只做源码迁移及人工静态对照，未编译、parse、运行、测试、安装、提交或发布；历史完整标记证据过期限制保留，整体尚未完成。

## 最新批次：建议行惰性对象与延迟输入/标题所有权

- `0x10000ed50`、`0x10000ee38`、`0x10000eedc`：补回显式可选缓存与真实getter，首次创建并配置标题、图标和横向stack，后续返回同一对象；原nil图标隐藏、行数/字体、alignment/spacing完整，构造/布局/测量/样式均消费同缓存。新增完整确认3。18x18与insets仍属于约束父，不错误并入getter。
- 建议行选中状态按变化检查置needsLayout，布局先super再刷新当前样式，构造末保初始刷新；原actor报告与Invalidating包装父仍partial。
- 标题提交增加weak预览View门控并保持其同步转发期间存活，避免Header被单独保留后仍写Store；state/VM强持有和原rename父未闭合，`0x10007a8c8`及尾转`0x10007c95c`仍partial。
- 集合命中从固定几何反算改为真实visible cell.frame字典遍历，不排序；延迟选择保原捕获数字索引，删除取当前item/提前越界过滤/抢焦点路径。当前identity护栏、弱state及原manager/DI/actor父仍partial。
- 相邻属性键转发 `0x100324534` 只保候选，未因有限解析值相同而升级未知原协议槽身份。

当前台账 **1,631 / 81,123 = 2.0105%**，本轮新增完整确认3。逐函数证据见 `reports/function-migration/suggestion-lazy-accessors-delayed-input-title-owner-static.json`。仅源码迁移与人工静态对照，未编译、parse、运行、测试、安装、提交或发布；历史完整标记证据过期限制保留，整体尚未完成。

## 最新批次：覆盖色getter、编辑按钮回调与tracking顺序

- `0x100311f7c`：独立可选NSColor覆盖查询接入真实rawColor，精确bundleID命中、miss nil、signed负码失败、既有解码与回退均保留；47项表不复制改值，新增完整确认1。表写槽初始化/原工厂父不升级。
- `0x1000124f4`、`0x100013a94`：完整弱Header/onEdit可选回调及Void尾转可直接复用现真实Edit按钮；成功链不消费伪码的残留code指针返回，不主张机器ABI。新增完整确认2。
- `0x10000f828`：tracking更新先super、移旧、按bounds/options0x81创建、先写可选槽再非nil添加，真实建议行顺序已补，新增完整确认1。原actor桥仍partial。
- 建议行entered/exited/down删除独立enabled门控，hover数字索引不再被提前吞掉；原统一字段helper/必备action模型/actor父仍partial。
- 右键打开菜单前改专用无focus选择入口：已选保多选，未选normal/animated=true，不再makeFirstResponder；仅改monitor那一处消费者，不改菜单内容或其它点击。完整右键父继续partial。

当前台账 **1,635 / 81,123 = 2.0155%**，本轮新增完整确认4。详细证据见 `reports/function-migration/tracking-edit-callback-source-override-static.json`。仅源码迁移与人工静态对照，未编译、parse、运行、测试、安装、提交或发布；历史完整标记证据过期限制保留，整体尚未完成。

## 最新批次：建议标题片段、通用位图与颜色调整

- `0x100010984`：新增真实建议行标题组装方法；query缺失/空/无匹配返回primary色不可变富文本，有匹配则按原顺序追加secondary间隔、primary匹配和secondary尾部，返回可变富文本。布局样式实际消费，新增完整确认1。
- `0x1003c7c4c`：固定128私有位图路径恢复任意目标宽高接口；真实取色仍传128，保原表示选择、两次size读取、Int/width*4失败、bitmap/contextnil及绘制状态顺序，新增完整确认1。
- `0x1003c7f84`：原饱和度/亮度调整恢复独立任意NSColor方法并由实际winner调用，保读取顺序与calibratedHSB，新增完整确认1。以上两方法重新读原ARM比较/选择条件，IEEE/NaN分支以机器指令为准，没有照搬Ghidra的反向关系误译。
- 图片commit移除原方法没有的canCommit额外拦截，保按钮启用、image/state可选及既有finish/error策略，整父仍partial。
- 鼠标按下恢复先visible-hit/点击次数，再有效Ctrl转自身rightMouseDown的顺序，空白/多击交super；完整事件父仍partial。

当前台账 **1,638 / 81,123 = 2.0192%**，本轮新增完整确认3。详细证据见 `reports/function-migration/suggestion-attributed-title-source-image-parameters-static.json`。仅源码迁移、人工静态对照及读取原二进制指令，未编译、parse、运行产品、测试、安装、提交或发布；历史完整标记证据过期限制保留，整体尚未完成。

## 最新批次：建议箭头重复计时、滚轮返回边界与Data复用

- 建议滚动箭头恢复原inside/mouseMoved门控：可继续滚动且无timer时启动75ms重复owned timer，移出释放wrapper停止；mouseenter不再直接滚一步。tracking改回bounds/options0x83，图标12pt medium、12x12及tint/fallback补入。原完整Scroller布局/可选回调/actor父仍partial。
- `0x100385984`、`0x100385ac4`、`0x100385acc`：新增真实使用的任意interval/repeats/action timer wrapper、invalidate及deinit失效，不再只覆盖Pause单次false路径。新增完整确认3；机器分配/释放ABI不升级。
- `0x10004b544`：完整tracking纯业务存储/添加顺序恢复，新增完整确认1；actor桥另列partial。
- `0x100236978`、`0x100236910`：滚轮转换恢复独立optional方法；原arm确认无需转换/CG缺失时返回原event，只有NSEvent重建可nil，上层helper??event再一次super。新增完整确认2，不copy/clamp。
- `0x10031b830`：合法Data长度/有效字节比较由真实来源PNG更新链复用系统Data.==；成功原完整体与本机Foundation公开inlinable源码对应，新增完整确认1。非法内存表示、ABI及底层unsafe helper未升级。
- 图片begin移除额外旋转重置、Undo清空和footer刷新，保已显示编辑配置，原zoom编辑调用及取消/提交重置保持；本地focus/事件父仍partial。

当前台账 **1,645 / 81,123 = 2.0278%**，本轮新增完整确认7。逐函数证据见 `reports/function-migration/suggestion-hover-timer-wheel-data-reuse-static.json`。仅源码迁移与人工静态对照，未编译、parse、运行产品、测试、安装、提交或发布；历史完整标记证据过期限制保留，整体尚未完成。

## 最新批次：滚动渐隐、拖拽边缘轨迹与Stored decoder

- `0x10004a994`：建议滚动补原18pt边缘渐隐mask；无layer不操作、两端不可滚动清mask、任意低/高端组合建立白body与两种方向渐变。原ARM确认nonnull分支只有一次setMask，不照搬Ghidra重复调用误译。真实bounds/layout更新消费，新增完整确认1。渐变helper已接，逐颜色actor诊断仍partial。
- `0x100226764`：恢复bounds读取轨迹与原LS/HI门槛、unordered回0、统一最后乘sign的算术顺序，实际draggingUpdated消费不变，不另clamp/转坐标。新增完整确认1，原拖拽父仍partial。
- `0x100316490`：完整原ARM补回Ghidra删去的异常分支，现有PL短路→JSON回退→双失败nil已完整满足；13optional字段及五类实际消费已闭，本地址无Config/DI/Entity访问。复用已有源码，新增完整确认1；动态Config encoder继续partial。
- 左右旋转删除额外isEditing门控，保quarter循环、可选图像、footer与反向Undo现链；原dictionary key、VM任务/弱Undo生命周期仍partial，不以简单布尔替代原key存在性。

当前台账 **1,648 / 81,123 = 2.0315%**，本轮新增完整确认3。逐函数证据见 `reports/function-migration/suggestion-mask-drag-edge-decoder-static.json`。只做源码迁移、人工静态对照和原指令读取，未编译、parse、运行产品、测试、安装、提交或发布；历史完整标记证据过期限制保留，整体尚未完成。
