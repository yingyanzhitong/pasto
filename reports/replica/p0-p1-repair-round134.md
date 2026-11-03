# 第一百三十四轮：空主内容的本地详细诊断

上一轮是实质进展：空表示数组raw诊断已迁移，余primary-empty typed-preview本地详细日志。本轮继续P1修复，不改联网同步、schema或P2。

nativeText在主串非空、unknown、无typed metadata或expected length=0时保持原出口。进入有效typed fallback后，将expected length与fallback结果交给实际content reader：text用metadata.length、link用canonical URL的String.count、files用无分隔路径拼串的String.count、image/color用-1。记录日志在最终fallback非空选择之前，因此成功恢复内容时也记录。除传出这些诊断信息，原primary/value fallback结果路径已按原文归一证明不变。

本地level2消息字段为id/type/app/synced/created/previewLength/usedPreviewFallback/types。类型摘要最多5个item，每个保序取前10个type；按当前data map取字节数，缺失0，保重复，不排序去重，格式item[index]={type:size, ...}，item间以分号空格连接。原hasAttributedString/pasteboardItemCount仅供独立telemetry payload，本轮不混进本地消息或接网络回调。

synced实际来自38efa8按objectID.uriRepresentation.absoluteString筛选objectURI，328980限1条offset0的本地ObjectMetadata fetch。原v10.mom实体和ObjC实际class名均已核。c00560 selector是createdAt；c0bba0是setFetchOffset:，没有误当includesPendingChanges。当前同context做该本地查询；离线模型缺ObjectMetadata时没有该类本地记录，guard返回false。该模型适配明确保留，不将现有CloudKit JSON journal伪装成原ObjectMetadata，不添加schema，也不声称原云端writer/完整generic fetch错误DI已迁移。旧nativeIdentifier为空时用key、required createdAt缺失时不记录也是既有本地模型边界。

1生产文件8个精确增量，246源文件保持。13原反编译片段、18ARM字、两个真实chained selector、消息字符串、原模型与ObjC metadata均绑定，5旧方法保持。新增16项，完整2102源码/Python/Mach-O静态检查通过。首次1失败1error来自130旧测试要求文件路径零长度门的内联拼写；两条断言改查同一joinedPaths与零长度门后通过。3历史测试工具7处精确调整，旧proof和初失败日志留存；新测试查当前实现，无编译或运行框架。

v45保201函数记录179组，6条额外分支均有有限源码修复，未因同函数细分扩分母。P0 77/77、P1 124/124、合计201/201（100%）仅当前已确认有限差异清单；不是全P0/P1或81,123原函数完成率。04430c/0f733c两未知、完整DI/模型/错误父合同及其余P1实际消费者继续核对，整体迁移完成率未知，目标仍在进行。

仅本地修改。版本1.0.2、HEAD、function-map与官网/README下载链9份既有修改保持。未编译、构建、安装、运行应用/系统框架、联网、提交、推送、打标签、发布或部署。
