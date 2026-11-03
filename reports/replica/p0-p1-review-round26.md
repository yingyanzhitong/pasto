# P0 / P1 第二十六轮代码复查

2026-10-30。只读原片段、机器字节及源码检查。本轮补P0恢复输入和时间子合同，不扩清单、不修改应用功能；未编译、构建、安装、运行应用/框架、联网、提交、推送或发布。

| 当前暂定清单v5 | 结果 |
| --- | ---: |
| 明确有限比较结论 | **653 / 656（99.54%）** |
| 有限合同一致 | 500 |
| 已确认差异记录 | 144 |
| 用户指定适配 | 9 |
| 未闭合 | 3 |
| P0 | 265 / 266（99.62%） |
| P1新增独立地址 | 388 / 390（99.49%） |

比例不变。**两个子合同不是整函数完成；没有增加已闭合函数数量。** 原版全部优先级库存分类仍未证明，全部full_function_migration_verified为false；此比例不是迁移完成率。

## 1. 实际表示数据getter与本地生产路径

已从原机器字节绑定`31b218 → 2ffc68 → 31bc34 → 31b1bc`。真正属性消息stub为`c08760`，selector ref `f88de0`指向字符串`rawPasteboardItems`；不是系统NSPasteboardItem.data(forType:)。2ffc68承担同步ObjC异常捕获边界，原getter的数据值进入31aeec解码。

当前本地capture只在`capturedItems.count>1`时写`originalItemDataPayloadKey=31a8e8(capturedItems)`；本地originalPasteboardItems读此键并交31aeec。单项采集保存orderedTypes和Data字典，恢复时重建单项，不能声称所有采集都直接存相同编码blob。普通有效文本数组的本地生产/消费输入已绑定；旧31a8e8、31aeec和32362c有限比较记录继续作为各自叶合同证据，不外推整个当前恢复函数。

子审引用的CloudGraph建图/导出不是本轮离线恢复consumer，主审未采纳其源码引用作为函数闭合依据。本轮未运行或修改云功能。

## 2. 成功History图片的时间顺序

限定源项已在History、有效非nil timestamp、成功写板且对象稳定：原383df4准备图像文件名时读取旧timestamp；随后正常恢复事务确实经`37a144 → 37b620 → 37ade4 → 固定History repository witness+0x28 → 3614c0 → 361ec0`推进timestamp。

当前image prepare同样读取旧createdAt，writer之后recordRestoredItems更新createdAt并commit，ClipboardPersistence把它映射到Core Data timestamp。因此该有限时间合同一致。当前updatedAt额外字段没有当作原modifiedAt证明，非history/错误/清理/refresh等域未由此判等价。

**撤回子审草稿的“原正常恢复不更新时间”结论**：它只看37a144直接setter，漏掉实际事务closure。主审没有把该草稿加入canonical差异，差异数一直为144。初稿与独立修正文件均冻结保存，不改写历史来源。

payload子审正文又把image分支写成“返回原实体”，主审继续采用上轮ARM纠正：383dc0尾跳383df4，返回图像表示数组，不是原实体。其余原支线的类型和异常映射仍需继续核实。

## 3. 仍未完成与验证

383d90保留unclosed：文本数据输入和History图片时间两个子合同不足以证明全部image/其它类型、单项兼容表示、原实体与当前kind/payload及桥接异常的完整对应。P1 coder04430c及Swift setter0f733c仍待证。

**378项Python源码/静态检查通过，0失败、0错误。** 沿用370项并新增8项，检查16个原机器块、真实getter selector/BL、条件写blob与单项fallback、原事务时间链、拒绝误报和CloudGraph消费外推，以及生产基线。首次新增检查断言了一段放在另一报告字段的说明文字，已改查实际contract字段后全量重跑通过；应用代码没有修改。

218个生产文件、function-map、版本和HEAD保持不变。当前[144条差异/131保守组清单](p0-p1-difference-backlog-v2.md)仍适用，未修复应用功能差异。下一步继续P0图像/类型上游输入与异常映射，随后回P1两个入口。

上一目标轮为progress：批量纳入7项并排除统计。当前轮补出真实getter、本地条件存储与完整成功事务时间链，撤回不成立的候选差异，属于证据进展；目标未完成，保持进行中。

[逐地址记录](p0-p1-review-round26.json) · [静态证据](p0-p1-review-round26-static-proof.json) · [固定清单v5](p0-p1-review-scope-v5.json)
