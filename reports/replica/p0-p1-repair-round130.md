# 第一百三十轮：修复P1原生索引构造与空内容回退

按P0修复→P1检查→P1修复继续，在129确认五模块当前入口和两处额外搜索差异后，本轮只修改两个搜索源码文件。

原生索引记录构造改为读取key UUID、required updatedAt和native title/type/来源应用/设备/分组/optional timestamp，不再先解完整ClipboardItem兼容归档。record工厂接收id和optional originalTitle标量；工厂主体仅替换旧value.id/originalTitle两项访问，类型名称、nil标题默认及其余输出保持。图片/内容能力仍为原分支下的延迟reader。旧值snapshot只改向该标量工厂传参，原提取格式不变，未改写任何既存content或旧归档关系。

native reader的空内容现走原typed rawPreview分支，复用既有primary extraction而不提供DTO文本回退：unknown空主串为nil；缺失metadata为nil；typed text先判断stored length非零，再读取完整first rich/plain表示，不使用截断预览sample。typed link先判断canonical URL非空，再合并optional name；typed files按无分隔路径长度判断零值，再空格合并。image/color typed metadata无文本恢复，以及恢复为nil/空时，保留原主空串。非空主串、value snapshot和普通primary提取原文保持。

范围仍有限：原3724f0的完整本地diagnostic、Objective-C raw getter异常继续路径和完整上下文/ABI父树未在这两个额外合同中冒称等价。本地必需UUID/date约束及其他兼容适配保留。

只读复核曾提出Link主URL不应追加name、占位URL成为主URL两项反证。主审用原3724f0 C627–720明确指出primary URL后仍读取metadata optionalname，且当前主URL仅从item取；复核已撤回，未按无证建议改动共享codec。主审另独立补齐typed link expected-length零URL门，再绑定最终源码和测试。

2生产文件8个精确增量，245文件不变；8原片段、6实际调用、13ARM字、11个不变方法和6个共享源已绑定。工厂及value snapshot重构有源码等价证明，原所有数据保存/P0复制/OCR SDK写入消费者保持。18新增检查，累计2048项源码/Python/Mach-O静态检查全部通过。

初始2048检查有73项历史hash/形状失败及1error；接入精确逆链后剩3个直接hash失败和2个错误UTF8读取二进制资源，改为只逆向Swift源码并补直接hash隔离后通过。6旧测试/工具20处审过的精确隔离增量，原proof、两次失败日志和实际最终源码均保留。新增18项检查直接读当前生产实现，不用逆向旧实现冒充测试。未编译或执行Swift/Objective-C/CoreData/系统框架。

v41保留全部201记录179组，129重开的371998/3724f0两额外合同已标source_repaired，不重复增加函数数。P0 77/77、P1 124/124、总201/201（100%）只指已确认有限差异，完整P1父合同与04430c/0f733c仍待证，整体Pasto迁移率未知。目标继续。

仅本地修改；未编译、构建、安装、运行应用/框架、联网、提交、推送、打标签或发布。官网9文件、版本1.0.2、HEAD与function-map保持。
