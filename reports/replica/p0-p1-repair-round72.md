# 第七十二轮：FRC 初始化的 ID 查询与校对

原 `365e18` 构造器在成功 performFetch 后、安装差分 delegate 前，确实直接调用 `366344`。Pasto 此前固定遍历 `fetchedObjects`；本轮改为原分支：有待保存修改时仍从 FRC 对象取 ID，无修改时先按实体名、谓词和排序做 ID-only 查询，核对第一 section 数量、第一项和最后一项；缺 section 或核对不符时回退 FRC。首尾相同的中间项不再逐项额外比较，保留原快捷分支。

原 `367014` 新建 ID 请求，只复制 entity/predicate/sort，将 resultType 设为 1；没有复制父请求的 limit、offset 或 batch。缺实体名触发原 trap；ID 查询 Swift 错误释放后返回空候选，再参与校对与回退。该错误分支被 Ghidra 标记 unreachable，但 ARM 的 x21 条件跳转、真实 throwing fetch import、swift_errorRelease 与空数组加载证明它实际存在。不能由伪代码的警告删除错误处理。

`367184` 对负数、缺 section 或越界位置返回 nil；非空域使用第一 section 的对应 objectID。Pasto 用 Foundation 的 `[section, item]` IndexPath 表示相同位置。本轮只改共享 FRC 构造器和三个私有 helper；公开 subject.value、差分、pending/flush、通知、搜索 wrapper、列表/UI 与存储模型保持原样。没有因未找到常见间接指针就断言原函数没有消费者，也没有推断全部公开同步 getter 合同。

| v15 已确认有限差异 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 93 | 93 | 100% |
| 合计 | 162 | 162 | 100% |

v15 保留旧 161 条/145 组，新增并修 `366344` 一条有限初始化差异；两个支持函数不重复计分。该比例不代表完整 P0/P1 模块或所有原函数迁移完成。04430c/0f733c、完整 viewmodel/DI/actor/源切换、任意 history 标识/metadata、pending/cross-process payload、CoreData 模型迁移仍未闭合。

1112 项源码/静态检查通过，本轮新增 14 项（前轮新增 11 项已纳入）。先运行旧定向 47 项发现 3 个历史摘要/整体构造器断言失败、1 个旧定位错误，日志保留；三处旧测试/工具仅明确隔离新增初始化块及调用，继续比较其余原合同。新 14 项与定向 61 项均通过，再执行完整既定源码检查集。标量分支表是源码约束，未执行 Swift 方法或数据库。

证据绑定 6 个原函数片段、12 个真实 selector、2 个 import、18 条 ARM 字和本地 SDK resultType 枚举。1 个生产文件修改、241 个不变，无新增生产文件；3 个旧测试/工具更新，新增 1 测试、1 范围比较工具。原分支可能减少初始化的对象数组遍历，但没有测量真实性能，不能称性能回归通过。

官网 9 文件、版本 1.0.2、HEAD、function-map 保持。未编译、运行框架/数据库/应用、联网、安装、提交或发布；目标继续进行。

[机器证据](p0-p1-repair-round72.json) · [有限差异清单v15](p0-p1-difference-backlog-v15.json) · [本轮源码补丁](p0-p1-repair-round72.patch)
