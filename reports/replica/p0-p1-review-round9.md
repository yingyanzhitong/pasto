# P0 与 P1 源码复查：第九轮

2026-10-30。继续只读复查离线 P0/P1，不修改应用功能，不编译、构建、安装、执行应用、联网、提交或发布。P2、联网协作及两个指定失败地址保持排除。

当前去重暂定清单中 **482 / 489 = 98.57%** 已形成明确的有限比较结论，本轮新增5项（2项局部一致、3项确认差异）。总分类为360项局部一致、114项确认差异、8项用户指定适配、7项未闭合。

| 范围 | 明确比较结论 | 比例 | 未闭合 |
| --- | ---: | ---: | ---: |
| P0 当前清单 | 243 / 243 | 100.00% | 0 |
| P1 新增独立地址 | 239 / 246 | 97.15% | 7 |
| 去重合计 | 482 / 489 | 98.57% | 7 |

这些百分比包含已经判明但未修复的差异，不是迁移完成率。清单保持provisional，原版全部P0/P1的分类边界尚未证明完整；全部记录仍为`full_function_migration_verified=false`。有限叶子结论不覆盖未证的父合同、完整错误或ABI。

## 已连接的真实消费者与差异

### 索引记录保留延迟读取，当前提前物化

`2faafc` 的元素类型不再仅凭C局部变量猜测。原`371e9c`指向`cad06c`的`SearchableItemEntity`；`d48900`字段记录确认为`id/type/title/content/app/imageData/timestamp/device/pinboard`。`ecd440`通过`c43568`和间接协议槽绑定到`SearchableItem`。

原桥将完整值及witness逐条复制到existential数组，保留content/imageData回调。实际builder在`2e3de8`读取witness的`+0x38` getter，`2e3df8`取回调，`2e3e0c`才调用它。非图片content经`3753f8→372440`在读取时创建新的CoreData context，`375480→3724f0`使用真实selector`existingObjectWithID:error:`读取实体data。

当前`liveEntries→Entry.init`提前生成`text:String`，builder之后直接使用`entry.text`。因此准备记录与构造SDK item之间若发生本地内容修改，两条链具有不同的读取阶段。这是已证的延迟回调保留/读取时点差异，不是仅因协议或结构名字不同而判差异；未执行并发复现，不宣称完整OCR或decoder错误已等价。与既有`371998`记录的生产者问题共源，不重复当作独立产品缺陷。

### 筛选动作中的公开状态与编辑器更新顺序

`2f7744` 的closure槽已用初始化和调用机器码对应到真实SearchBar回调：`+0x48→041bb8/0406ac`构造富文本，`+0x28→041ba8/040284`应用编辑器文本/选区，`+0x18→041ba0/0401ec`发布SearchBar query，`+0x38→041bb0/0403b0`更新建议。

限定FilterBrowser的mode=0路径：原先更新协调器内部query，然后构造文本、条件记录history、更新编辑器，之后才发布SearchBar的`Published query`；当前先由`applySearchInput`发布state，随后`SearchEditor.updateContents`渲染并记录history。确认公开通知与编辑器副作用的顺序不同，不声称最终文本、选区或视觉结果必不同。

另纠正调用者归因：flag=1来自`03ff40`的Published-query订阅；键入delegate走`040990→2f7370`，选区delegate走`040a24→2f7dd8`，它们不是这组slot或该函数的直接键入入口。

### 空历史的删除菜单入口

`021f00` 的原history分支先检查`rawType=1`及`325130`的isEmpty结果；只有非空才构建清空历史动作。ARM`0221f0`调用isEmpty，`0221f4`仅在返回false时转入菜单构造。当前history context menu始终包含“删除历史…”，没有相同显示门。确认这处离线条件差异；CloudKit/CloudSharing菜单仍按用户范围排除。

## 空搜索结果的发布链已补齐

`360808`发送的subject并非主列表`SearchVM?`，而是`SearchResultsCollection`中的实体序列provider可选值。本轮解析`c425d0`确认`SearchResultsCollection:ObservableCollection`，并用Mach-O段映射验证witness表文件位置。

`1ae768`把`1aeaa4`安装到eraser的`+0x40`；后者经witness`+0x30→355854→355874`读同一`owner+0x18` subject。`Map(355be0→355a98)`把nil映射为`Just(emptyArray,emptySet)`，再`switchToLatest→erase`交给CollectionView订阅；元素getter`3556e8`在nil时也返回空数组。**不是subject的nil原样传到视图。**

当前非空查询成功返回空ID集合时，`visibleItems`为空并交NativeCollectionHost。由此闭合“空结果显示空列表”的有限分支。`3bb540`搜索来源/普通列表来源分流职责也可对应；非空结果排序、缺项、初始状态和取消/持有生命周期仍未由这两条有限结论判等价。

## 剩余项与检查

剩余7项均在P1：`052734`、`06f29c`、`07e088`、`0f733c`、`2e00a0`、`3647d4`、`3b8bfc`。继续追构造器初始状态、列表缺失路由、拖放动态目标、候选全域及缓存/刷新生命周期。无消费者的setter声明不能计作完整迁移。

**215项Python源码/静态证据检查通过，0失败、0错误。** 检查包括逐函数原片段与当前引用、补充槽位证据、Mach-O文件段映射、两种协议及字段metadata、实际延迟调用、空结果Map链、公开回调次序和菜单门控。它们是源码及证据守卫，不是编译或应用回归。

218个生产源码文件、迁移台账与HEAD`050e6878a5a52f96fe33aa40f48bb8a056cd0f05`未变。目标继续进行。

- [逐地址报告](p0-p1-review-round9.json)
- [metadata、witness及ARM证据](p0-p1-review-round9-static-proof.json)
- [本轮源码检查](../../scripts/tests/test_p0_p1_review_round9.py)
- 测试日志：`.local/p0-review/p0-p1-round9-code-tests.log`。
