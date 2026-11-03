# 第一百零二轮：颜色、链接读取与实体事件

原Color getter3bbc20和Link getter3bf65c通过31ebc8读取当前Item.rawPreview，分别取得颜色或canonical URL。31ebc8明确使用objc rawPreview，最初只读复核中将其称为Item.data已更正；Image3bd9cc才从Item.data读取原始表示。本轮不把颜色/链接的观察机制外推给图片。

新增原生颜色/URL getter，缺失或错误类型颜色元数据返回黑色，Link维持canonical metadata失败时trap，不静默改用旧缓存。Color native type2工厂可不提供DTO，使用捕获实体创建内容；旧非文本chrome尾提取为shared helper，逐字符证明header/footer/layout/编辑连接不变。Link正文renderer仍保留旧Store适配，未宣称该父合同完成。

原3bc500→3bbf5c先替换VM+50的实体，再调用UI；Color回调3e16b4只有非编辑时刷新颜色与标签，Link事件不写URL编辑框。当前Color/Link均先按原生context/objectID订阅，再初读同handle；回调先更新editInput再交UI。Color编辑中保留显示但更新模型，取消/比较读新值；Link只更新本地metadata，打开和显式进入编辑读当前URL。原有legacy值订阅及保存代码保持，观察层没有新增isDeleted过滤。完整删除/失效对象fault和原生通知生命周期仍未验收。

21个原片段、17处实际ARM调用、10个字段/回调/编辑门指令绑定。1540项Python源码/Mach-O静态检查全部通过，包括18项新增。4个生产文件修改，243个保持本轮前摘要；11个精确增量，2个历史测试/工具仅隔离这些增量。17个既有方法和10个共享源保持摘要，Image与旧只读renderer未改。未发生本轮检查失败。

有限差异清单v26保留v25全部174条/158组，新增并修两个getter与共用事件三条：P0 70/70，额外P1 107/107，合计177/177（100%）。共用事件只计一次，Color工厂扩展不重复计已存在3c3c90。该比例不是Pasto总体或完整函数迁移率。

Link正文/完整factory、image/files/card、坏数据/完整metadata codec、删除fault、模型/DI/ABI/UUID桥、图片task/debounce/Undo/OCR调度、组/Stack/选区与04430c/0f733c仍开放，目标继续。未编译、构建、安装、运行应用/框架/CoreData、联网、提交、推送、标签、发布或部署。官网9个本地文件、版本1.0.2、HEAD和function-map保持；静态检查不冒充功能或性能实测。
