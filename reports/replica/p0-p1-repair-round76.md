# 第七十六轮：同步选区复制直接交付已解析输入

原37a144使用调用者提供的实体数组构造处理器，再将相同序列交付恢复事务。原输入保留、processor+0x10存储和38222c调用已绑定4条ARM字，相关7原函数片段摘要同时冻结。此处不应把已取得的条目先转ID，再从另一个值快照重建输入。

本轮新增selectedItems写入入口，保留输入顺序和重复项，转入原shared writer。已解析分支直接使用这些值，不调用reload、不查询Store.items；ID-only调用保留既有reload、非删除校验适配。真实copySelection在原空选择beep后，通过原performCopy直接交付已解析选中项。

从let selections开始的表示处理、prepareHistoryRestore、剪贴板writer、保存失败处理、Undo、DidRestore通知全部与前轮逐字相同。反馈/隐藏和AppMain的权限、目标应用、焦点交付均未改。事务仍使用既有预备native targets；本轮没有更改模型、持久化或跨进程合并规则。

这只是同步选区复制输入的部分修复。当前值来自对象引用的ClipboardItem投影，原版保留实体数组，不能据此称完整entity/schema/DI等价。直接paste可能经过权限modal，实体/值的取样时点和生命周期仍需单独核对；copy(item)、copy(ids)、OCR等入口也保留ID适配。sourceApp字段、元数据成员及其他消费者尚未闭合，不宣称实际性能改善。

| v16 已确认有限差异 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 93 | 94 | 98.94% |
| 合计 | 162 | 163 | 99.39% |

3544dc仍未关闭，有限分母/累计修复数和function-map不变；完整模块和04430c/0f733c继续开放。

1149项源码/静态检查通过（新增12）。检查真实selected入口、resolved分支不重读、ID兼容分支、copy消费者、原处理/保存/Undo/通知尾部及其他代码不变。初1137旧检查出现17个结构/摘要失败及2个定位错误，6处旧测试/工具按明确input增量或实际入口更新后全绿，日志保留。未执行Swift方法、剪贴板、数据库或性能回归。

243生产文件中2个修改、241不变；6个旧测试/工具调整，新增1测试和1范围工具。官网9文件、1.0.2、HEAD/function-map均保持。未编译、运行框架/数据库/应用、联网、安装、提交或发布；目标继续进行。

[机器证据](p0-p1-repair-round76.json) · [差异清单v16](p0-p1-difference-backlog-v16.json) · [源码补丁](p0-p1-repair-round76.patch)
