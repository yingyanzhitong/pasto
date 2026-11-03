# 离线迁移第十二轮：索引历史时间和列表入口身份

2026-10-29。只做已有反编译代码/原二进制的静态读取、源码修正及 Python 源码检查。未编译、构建、安装、执行 Spotlight 查询、运行应用或原函数、联网、修改真实历史、提交或推送。

## 索引日期修复

Pasto 的索引 Entry 原把 `updatedAt` 写入 `contentModificationDate`。原 `0x100371998` 快照构造却读取实体的 **timestamp**，保留可选 Date，然后经 `0x100375200 → 0x1002e3ce8` 写入属性。使用编辑时间会使文本/标题修改影响日期筛选；给分组独有项目填一个创建日期，也不等同原 nil timestamp。

现 Entry.modified 改为 **Date?**，生产输入为 `item.isInHistory ? item.createdAt : nil`，属性 builder 原样接收这个可选值。该投影复用现有历史标记与时间兼容字段，不重写或迁移用户数据；编辑时间、当前时间及强制创建日期都不作兜底。查询表达式与上轮列表时间排序直接复用。

证据不止是字段名称：

- 从原 nominal descriptor `0x100cad06c` 确认 SearchableItemEntity 的九个字段，第六个索引为 timestamp；偏移向量位置为两个 pointer word，第六项的位置正是 getter 读取的 metadata+0x28。
- timestamp 的 symbolic typeref 带 Optional 后缀 Sg，其间接引用解析到真实 dyld import `_$s10Foundation4DateVMn`，确认是 Optional<Date>。
- 真实 conformance `0x100c43568` 指向该类型和 witness 表 `0x100ecd440`；遍历 dyld 声明页面链确实到达 `+0x18` 槽 `0x100ecd458 → 0x100375200`，不是读取附近指针猜 getter。
- 原 builder 在 `0x1002e3f74` 从 witness+0x18 取 getter；快照在 `0x100371ac4` 构造 timestamp 小串再做 KVC。原 nil/动态转换失败路径保留可选空值。

字段记录、原指令、import、链可达证明及逐函数/源码摘要均在 [机器记录](offline-migration-p0-round12.json)。自有日期/flag 模型仍是兼容投影，未宣称原数据库对象布局相同或真实日期查询已经运行通过。

## 修正上一轮的入口归类

上一轮把 `0x10007d9c8` 概括为“用户选组时清 query”过宽。本轮追到真实绑定：MainView 初始化把 `ItemCollectionView.onSelectList` 绑定到 `0x100037ec0 → 0x100036860 → 0x10007d9c8`。原 `0x10006c338` 会先保存 pendingFocus 的列表/项目标识和横向偏移，再走该回调，属于**卡片定位到列表**路径。它确实先清 query 再选列表，但完整恢复焦点消费者在 Pasto 仍未闭合。

普通 `TabBarCell.onSelect` 的 `0x100099adc` 直接取 identifier 调 `0x100039c50(force1)`，不走该清搜索入口。关闭后的 `0x1000217a8 / 0x100021908` 也只改变 history 路由和 timer，不清 query。当前 chooseBoard 保持普通标签/程序路由的已有子行为，没有因错误归类把所有入口机械改为清空搜索。完整强制重选 Published 时序、卡片 pendingFocus 及工具栏的全部路径继续待迁移。

## 检查、边界与进度

**127 / 127** 项 Python 源码、台账及静态证据检查通过，本轮新增 **10** 项。覆盖原 timestamp 立即数、字段/可选类型、conformance/真实 dyld 槽、getter/attribute 一致性、nil/date 输入及错误投影反例、历史与列表时间一致性、普通标签/卡片定位/关闭路由的分工。它们不是 Swift 编译、实际日期查询或焦点交互回归。

本轮核对 **18 个原地址**，其中 **14 个**首次进入本目标当前复核并集；新增 **1 条 partial** 映射，扩展原快照父的已有 partial，partial 合计 **440**，新增完整迁移 **0**。十二轮去重累计 **356 / 81,123 = 0.4388%**。历史完整标记仍为 **1,648 / 81,123 = 2.0315%**，含过期证据，不代表当前 Pasto 全量完成度。

索引重建/可选 app-device-pinboard、多分组投影、内容/图片闭包、Task/DI/FRC 生命周期，以及卡片定位的完整 pendingFocus/新列表恢复仍有差异。目标保持进行中，继续按真实功能消费者核对，未完成项不以阶段结束替代验收。
