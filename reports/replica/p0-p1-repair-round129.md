# 第一百二十九轮：P1当前入口检查与两处搜索差异

本轮只检查，不改生产代码。搜索候选独立错误及顺序、原生分组和目标、Stack原生队列/渲染/复制粘贴、同input文本编辑提交的当前有限路径可复用。OCR独立核查确认四叶用于原Spotlight worker；原用户图片选区复制由VisionKit automatic overlay承接。Pasto新增整图OCR菜单复制全部文字，与系统选区copy不属同一动作，不能把两者文本范围和写入路线不同冒称数据丢失。

确认两个额外搜索源码缺口：

1. **371998索引元数据构造**：Pasto `ClipboardSnapshotReader.searchIndexRecords` 先解码完整ClipboardItem。若旧content blob无效，即使native字段/data/rawPreview有效，也在创建deferred reader前失败。原371998从native字段取得identifier/title/type/关系列，只创建内容/图片闭包；SDK真正取内容时才重新读实体。该结论不把缺native data错误当兼容blob问题，也不更改本地必需UUID/date元数据约束。
2. **3724f0空内容分支**：Pasto native Reader在空主串时取旧DTO plainText；unknown空主串返回空串。原3737ec检查主串空后，kind0直接到373870/373888写nil；非零类型373824读取31ebc8当前rawPreview，再走typed rich/file/link恢复。缺metadata有nil出口，而有效typed-empty并非一概nil。原text fallback读取完整原始富文本表示，不能直接把截断的预览sample当完整内容。

22原片段、9个ARM字、实际rawPreview调用及16个当前入口方法已绑定。10新增检查，完整2030项Python/源码/Mach-O静态检查通过。新增检查首次把默认content key在body中定位而实际位于签名，1处断言失败修正并保留初日志。生产247文件与旧256测试/工具保持；1个旧Todo断言由P0阶段更新为P1，原源码检查保留，不改旧proof。完整首次2030检查仅该过时阶段断言失败，修正后重跑通过并保留初日志。

v40保留201函数记录179组，给既有371998/3724f0新增pending合同，原normal有限修复原文保持；不因同函数新分支重复扩表。P0 77/77（100%）、P1 122/124（98.39%）、总199/201（99.00%）。该进度仅对已确认有限差异，整体Pasto迁移率未知。

当前五模块入口检查批次完成，按用户顺序进入P1源码修复。完整P1父合同、04430c归档图与0f733c返回ABI仍未闭合，不把本轮入口范围缩成整体目标。将先处理上述两个已证搜索门，其他模块无证据不盲改。

未编译、构建、运行应用/框架、联网、安装、提交或发布。官网9文件、1.0.2、HEAD与function-map保持。
