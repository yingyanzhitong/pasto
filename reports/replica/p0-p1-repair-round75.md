# 第七十五轮：已应用选区与拖拽按需读取

本轮继续部分修复3544dc，应用源码只改两个UI文件。host新增已应用选区读取入口：先验证state/owner身份，使用已应用items建立ID到index映射，按请求orderedIDs保序、跳过不属于已应用列表的ID，只对选中位置调用已有实时渲染读取。该入口不会解码全部历史内容，也不改pending/applier/保存或选择状态。

state.selectedItems有owner时使用同一applied入口；失效owner返回空，不回落到较新的可见投影。无owner时保留既有可见成员适配，仅为选中行读取当前对象引用。controller的实际选区入口验证loaded panel、真实host及window，然后交付有序选中ID；复制/粘贴、编辑、打开、写作工具和空格预览等原调用入口继续复用。拖拽仍使用原已应用index及预览位置，只将选中值改为这些index对应的实时读取，原group writer、marker、modifier和formation逻辑保持。

复制/粘贴的选区入口已读实时值，但后续仍转为ID，恢复writer再reload Store获取输入。该交接没有在本轮迁移，可能产生重复投影；未测量性能，不能据本轮源码接线声称复制更快。下一步优先核对原恢复输入/上下文，连同元数据成员及其他动作继续处理。

| v16 已确认有限差异 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 93 | 94 | 98.94% |
| 合计 | 162 | 163 | 99.39% |

未关闭3544dc，不增加累计修复条数、分母或function-map标记。visibleItems/primary元数据路径、恢复writer、删除/编辑持久化、其他动作和完整生命周期仍待核对，两个未知04430c/0f733c继续保留。

1137项源码/静态检查通过（新增12项）。覆盖已应用owner gate、ID顺序/缺项过滤、仅选中值解析、无owner适配、loaded panel和window检查、真实copy/paste/open/edit/write/space消费者、拖拽index与旧合同其余代码保留。初1125旧检查有13处旧结构/摘要失败和1处定位错误，6个旧测试/工具沿新实际入口或明确限定选区增量后全绿，日志保留。未执行Swift方法或原生运行回归。

243生产文件中2个修改、241不变，无新生产文件；6个旧测试/工具调整，新增1测试和1范围工具。CoreData提供者/模型、恢复writer、Package和保存时序均未改。官网9文件、版本1.0.2、HEAD/function-map保持；未编译、运行框架/数据库/应用、联网、安装、提交或发布。目标继续进行。

[机器证据](p0-p1-repair-round75.json) · [差异清单v16](p0-p1-difference-backlog-v16.json) · [源码补丁](p0-p1-repair-round75.patch)
