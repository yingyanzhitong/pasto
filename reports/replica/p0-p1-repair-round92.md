# 第九十二轮：标题比较、空值与原生回写

本轮继续P1编辑链，不涉及界面布局。原3bae08先用原生title或类型默认值组成显示标题；提交值相同就直接返回，不trim也不开事务。不同时才trim，结果为空时再次读取原生title，据当前字段是否非nil决定nil或Some(空串)，最后经2ff310提交。364ab4只在optional标题不同才setTitle，3bbb70只复制捕获的标题值；该链无时间更新。

新增共享OriginalPreviewTitles.f_1003bae08，两个getter参数采用autoclosure保留默认值延迟与空结果二读；update回调可抛错并rethrows。native updateItem(handle,title:)在事务前比较同一object的title，默认rawType/rawPreview也从同对象读取；进入callback后在已有事务内投影同input当前metadata，只更新标题并交TitlePersistence对同object写入，cache缺项补入、命中替换，不按ID另找目标、不改日期。两个preview factory将已有input传到header的真实提交闭包，保留weak view/state和view寿命保护。

旧card/ID更新路径同样复用规范化逻辑，但其调用位置仍在原mutate内，因此“显示相等不启动事务”只适用于本轮native入口，旧值入口只是不改字段。正文编辑和text格式更新尾部、默认标题资源、内容归档比较与原生setter均保持。

绑定9个原片段、2条真实title getter调用/选择器及实际Writing+0x20槽，复用第87轮字段与setTitle证据。1386项源码/静态检查通过，新增15项，覆盖比较/trim/二读次序、相等native无事务、optional与错误传播、同对象默认值/目标、cache和预览实际消费者。首轮1371项有34失败/5错误，主要为旧标题形态/摘要，日志保留；2个旧测试/工具只隔离7个精确hunk，历史证据不改。旧1371与最终1386均通过。3个生产文件修改，其余244个保持，无新生产文件/schema/Package改动。

| 已确认有限差异 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 70 | 70 | 100% |
| 额外P1 | 96 | 97 | 98.97% |
| 合计 | 166 | 167 | 99.40% |

本轮补已有标题/实体父合同，不新增完整函数或有限差异分母。卡片/未传input的普通预览仍可走ID适配；header显示观察、通用metadata的UUID同步、投影错误与跨进程合并时序、跨Store/context及完整DI/ABI、3544dc父合同、其他内容/分组mutation、Stack失效/owner、选区观察与04430c/0f733c仍开放。百分比只描述v20有限差异，整体目标继续进行。

主智能体独自修改，复用1个既有低模型智能体只读核原流程和当前hunk，明确保留旧值事务边界。未编译、构建、执行框架/数据库/应用、联网、安装、提交或发布；官网9文件、1.0.2、HEAD与function-map保持。

[机器记录](p0-p1-repair-round92.json) · [源码补丁](p0-p1-repair-round92.patch) · [有限差异清单v20](p0-p1-difference-backlog-v20.json)
