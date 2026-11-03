# 第七十轮：普通历史/分组的真实数据源与顺序列

普通历史和分组已接入长期FRC结果源，不再仅由内存数组决定其正常成员与顺序。原329088请求明确：history使用timestamp非空、timestamp降序；pinboard使用list==当前owner、displayOrderInPinboard升序；其他类型保留typed默认请求。新工厂在稳定view context上取真实List并构建请求，共享此前已核的FRC首次抓取错误、差分、更新/刷新通知及批次发布实现。搜索转为convenience initializer，其原始ID谓词与count诊断保留。

本轮纠正旧术语：静态解析原MOM的全部九实体，没有ItemMetadata实体。ItemEntity的displayOrderInPinboard是Int64/default0属性；ListMetadataEntity.index只用于标签顺序。Pasto新增实际顺序列和可选State回填marker，八个旧模型候选（前一typed版加此前七版）明确禁用新字段，既有推断迁移与源库成功后替换算法保留。旧内容仅在marker未完成时回填一次，marker与列值在同一保存事务中落盘；新root首commit直接标1，避免重启从已剥去order的新内容反向覆盖为0。真实CoreData模型哈希/迁移未运行验证。

正常commit在关系更新后按实际列值差异写order；读取先投影owner，再从列投影现有DTO.pinboardOrder。content比较剥掉顺序字段，因此只重排不会重编码未变的图片/其他载荷；原排序算法和其余业务/保存时序保持。旧nil顺序使用原模型默认0，原单一排序键的相等项没有已证稳定次序，不能冒称旧nil/tie行为逐项完全一致。

UI在query/list切换后、selection规范化和applier替换前安装并持有普通结果源/订阅；订阅跳过已同步读取的首值，后续成员/顺序从源缓存取，变化ID进入既有cell reload通道。普通原单owner域按FRC ID序列显示。旧归档可能保留secondary分组成员，显式兼容分支保留这些成员并使用既有Store顺序；删除视图也保留原本地适配。混合legacy域会覆盖FRC顺序，特此保留为用户旧数据适配，不计原版单owner等价。

| v14已确认有限差异 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 92 | 92 | 100% |
| 合计 | 161 | 161 | 100% |

v14原样保留旧160记录/144组，新增并修329088有限请求/存储/实际消费缺口1条，现161记录/145组。支持方法不重复计分；这不是全产品或原版所有函数完成率。完整provider/DI/witness身份、任意列表标识/metadata、pending/cross-process payload、源切换等父合同和04430c/0f733c仍待证。3bb540只证带tag的witness-dispatch，未将它冒称为唯一365cd8请求factory。

1087项源码/静态检查通过（新增20）：11原片段、5真实selector、4条ARM字、原MOM/schema摘要绑定。覆盖新列默认/标记、八旧模型结构、回填/保存顺序、新root重启保护、实际重排读写与content隔离、原请求分支、共享FRC生命周期及真实UI消费者、legacy/trash保留。标量重启/成员例子是源码约束，不执行新Swift函数或数据库。17旧测试明确隔离新字段/源安装块或冻结历史摘要，继续核对原合同其余代码；初32失败/3定位、后续7旧位置及新MOM UID未解引用的断言错误日志保留。低模型只读复核未发现可证marker重启覆盖或重排漏写，并指出mixed legacy分支不保FRC顺序，已如实保留边界。

5生产文件修改、1新增、236不变。官网9文件、1.0.2、HEAD及function-map保持；未编译、运行CoreData/AppKit/数据库/应用、联网、提交或发布。目标继续进行，不将源码检查称为真实迁移/性能/功能回归通过。

[机器证据](p0-p1-repair-round70.json) · [差异清单v14](p0-p1-difference-backlog-v14.json) · [本轮源码补丁](p0-p1-repair-round70.patch)
