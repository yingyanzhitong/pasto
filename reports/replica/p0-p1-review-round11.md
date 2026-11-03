# P0 与 P1 源码复查：第十一轮

2026-10-30。继续只读对照离线P0/P1源码及原反编译证据，不修改生产代码、迁移台账或版本；不编译、构建、安装、执行应用、联网或提交。

| 当前暂定清单 | 有有限比较结论 / 分母 | 比例 | 未闭合 |
| --- | ---: | ---: | ---: |
| P0 | 243 / 243 | 100.00% | 0 |
| P1 新增独立地址 | 245 / 246 | 99.59% | 1 |
| P0 + P1 去重合计 | 488 / 489 | 99.80% | 1 |

本轮重审此前4项，新增2项局部一致和1项差异结论。当前共365项局部一致、115项差异、8项用户适配；7个共享地址只计一次。差异记录包含父子调用链共享根因，115不是独立缺陷数。

**以上是当前暂定清单的比较结论比例，不是迁移完成率。** 原版完整P0/P1分类边界仍未证明完整；已发现的差异本轮未修复，所有记录继续保持`full_function_migration_verified=false`。

## 新增有限结论

- `07e088`：`07e194`将它作为真实Combine `compactMap`回调。对非nil且有效的History/Pinboard列表，原构造相应列表上下文，当前`chooseBoard→visibleItems→NativeCardCollection`也路由到相应内容，有限一致。原nil输入被`compactMap`丢弃，不能把它等同当前`pinboardID=nil`表示History；此输入映射及完整发布时序仍未证明。
- `052734`：metadata表明它是Paste模块的`ItemCollectionViewModel`，六个派生字段是四个依赖和两个偏好，不是selection/list字段。两个偏好KeyPath分别经`0542b8→070eb8`及`0542bc→091254`，缺省Bool为false、true；当前`alwaysPastePlainText=false`、`pasteToActiveApp=true`及实际粘贴消费者对应，窄合同一致。不覆盖四个依赖对象身份、已有偏好迁移、更新通知顺序或整个构造器。
- `2e00a0`：接通真实候选来源后确认差异。原`SearchService.index`为`SpotlightIndex`，其`suggestionDataSource`由AppDelegate注入`CoreDataSuggestionDataSource`；DI factory使用`viewContext`。四个witness槽分别到应用、类型、设备、分组方法。应用/设备/分组候选实际走此前已审的数据库fetch路径，当前FilterBrowser读取store内存快照，读取阶段和fetch错误输入域不同。该父记录复用`30e070`、`30ed6c`、`30e6bc`的根因，不重复宣称新独立缺陷。

## 新证据与纠正

`c27110`的KeyPath getter相对槽`c27138→07d73c→2fd914`绑定具体数据源注册，factory `2fd99c`将`viewContext`存入数据源。conformance `c40a90`及witness `eca2b8`再把四个方法连至`30e070`、`30f3e0`、`30ed6c`、`30e6bc`，不再停留于未解析的resolver。

`SearchService`、`SpotlightIndex`、`CoreDataSuggestionDataSource`是不同对象。`2e19c8`初始化SpotlightIndex；`2d6cf4`属于带r的SpotlightIndexer actor。DI源文件的行号参数也不是注册key。本轮调查草稿中这些混淆已纠正，不作为差异依据。

本轮父候选差异依据数据库与快照读取/错误范围；不把当前legacy `rawType=nil`兼容解释成原生`rawType=0`而虚构同输入反例，不宣称全部候选成员或后续交互已经一一对应。

## 唯一未闭合地址

`0f733c`的独立String setter仍只有当前声明，没有已证生产消费者。补查原二进制ADR及12条指令窗口内ADRP/ADD引用也无命中；这只是有界负检索，不能证明原方法不可达或没有内联消费。其机器码尾跳`objc_release`，Ghidra的`return 0`仍不足以确定返回ABI。保持未闭合，不为达到100%而计入。

## 检查

230项Python源码/静态证据检查通过，0失败、0错误，包括原片段及当前引用摘要、metadata字段、KeyPath相对指针、witness、SDK binding和不变历史结论。检查不编译或执行原版/Pasto，不是应用功能回归。

218个生产源码文件、迁移台账和HEAD与本阶段基线一致。

- [逐地址结果](p0-p1-review-round11.json)
- [静态证据](p0-p1-review-round11-static-proof.json)
- [本轮检查](../../scripts/tests/test_p0_p1_review_round11.py)
- 日志：`.local/p0-review/p0-p1-round11-code-tests.log`。
