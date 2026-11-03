# 第185轮：原生实体筛选图标

2026-11-01。继续P0修复→P1检查→P1修复，P2和联网排除。

原0546e0的三个特殊分支依赖真实本地实体：应用按名称查Application并读取rawIcon，存在但数据缺失/无效时310dd0返回空NSImage；设备按名称查Device，31212c仅允许unsigned rawType0/1/2，再选iphone/ipad/macbook；分组以原String标识查List，3293c4成功解码pinboard颜色后用324cb0/3de9a0转换并绘制12pt圆点。无实体/属性才回通用符号；通用符号nil返回nil，图像存在性检查后会再次创建，最后必须有questionmark.square，否则原代码trap。

已绑定applications/devices真实witness槽ecc8e8/ecc938→35fa18/35fe08。原名称谓词是name ==[c] %@，不是建议列表的MATCHES[cd]正则，也没有items计数门。原通用请求保留class默认sort/predicate和batch20，覆盖name谓词后limit1/offset0取首个；32af20机器错误分支释放Swift error并给空结果，不传播。当前新firstNamed复用原请求工厂；Store→Persistence→同主viewContext.performAndWait读取应用图像/已校验设备类型，不创建实体、不改历史。

共享chip现在调用原生图标分支，去掉旧sourceApplications DTO/history猜测及NSWorkspace补查；标题仍在图像之后按上轮原rawValue规则解析。分组的现有Palette及OriginalPinboardHeaderIcon复用，绘制代码未改；另核对3ed004描边算法，sRGB转换后RGB乘1-amount、alpha原样保留，失败回原颜色，与当前darkened一致。设备值通过本地facade返回同MainActor上下文读取的枚举快照，未声称原实体/DI/私有ABI同构。

328e60的共享标记确经3b4444读取cloudKitZoneOwnerName/shareRecordData并解码CKShare、32670c读参与者信息，按用户排除CloudKit/协作的范围单列；当前独立应用仅本地未共享分组，shared:false不宣称覆盖原共享列表输入。未修改既有同步代码，也没有运行或联网验证。

4生产文件7精确增量，243份不变；247源逆恢复/旧快照幂等、362历史Python精确还原。31原片段、14完整机器范围、208直接分支、25真实ARC/error导入、9真实selector、2谓词MOV重建、2witness槽和4符号字节绑定；18邻接方法、11共享源保持。13有限要求审计，新增20检查；203项定向和2751项完整源码/静态检查通过，审计后20复验通过。3旧测试文件9处历史归一化调整；定向首轮顺序断言误匹配分支return、完整首轮1项旧整文件摘要失败均留日志并修测试读取，未调整生产逻辑迎合快照。

v89新增并修0546e0本地分支、35fa18/35fe08实际读取链三条有限记录/2组，既有242记录保持；245记录214组/16额外完成合同：P0 81/81（100%）、P1 164/164（100%）、总245/245（有限100%）。这仅是已确认差异修复率，不能冒作全部P0/P1或原函数完成度。query-array格式包装器真实消费者、unknown0f733c及其余实际父合同仍开，整体目标继续。

官网9文件、版本1.0.2、HEAD和function-map保持。未编译、构建、安装、运行应用/框架、联网、提交、推送、发布或部署。
