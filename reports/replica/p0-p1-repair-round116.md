# 第一百一十六轮：恢复时间不回放旧内容

继续P0。原361ec0先逆序取输入，逐个Date→setTimestamp，然后按List属性清理和refresh，不以缓存重建ItemData或覆盖预览/排序。本轮针对Pasto已捕获原生目标后仍进入通用值差分保存的边界修复：只有native targets准备的Transaction登记原目标；旧值/ID入口默认没有该登记。

对已有state行，以previous整行复制，只替换createdAt/updatedAt/isInHistory，再作完整ClipboardItem Equatable比较。除这三字段外全部相同才走快捷路径：对同一捕获实体仅写既有localCreatedAt/updatedAt/inHistory兼容列，从通用Item更新的前后数组同时排除。这保留原生timestamp和当前data/rawPreview/order，不按UUID重查，不补写缺失内容。任何其他本地字段变化仍走原apply。没有根据contentForComparison的裁剪子集误吞标题/顺序/来源快照改动。

只读复核发现一个额外反例：target缺state行但previous有行时，原补丁会被差分当作删除。现以native target IDs减state IDs，仅从previous排除这些缺值目标，不造DTO、不复活context已删除对象。非target缺项仍删除；有state且真实编辑的target仍走普通更新。空缓存两侧缺项也继续保存原生时间。

8原片段、361ec0完整26个BL和实际setTimestamp选择器绑定；复用第13/14/115轮时间/无share/目标证据。原反序timestamp循环及10既有方法保持，generic apply→refresh/save尾严格原文保持，6共享源不变。仅1生产文件3精确增量，246生产文件不变。分组/Stack/P1生产未扩展修复。

21新增检查包含所有25个存储字段的反例、三时间字段所有组合、当前native内容不被覆盖、缺缓存误删、非target删除和真实编辑保留。最终1802项源码/Python/Mach-O静态检查通过。初辅助脚本因假设存在pathlib import定位失败，逆链未接导致69失败11error；修复定位、新检查实际25字段和最新P0计划断言后，3失败7error均旧shape，再精确逆隔离本轮增量后1800绿。只读复核随后提出缺缓存反例，修生产并补2检查后1802绿。初/第二次/反例前日志均保留；9既有测试工具18修改可精确逆推baseline，其中7历史测试和1链工具仅隔离本轮源码，1计划断言按用户最新P0顺序更新。

既有低模型只读复核修复前反例与修复后数据流、真实编辑/删除保持、类型/actor形状，未发现明确新缺口。无Swift/CoreData/应用执行；不把源码检查称实际性能或运行回归。

既有361ec0/37ade4额外消费者修复不重复计数，v37原样保持：P0 72/72、P1 124/124，总196/196（100%）。这是已确认有限差异分母，整体迁移率仍未知。完整metadata验证/合并、模型DI/context/fault/save/跨进程一致性及两未知未闭合；P0继续，之后检查P1再修P1，P2和联网排除。

未编译、构建、安装、运行、联网、提交、推送、标签或发布；官网9文件、1.0.2、HEAD及function-map保持。
