# 第七十八轮：从实时条目读取原生来源应用

继续P1修复。上一轮已经把实际双击、回车、Command-V输入改为持有实体跨权限弹窗，但实体投影仍从旧content取得来源应用标识，sourceApplication(for:)又按标识读取Store旧记录。这使实时内容路径仍可能混入另一份来源快照。本轮针对这条共享读取路径修复，没有扩至P2。

原38222c在处理选中实体时直接调用sourceApplication，再取bundleIdentifier；原383df4图片恢复直接取该关系的name。两处均有明确nil关系分支。绑定3原函数片段、6条ARM字、3个真实ObjC selector及dyld链，原MOM的可选关系、必需bundle/name/rawColor和可选rawIcon同时复用冻结证据。

共享ClipboardPersistence.item现在从传入的同一个原生对象读取关联ApplicationEntity，投影当前bundleIdentifier/name/rawIcon/rawColor。只读快照附带“已读取”标记，用于区分原生关系为空和旧值记录没有读取原生关系。实际sourceApplication(for:)先返回该快照，包括nil；只有没有原生快照的旧值记录才走原Store查找。required字段错误使用本地损坏文件错误适配；不冒称原typed实体ABI相同。

恢复processor的来源bundle ID、图片恢复的sourceName，以及实际卡片图标/颜色均复用这个getter。原writer、事务、保存失败Undo/通知和权限/焦点流程未改。设备关系和完整模型依赖仍待审，没有顺带重写。

两个新属性只供读时使用，不参与Codable；显式CodingKeys静态确认恰好覆盖之前23个存储字段。content比较及编码前清除两属性，防止关系快照引起无关payload重编码。这是源码字段与路径检查，未执行Swift编解码或真实数据库迁移。

| 已确认有限差异 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 93 | 94 | 98.94% |
| 合计 | 162 | 163 | 99.39% |

3544dc仍未关闭：完整实时列表成员/metadata、primary和其他持久化或ID动作调用方，以及完整device/entity/DI/模型切换仍需证据。04430c、0f733c继续未知。批量核对发现分组动作从visibleItems重建选区的候选，但原动作消费者未完整对应，未猜改，也未新增已确认差异计数。

1179项Python源码/Mach-O静态检查通过（新增15）；验证当前真实消费者、native nil权威性、旧值兼容、颜色位保真表达式、原归档字段集合、内容比较排除临时值及其余生产源码保持。5处历史测试/工具仅隔离本轮5个精确新增块，原证据摘要均未改写。初1164项中的19个旧结构/hash失败日志保留，最终全部通过。

244个生产文件中4个修改、240个不变，无新增生产文件、CoreData模型或UI改动。官网9文件及1.0.2/HEAD/function-map保持；未编译、构建、框架/数据库/应用执行、联网、安装、提交或发布；目标继续进行。

[机器证据](p0-p1-repair-round78.json) · [有限差异清单](p0-p1-difference-backlog-v16.json) · [源码补丁](p0-p1-repair-round78.patch)
