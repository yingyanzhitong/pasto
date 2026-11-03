# 第九十七轮：闭合有限实时实体提供者差异

本轮重新核对v20最后一条未修复记录3544dc的原合同及真实消费者。phase73时的缺口是FRC只发布ID/dirty IDs，UI按Store.items字典取DTO；此前多轮已接上当前context/objectID引用与原生handle。但Reference.item仍在实体查询成功后用try?执行ClipboardPersistence.item，导致内容投影错误被合并成lookup nil，选择消费者compactMap可静默漏掉有效实体。

现移除这两个含混的值getter。Reference.restoreItem只做current context existingObject查询、PastoItemEntity class check并返回强实体句柄；lookup/class错误才nil，不读payload。requiredRestoreItem复用同一optional getter，缺实体才trap。Entry.item、requiredItem和Snapshot.item(at:)都先取得对应handle，再由独立内容消费者投影；数组索引仍保越界trap。有效实体的内容错误不再被吞成“查不到条目”。当前resolvedItem仍沿既有内容失败fatal，不声称原完整decoder错误合同已还原。

7原片段、14ARM指令、5个真实ObservableCollection槽位、existingObjectWithID:error:选择器/动态cast及errorRelease导入和本机SDK头已核。14个真实FRC/普通搜索/渲染/选区/预览/编辑/Stack消费者方法摘要绑定，6个供给/通知方法及5份共享源码保持。独立只读复核确认：canonical3544dc有限liveprovider/optional-ID/required-index与实际消费者缺口现可关闭，完整函数/model/DI验证仍false。

1456项源码/静态检查通过，新增15项；旧1441项也已单独通过。3个生产文件修改，其余244个不变；6个历史测试/工具仅逆隔离5个精确hunk。首29失败/5错误、随后3失败/1错误为旧getter形态/摘要和直接读取断言，日志保留，未删测试或覆盖旧证据。

| 已确认有限差异 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 70 | 70 | 100% |
| 额外P1 | 97 | 97 | 100% |
| 合计 | 167 | 167 | 100% |

v21原样保留v20全部167条/151组历史记录，只为3544dc添加有限修复overlay，不增加分母、不改原片段或旧baseline。旧记录中“尚未迁移”描述是phase73历史状态，当前由修复overlay覆盖。

100%仅代表已经确认的有限差异清单。整体复刻未完成：完整payload解码/错误、原生实体schema及UUID/旧档/软删除桥、source/device/context/DI/ABI及跨进程寿命、optional不可用卡片、非文本观察/变更、分组通知、Stack失效/owner、完整选区manager及04430c/0f733c仍开放。全文迁移验证false、全范围百分比仍未知；后续继续这些真实未闭合合同，不重复已闭合记录冒计进度。

主智能体修改，复用1个既有低模型智能体只读独立复核。未编译、执行框架/数据库/应用、联网、安装、提交或发布；官网9文件、版本1.0.2、HEAD与function-map保持。

[机器记录](p0-p1-repair-round97.json) · [源码补丁](p0-p1-repair-round97.patch) · [有限差异清单v21](p0-p1-difference-backlog-v21.json)
