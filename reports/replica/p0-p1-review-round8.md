# P0 与 P1 源码复查：第八轮

2026-10-30。只读核对离线 P0/P1，未修改应用功能，未编译、构建、安装、执行应用、联网、提交或发布。P2、联网协作与两个指定失败地址排除。

当前去重暂定清单有 **477 / 489 = 97.55%** 形成明确比较结论，本轮新增4项。分类为358项局部合同一致、111项确认差异、8项用户指定适配、12项未闭合。

| 范围 | 明确比较结论 | 比例 | 未闭合 |
| --- | ---: | ---: | ---: |
| P0 当前清单 | 243 / 243 | 100.00% | 0 |
| P1 新增独立地址 | 234 / 246 | 95.12% | 12 |
| 去重合计 | 477 / 489 | 97.55% | 12 |

**P0的100%只表示当前243项都有比较结论，其中包含差异，不是迁移完成率。** 有限一致不代表完整父合同或ABI一致，差异判明不等于修复。原版全部P0/P1的分类边界仍未闭合；清单保持provisional，全部记录仍为`full_function_migration_verified=false`。

## P0 最后一项：查重未命中时的标识差异

`3611b0` 的未知归档身份此前未闭合。本轮证明了一个不依赖它的普通文本首次采集分支：空库查重返回`x0=nil`，`3611ec`跳至`36120c`，再将`x1`置零、原内容数组交`x2`，`361218`调用`360d9c`。这明确传入了nil identifier。

`360d9c` 的nil分支计算内容校验和，将返回String保存在`x23/x26`，再经`360ef4`写入identifier。普通文本走UTF-8 MD5，`323158/32315c`指令装入的格式小字符串确为`%02x`。当前采集构造`ClipboardItem`未传id，采用默认`UUID()`；未命中后保留该UUID，持久与索引标识使用`id.uuidString`。

空库首次复制合成文本`pasto-p0-fresh-item`时，原identifier由源码推导为`d84e1a0775d13912d49cd129e7e579ba`，当前为UUID字符串，规则和值域明确不同。**这是静态反例推导，没有执行原应用、Swift或真实用户数据。** 它与既有`360d9c`共用一个创建标识问题，不重复计算为独立产品缺陷；未知归档、全部错误和生命周期仍未宣称等价。

## 其他新增结论

- `2f2690`只保存目标IDs/上下文并调度后续工作，当前也将请求交异步索引任务；有限捕获/交接合同可对应，不包括namespace筛选、合并顺序或完整worker。
- `2f26a8`的内层descriptor`100c3ec00`相对字段`8c506bff`指向`1002f3c8c`，经`2f2ca8→2ea770(ids,1)`接入已证force=1写入链。当前builder缺原`isUpdate` setter，确认共享的子合同差异。`100c3ec08`指向`2eb754`完成回调，不能混作worker。
- `368560`先插入实体、设置identifier/name、取得永久ID，再编码并设置属性/类型；当前先编码属性、再构造UUID分组及追加state，最后commit。仅确认方法内操作及错误点前的时序不同，不推断外部CoreData框架最终rollback行为。

原`021f00`的CloudKit/CloudSharing回调虽已追清，但属于用户排除的联网协作能力，不用当前缺这些菜单增加离线差异。离线rename/delete/color等完整门控仍未逐项闭合。

结果subject已确认为`EntitySequenceProvider?`，没有把它错当主列表`SearchVM?`。当前`ReplicaSearchIndex→identifiers→visibleItems→collection host`链已列，但原provider、VM和subscriber完整对应仍缺证据，不能据某处nil就断言回退历史列表。

剩余12项均在P1：`021f00`、`052734`、`06f29c`、`07e088`、`0f733c`、`2e00a0`、`2f7744`、`2faafc`、`360808`、`3647d4`、`3b8bfc`、`3bb540`。继续优先追结果订阅、输入回调和拖放位置门控；无消费者的声明不计迁移完成。

## 检查

**208项Python源码与静态证据检查通过，0失败、0错误。** 新检查覆盖miss时nil参数、校验和String寄存器、十六进制格式、任务descriptor、联网分支排除及创建顺序。它们是源码/证据守卫，不是应用回归或原二进制执行结果。

218个生产源码文件、迁移台账和HEAD`050e6878a5a52f96fe33aa40f48bb8a056cd0f05`未变。目标仍进行中。

- [逐地址记录](p0-p1-review-round8.json)
- [ARM与静态反例](p0-p1-review-round8-static-proof.json)
- [源码检查](../../scripts/tests/test_p0_p1_review_round8.py)
- 测试日志：`.local/p0-review/p0-p1-round8-code-tests.log`。
