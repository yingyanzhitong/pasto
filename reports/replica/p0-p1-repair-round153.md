# 第一百五十三轮：ItemData 实际对象持有本地日志

遵循先修P0→检查P1→修P1。继续原生类族后发现P0共用数据读取生命周期差异，因此先补：原31b494在.cxx_construct建立ItemDataEntity命名日志wrapper，31b59c释放对象字段；Pasto主读取直到异常时才建立关联对象，搜索私有context则临时创建。原类表与真实ARM确认该字段所属ItemDataEntity，不是Syncable父类的日期行为。

新增实际PastoItemDataEntity，直接继承NSManagedObject，以stored let持有本地命名wrapper。当前model注册此类；主读取和搜索私有context都优先复用data.diagnostics，旧plain对象仍保关联/临时fallback。没有加入createdAt/updatedAt hook；raw getter、异常诊断、空数组返回和解码函数体逐字不变。wrapper构造仍不解析输出sink，保持原有惰性本地日志依赖行为；遥测不接入，serialization format继续由既有参数适配，不冒整个原cxx_construct完成。

模型增加includeTypedItemData，新增上一当前model为false候选，既有11源模型各显式false，共12个源模型候选；原属性、关系及迁移算法尾保持。实际模型hash、NSManagedObject初始化、fault和ARC释放均未运行，不称数据库迁移或生命周期运行验收。

6个原函数片段、原真实类/父指针、构造工厂和析构释放两个ARM调用绑定。修改3生产文件7处，其余244文件不变，5共享源保持。8新增源码检查直接检当前类、模型和两消费者，完整2340项源码静态检查通过。首次4项旧摘要/模型候选数量失败、第二次1项旧完整源码摘要失败日志保留；3旧测试/工具7模式8替换仅精确隔离本轮增量，新增检查未隔离当前代码。247源文件完整逆增量恢复与旧测试调整精确重放通过。

v62新增31b494一个有限修复记录，保留旧216记录194组及11额外合同：现217记录195组。已确认清单P0 78/78、P1 139/139、总217/217（100%）；这是有限差异修复比例，完整P0/P1、模型/DI、序列化依赖及04430c/0f733c未知尚未闭合，整体完成率未知。

只保留本地改动；版本1.0.2、HEAD、函数映射、官网/下载九文件保持。不编译、构建、安装、不执行应用/系统框架或CoreData、不联网、提交推送或发布。
