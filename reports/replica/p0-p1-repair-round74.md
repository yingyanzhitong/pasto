# 第七十四轮：实时对象引用接入可见卡片渲染

本轮部分修复3544dc，未将整项标为完成。新增引用保存真实稳定view context及NSManagedObjectID；消费者调用时执行existingObject、PastoItemEntity类型检查，再使用既有本地DTO投影。可选读取失败返回nil，required读取失败触发错误；Snapshot索引入口先走数组边界再要求对应引用。该DTO投影的解码错误域是本地表示适配，不冒称原版完整实体schema。

FRC的pending flush与有序UUID在同一批次发布引用，创建引用不读取载荷。普通列表和搜索向实际卡片host提供相应引用；host将引用连同旧元数据items、changed IDs捕获进pending，再按同一批次安装为applied。引用身份变化也会替换pending，即使旧DTO值相等。切换state/model或detach清理applied引用，引用自身仍可按原对象ID解析，不依赖最新数据源的成员字典。

真实tileCells的可见索引循环与refreshCellRoots调用required读取，取得当前托管内容。只有缺少托管引用的本地兼容行使用原DTO；引用存在但查找/解码失败会触发required错误，不会回落旧值。本轮没有增加每次SwiftUI重绘时对全部历史载荷的解码或一个未使用的getter。

仍待迁移：visibleItems的元数据成员投影、selectedItems、appliedItems以及复制/粘贴、删除、编辑、拖拽等实际动作仍有旧DTO路径。已有可见渲染不能证明所有消费者完成，故3544dc保留为未修复记录；Snapshot indexed公开入口也不能仅凭存在就作为全部原UI索引消费者迁移证据。

| v16 已确认有限差异 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 93 | 94 | 98.94% |
| 合计 | 162 | 163 | 99.39% |

差异清单不扩充，不增加累计修复函数，不升级function-map。本轮为该缺口的部分源码修复；完整消费者、实体/DI/ABI、source生命周期及04430c/0f733c等父合同继续开放，不计全产品完成。

1125项源码/静态检查通过（新增13）。覆盖原第73轮14原片段/协议链证据摘要、实际对象引用、可选与required读取、同批发布、普通/搜索路由、pending引用epoch、可见渲染、引用清理及旧合同外代码保留。初次1112检查有14个旧摘要/结构断言失败，7处旧测试/工具仅隔离新增引用/渲染块并继续核对原其余方法；新增测试一处重复if定位错误已修，日志保留。标为源码/静态检查，不执行新的Swift方法、数据库或应用。

4个生产文件修改，新增1个引用文件，238个不变；7个旧测试/工具调整，新增1测试及1范围比较工具。存储模型、Package、保存和FRC差分/通知时序保持；官网9文件、1.0.2、HEAD/function-map保持。未编译、运行框架/数据库/应用、联网、安装、提交或发布，目标继续进行。

[机器证据](p0-p1-repair-round74.json) · [差异清单v16](p0-p1-difference-backlog-v16.json) · [源码补丁](p0-p1-repair-round74.patch)
