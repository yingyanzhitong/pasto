# P0 / P1 第二十五轮代码复查

2026-10-30。仅只读代码比较、原机器字节/元数据和无需编译的Python源码检查。应用源码218文件、function-map、版本和HEAD保持本阶段基线；未编译、构建、安装、运行应用/框架、联网、提交、推送或发布。

| 当前暂定清单 v5 | 结果 |
| --- | ---: |
| 明确有限比较结论 | **653 / 656（99.54%）** |
| 有限合同一致 | 500 |
| 明确差异记录 | 144 |
| 用户指定适配 | 9 |
| 未闭合 | 3 |
| P0 | 265 / 266（99.62%） |
| P1新增独立地址 | 388 / 390（99.49%） |

本轮新增7个业务地址：6个P1有限合同一致，1个P0保留待证；原649条记录与状态逐项保留。9个共享地址只计一次。**比例下降来自分母扩充，不是功能回退；比较覆盖率包含未修差异，不是迁移完成率。** 原版全部优先级分类仍未证明，full_function_migration_verified全部false。

## 批量富文本复查

覆盖OriginalPreviewTextTraits.swift内10个当前有真实消费者、此前在清单/边界外的地址，另核其原任务描述符和完整原初始化片段。

| 新增业务地址 | 有限比较结论 |
| --- | --- |
| `207db8` | 普通属性字典投影为trait集合；font的bold/italic位、underline/strike的Int==1判断可对应 |
| `208290` | 同一有效Trait集合中的成员判断；当前真实编辑按钮及toggle消费结果 |
| `207b54` | 普通有效非空选区取所有run trait并集；空选区/越界回退typingAttributes |
| `2083e4` | 指定run先删除源属性键，再加入转换结果；返回值和正常操作顺序一致 |
| `213fe8` | MainActor内普通稳定输入的trait发布及结束flag值可对应；不把原异步续体ABI当同步Bool返回 |
| `214704` | 稳定owner且回调不销毁/重入的域中，traits先于content发布；不据两次weak读取证明完整ARC/任务生命周期等价 |

`2080e0`并集、`208024`组合、`2085e0`回调透传及`21453c`异步投递保留为支持方法，不重复扩分母。`207648`、`2072a0`、`213780`已在旧范围，未重复计数。

实际原异步路径绑定为：

- TextEditor构造`213978`安装KVO，经回调及`213e54`使用异步描述符`c36708`→`216048`→`213f58`→task_switch至`213fe8`。
- storage回调`21453c`使用描述符`c36650`→`215e18`→`214674`→task_switch至`214704`。

原`213fe8`把结束flag写入async context再续调，当前同步helper返回Bool仅对应其普通值处理，不是相同ABI的证明。原`214704`弱持有的是TextEditor owner，当前桥弱持有NSTextView，整体对象结构/回调销毁竞态未据此判等价。当前adapter/document的两类发布消费者均绑定真实源码字面。

源码注释的`213cb0`并非独立导出函数：它位于真实`213978`完整函数内部，是KVO选项设为1的指令，不另计函数。

## 统计回调范围已闭合

上轮待定`3b9490`现排除为纯统计上报，未计入离线业务缺失或迁移分母。证据不是名称猜测：

1. 类metadata`fc26f8`的descriptor指向ItemCollectionViewModel，方法槽`fc2878`直接指向`3b9490`。
2. 真实field-offset vector将analytics映射到对象`+0x38`，context映射到`+0x40`；字段名及类型记录均从field metadata解析。
3. analytics的符号类型编码明确为Injected<PasteAnalytics.Analytics>，两段间接context descriptor分别解析到PasteDI.Injected与PasteAnalytics.Analytics。
4. 原机器指令`3b96c0`读取`owner+0x38`，保存后在`3b9744`恢复为Injected getter receiver；最终`3b9760`从Analytics witness `+0x20`取回调，`3b977c`交付type/day/mode。

**纠正上轮表述：`+0x40`是context筛选条件，不是统计或复制内容回调接收者；实际统计依赖来自`+0x38`。** 不为模仿原版而迁入已排除的统计上报。

## 新增P0待证与子报告更正

`383d90`属于真实恢复父`38222c`的rawType分派/数据解码，纳入P0并保持unclosed，不能因为尚未得到结论就放在分母外。

原路径将业务实体rawType规范后，值1直接tail-call `383df4`，返回图像表示准备的数组结果；其他值读取实体data交`31b218`解码返回数组。当前真正入口先ordinaryRestoreRepresentations解码，再按非plain且kind=image调用imageRestore.prepare；上游原实体/data与当前kind/payload及错误域的逐值映射仍缺。

子报告有两处主审纠正：原输入不是系统NSPasteboardItem；伪代码的`return param_1`不代表原实体原样返回，`383dc0`的ARM尾跳已证明结果来自图像helper。子报告仍沿用“3614c0未纳范围”的旧文字也不采纳：它早已在清单且确认差异，原记录保持不变。`368080`继续只作既有History lookup支持。

## 验证与下一步

**370项Python源码/静态检查通过，0失败、0错误。** 继承上轮360项，新增10项，覆盖范围不丢旧记录、unknown照实纳入、原片段/当前字面、38个机器块、analytics字段/协议/调用、trait顺序、原异步描述符及图像尾跳。初次测试中一个原片段路径写成相邻part文件，改为读取权威function-index后全量重跑通过；这是检查脚本路径错误，没有修改应用代码。

当前三项unknown为P0 `383d90`、P1 `04430c` coder输入和`0f733c` Swift setter绑定。下一步按P0优先补恢复上游值映射，再回P1两入口。旧[144差异/131组清单](p0-p1-difference-backlog-v2.md)仍适用，本轮未修任何应用功能差异。

上一目标轮为progress：补入三个P1业务叶合同并纠正范围。本轮也是progress：批量补核六个trait合同、排除原统计回调并纳入一个真实P0待证分支。原全部P0/P1分类及Pasto完整迁移仍未完成，目标保持进行中。

[逐地址记录](p0-p1-review-round25.json) · [静态证据](p0-p1-review-round25-static-proof.json) · [清单v5](p0-p1-review-scope-v5.json) · [边界决定](p0-p1-review-boundary-round25.json)
