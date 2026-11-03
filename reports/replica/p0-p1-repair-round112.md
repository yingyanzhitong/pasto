# 第一百一十二轮：新建分组原生返回链与编码错误分支

原ListRepository Writing+8经eccd68→eccda0、eccda8→368540→368560创建原生List。367c5c在witness调用后把返回x0保存到x19，释放UUID字符串后再交回同x19；Ghidra的char*别名不能据此判定返回UUID。列表0538b4把创建返回保存并直接交3b9a78分配；preview3c36f0先创建，再经3c2ee0读取当前Published Item。两条输入时点不能混淆。

本轮ListPersistence.insertPinboard返回新建object与attributes；Store同一事务返回兼容board与strong ClipboardPinboardTarget。既有public create/FromIntent仍返回board，名称验证不变；新增createPinboardTarget供列表和preview原生consumer使用。Controller继续用构建时captured selectionItems，preview继续创建后读self.input；两者直接用target重载，不再通过board.id重新查询List。legacy orderedIDs和preview旧modal完整尾不变，未用颜色优先用户适配保留。共享事务、同步、assign方法及模型没有改动。

另外核出此前Ghidra省略的错误支路：368754检查Swift错误寄存器；失败后释放错误、x20=nil并跳到setRawAttributes，再设置rawType2、返回原List。因此try encodeAttributes直接抛错不符合原逻辑。本轮改为try?，失败仍以nil属性继续。显式更正第57轮关于编码错误传播的当前实现断言；该轮正确的插入/永久ID顺序证据不改写，也不外推save/异常/外层rollback。列表创建外层transaction错误仍有trap/UI facade差异，完整错误合同未计闭合。

17原片段、14真实branch、18ARM字、2真实链指针与2setter选择器绑定。4生产文件10精确增量，243生产文件、5共享源及7既有方法保持。20新增源码检查；初次1721项中9失败4error均为旧接口/摘要shape，已通过7历史测试及1工具仅逆隔离本轮增量，保留初日志，不改旧proof或摘要。最终1721项Python源码/Mach-O静态检查通过。既有低模型只读复核同对象、同步、访问级别、tuple和编码错误分支；未运行Swift/应用/框架/CoreData。

v35原样保留190条/173组，新增367c5c返回及0538b4 consumer两有限记录并修；已有368560和3c36f0的额外修复不重复计地址。P0 70/70、P1 122/122，总192/192（100%）。这是已确认差异清单，不是完整函数或Pasto整体迁移率。完整创建/模型/DI/context/fault/save/owner、兼容blob/cache-miss错误、Stack/选区/image父合同与04430c/0f733c继续开放，目标进行中。

未编译、构建、安装、运行、联网、提交、推送、标签或发布。官网9份本地改动、版本1.0.2、HEAD和function-map保持。
