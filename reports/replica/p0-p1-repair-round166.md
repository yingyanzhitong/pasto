# 第一百六十六轮：本地分组原生删除与面板确认

继续P0修复→P1检查→P1修复，本轮修改P1分组删除的真实消费者。菜单rawType2分支捕获ClipboardListTarget，计数、确认状态和提交均保留同一List。移除兼容Pinboard行存在和UUID匹配的前置门；面板确认直接显示该目标名称，移除菜单已不使用的Pinboard参数。空组立即执行，非空仍在panel内确认；失败继续在同一面板展示供重试/取消，成功由原生集合选择邻项。

## 对照与实现

368818从目标List自身managedObjectContext读取329088构造的项目请求。nil context取空数组；fetch失败块3688d4虽被Ghidra删除，真实3688d8调用swift_errorRelease后汇入空序列，再继续删除List。本次保留try? fetch→空数组，不把失败改为提前return或额外错误弹窗。

363004的本地分组分支先检查项目实际owner与目标List相等才解除关系；历史timestamp和owner都为空才调用3646ec式项目自身context.delete。原生序列清理完成后才删除目标List。当前采用同一对象、原请求顺序和这些门，不先用缓存成员或UUID筛选内容。

ManagedRepository在全部原生变更后才读取兼容key/UUID并登记assigned/unassigned/alreadyDeleted集合，阻止后续兼容回放重复归属/删除。Store之后移除兼容组及投影当前项目，仍在历史中的内容保留、原生已删除内容移出兼容缓存；fetch失败时不按缓存推断孤立项目并追加删除。未保存/无兼容分组行可进入原生操作，不冒完整坏数据投影/框架时序验收。

本轮仅迁移原通用删除的local rawType2分组分支，rawType1历史timestamp/refresh继续由既有P0入口负责并保持不变；没有宣称新API覆盖任意List类型。原3c5308消费事务错误，Pasto保留既有panel内失败展示作为用户交互适配。原3acd8c明确recordID/zoneID→private/sharedCloudDatabase，排除该云删除子链，不排除368818本地尾。

## 验证与进度

15原片段、2真实协议指针、102实际调用、5完整机器范围、5实际ObjC选择子及关键分支绑定。5生产文件16处精确增量，242文件保持；247文件逆恢复和7旧测试/工具17模式精确重放通过。新增11项直接核对当前源码/机器码，完整2466项静态检查通过。首7失败2错误是旧UUID入口/确认状态和历史摘要断言；定向122项仅1项把历史注释里的NSAlert误判为真实调用，已仅过滤注释后复查，日志保留。未执行Swift/ObjC编译、CoreData/Combine/AppKit/UI，不称功能回归通过。

有限清单仍P0 81/81（100%）、P1 144/145（99.31%），总225/226（99.56%）。v72仅给367f78追加部分修复，不加地址完成计数；原生全List排序、私有context保存observer、创建inline编辑/未用色及两unknown继续开放，整体迁移完成度未知。

下一步沿368a30→36c25c/36c290/35ca9c核对完整顺序和私有context合并，再替换兼容数组排序。版本1.0.2、HEAD、function-map及官网/下载九文件保持，只留本地修改，不编译、构建、安装、运行、联网、提交推送或发布。
