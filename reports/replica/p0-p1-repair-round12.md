# P0 → P1 源码修复：第十二轮

| 范围 | 已修有限差异 / 固定差异分母 | 进度 |
| --- | --- | --- |
| P0 | 40 / 64 | 62.50% |
| P1（P0依赖） | 5 / 81 | 6.17% |
| 合计 | 45 / 145 | **31.03%** |

新增计分仅为 `328bb4`、`328bc8`、`3293c4` 三条已证有限差异。仍有100条差异和2个未知入口；不是全函数或产品完成率。旧比较结论覆盖654/656（99.70%）不计作代码修复完成。

## 本轮实现

新增实际本地 `ListEntity`、`ListMetadataEntity` 与 `Item.list` 关系。List.metadata使用Cascade，反向metadata.list使用Deny，List.items与Item.list双向Nullify。元数据包含真实排序index。Item仍保留Pasto兼容实体与字段，不直接装载原厂整个模型。

实际首项查询使用ListEntity、可选predicate/sort、metadata.index默认升序，以及limit1、offset0、batch20；返回首项或nil，错误向上传递。history固定标识和分组owner都有真实消费者，刷新对象是List托管对象。

容量从实际history.rawAttributes读取。nil/损坏/非clipboard在过期处理时不当作30；成功解码的clipboard缺capacity才默认30。界面显示的fallback与过期分支分开；新建本地历史仍保留用户要求的一周默认值。正容量按checked Int乘天数后构造Date(timeIntervalSinceNow:)；相应原Foundation导入已核实。

恢复和采集在修改/清理后、条件save前重新first-fetch历史List并refresh(mergeChanges:true)。正常空恢复提前返回；native历史删除空序列仍走刷新，分组上下文删除不刷新，动态上下文只读一次。完整原Sequence/tagged分支、可选timestamp及事务父链仍保留partial，不据此升级父地址。

## 旧数据与验证边界

识别三种无List的旧模型，先迁入临时存储再替换；图填充只新增List/Metadata、owner关系及revision，不重写旧内容blob或额外成员关系。ClipboardPersistence构造已受Store现有文件锁保护，图填充在同一context事务保存。已存在history是正常填充完成标记；外部造成的部分图尚无自动修补策略。

305项Python源码与原始数据静态检查通过，新增20项。修改3个旧生产文件、新增1个实际接线组件，其他220个与本轮备份一致。7个旧测试随模型候选、refresh参数和capacity参数更新；旧全文件冻结绑定本轮before副本，并逐字核对未改的通知方法，保留原顺序与保护断言。旧报告不回写。

两个子审保留较早checkpoint；根审另外核对最终去除冗余fetch、checked Int日期运算、可选回调参数和按名称查找Item实体的改动，最终文件摘要绑定于本轮记录。

未编译、运行Swift/CoreData、迁移真实用户存储、联网、提交或部署。inferred mapping、关系删除规则及dirty List的refresh合并效果未做运行验收；静态检查不代表实际迁移成功。版本和全函数台账不变；官网、README及Actions下载链接修复继续仅保留本地。

[完整记录与源码绑定](p0-p1-repair-round12.json) · [源码补丁](p0-p1-repair-round12.patch)
