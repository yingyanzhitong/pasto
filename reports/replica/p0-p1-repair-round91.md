# 第九十一轮：正文保存回写同一实体

上一轮将已捕获条目传到编辑观察器。本轮继续保存消费者：原3c0e50两条表示分支从VM+0x38读取同一条目，实际Writing+0x18→363ff0→360ff8直接写该实体，不按ID或新checksum寻找另一个对象。360ff8只在checksum非nil时设置类型/摘要、替换data并生成preview，不改标题、来源或history timestamp。

Pasto的ClipboardRestoreItem增加内部nativeObject引用，正文视图持editInput直到提交。Store新增handle重载，与旧ID入口共用一个事务worker：native目标直接用该object，当前缓存投影从同handle读取；cache缺项时在checksum非nil后补入，不以旧缓存决定原生输入是否有效。legacy/value仍按ID查找并走prepareHistoryItems。nil checksum在目标选择、实体写入、缓存内容/append和preview之前返回。data→preview、替换marker及通用保存/发布尾部复用不改。

原生分支还移除额外updatedAt=Date，保留实体当前updatedAt/createdAt/history timestamp；旧值分支保原Date。只读复核确认本地merge按payload相对baseline的变化逐字段合并，不用updatedAt决定正文胜负，因此正文无需刷新时钟也会参与合并。updatedAt仍影响本地排序和归档导入比较，本轮原生内容编辑保原时间；不据此声称归档/网络运行回归通过。

绑定6个原片段、6条捕获目标/间接交付指令及真实Writing槽，复用第88轮原生内容setter/preview证据。1371项源码/静态检查通过，新增15项，覆盖同对象target、cache缺项、校验短路、元数据与时间、旧入口及共享writer尾。首次旧套件实际运行1343项、32失败/3错误，含setup失败导致未执行项，日志保留；2个旧测试/工具仅逆变换本轮8个精确hunk，旧证据不改。原1356与最终1371均通过；新增测试清理无意义逻辑断言后定向15项再次通过。3个生产文件修改，244个保持，无schema/Package变化。

| 已确认有限差异 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 70 | 70 | 100% |
| 额外P1 | 96 | 97 | 98.97% |
| 合计 | 166 | 167 | 99.40% |

本轮补已有编辑实体父合同，不增加完整函数/有限差异分母。通用Store merge/commit仍在原生data替换后按UUID同步值元数据；元数据cache缺项时可能触发这些通用setter，不冒称所有原实体调用次数等价。普通预览、标题栏、非文本写入、投影解码错误、跨Store/context混用和完整DI/ABI、3544dc父合同、分组mutation、Stack失效/owner、选区观察及04430c/0f733c仍开放。目标未完成，百分比只代表v20有限差异清单。

主智能体独自修改，复用1个既有低模型智能体只读核原目标链、当前native分支及本地merge。未编译、构建、执行框架/数据库/应用、联网、安装、提交或发布；官网9文件、1.0.2、HEAD及function-map保持。

[机器记录](p0-p1-repair-round91.json) · [源码补丁](p0-p1-repair-round91.patch) · [有限差异清单v20](p0-p1-difference-backlog-v20.json)
