# 第七十九轮：列表成员和主选区使用对象引用

继续P1实时内容读取链修复。上一轮来源应用已经从原生关系读取；本轮进一步去掉列表成员必须存在于Store DTO字典中的条件。

原FetchedResultsCollection把缓存对象ID数组作为成员序列，indexed读取另经35440c/3544dc按同context解析实体；缺项/越界为required错误。复用并重新核验第73轮14个原函数片段、协议/类型/表槽、原生selector及二进制证据，不把只读库存扫描计入迁移。

Pasto普通和搜索列表新增ClipboardCollectionEntry：原生成员只持UUID和对象引用，不在构造时fetch或解码payload。普通列表同一次Snapshot提供ID和引用，搜索用实际FRC结果ID/引用；缺引用报错，不能回到旧DTO。此前source IDs=[A,B]、cached values=[A]会经compactMap只保A；新结构保留A/B。此例为源码结构反例说明，未执行Swift或复现运行故障。

host pending/applied及八个ID选区/导航/邻项helper使用Entry数组，方法体的队列、mutation-before-selection、清槽、焦点和回调顺序保持。渲染只解析可见索引，选中动作只解析选中索引；恢复Entry直接保实体，不提前读payload。主选中项使用已应用列表，owner失效不回新投影；无owner选区使用自身Entry引用。双击和数字快捷粘贴按已应用ID接原跨modal持实体路线。

旧本地tombstone过滤、回收站值记录和secondary membership归档顺序属于兼容适配。旧归档含secondary时保原archive顺序，并追加未出现在Store的原生成员，避免继续丢项；不把此混合域称原版单owner模型等价。

| 已确认有限差异 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 93 | 94 | 98.94% |
| 合计 | 162 | 163 | 99.39% |

3544dc仍未计为整条完成：其他ID-only复制/Stack/OCR和持久化编辑/删除消费者、全实体/DI/模型替换及生命周期边界尚需核；分组选区顺序候选的原动作消费者仍未闭合。04430c、0f733c继续未知。当前清单不是全产品完整迁移分母。

1199项Python源码/静态检查通过（新增20）。新检查覆盖实际FRC成员不依赖缓存值存在性、延迟内容读取、主选中项/owner门、真实双击/数字粘贴、八ID方法与applier时序以及其余源码保持。16个历史测试/工具显式隔离23个已审body/类型/调用变化和单新增文件，原证据摘要未改。首次执行1130项有27失败/12错误（含setup失败导致部分未执行），后续7项/1项旧形态失败及新增检查的selector字面名、重复update定位错误日志保留，最终1199全部通过。

2个生产UI文件修改、1个Core类型新增、242个生产文件保持；writer/持久化模型/Package/AppMain未改，官网9文件及1.0.2/HEAD/function-map保持。未编译、构建、框架/数据库/应用执行、联网、安装、提交或发布；不宣称实际性能或运行回归通过。目标继续进行。

[机器证据](p0-p1-repair-round79.json) · [有限差异清单](p0-p1-difference-backlog-v16.json) · [源码补丁](p0-p1-repair-round79.patch)
