# 第九十八轮：原生文本预览直接读取ItemData

本轮继续P1文本读取父合同。原3c05d4从当前实体Item.data读取31b218解出的表示数组，只取首项，按flatRTFD/rtfd/rtf、同项plain、空文本处理，再更新original/editing两份模型。它不先读取整份ClipboardItem archive、来源应用、排序或时间元数据。原生文本Observer此前先用ClipboardPersistence.item投影全DTO，其他字段的投影错误会让有效原生正文变空或不再更新，确认新增有限依赖差异。

新增ClipboardItemObservation.attributedText直接读当前data/rawPasteboardItems，并复用原有codec和首项rich/plain helper。正文初值、同context通知和reload均接这一入口；native通知先更新当前实体，再更新文本基线。编辑中仍只更新两份基线，不覆盖当前输入；非编辑显示沿原尾部。旧DTO onChange仅在兼容客户端订阅时投影，未传原生源的legacy值入口保留。

原31b218的Ghidra结果删掉了getter异常分支；实际ARM b250检测Swift error，b3e0释放错误，b3e4/b3e8读取真实导入__swiftEmptyArrayStorage后返回。新raw getter桥只包raw字段读取，Item.data关系读取在外；捕获OriginalObjCExceptionError返回空文本，通知仍发生，避免保留旧正文。缺data/raw字段保留现有nil适配，不据此宣称原无效图行为已还原。任意坏字节/压缩完整错误和原诊断日志也未在本轮声称闭合。

1471项源码/静态检查通过，新增15项；旧1456项已单独通过。绑定12原片段、13实际调用、6指令、raw selector及empty-storage真实导入，9个提交/生命周期/header方法和7份共享源码保持。2个生产文件修改，其余245个不变。4个历史测试/工具只逆隔离8个精确hunk；首30失败/3错误、随后1个旧observer摘要断言失败日志保留，测试与旧证据未删除覆盖。独立只读复核指出异常时通知会被nil吞掉，主已改为空文本通知并重新检查。

| 已确认有限差异 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 70 | 70 | 100% |
| 额外P1 | 98 | 98 | 100% |
| 合计 | 168 | 168 | 100% |

v22原样保留v21全部167条/151组；新增3c05d4的“有效原生ItemData读取不依赖旧DTO/source/order”合同1条并修复，168条/152组。未据正常data域一致宣布3c05d4完整函数迁移。上层header/card/factory仍可能先做DTO投影；完整无效图/codec错误、原生实体schema/context/DI/ABI、非文本变更、分组通知、Stack失效/owner、完整选区及04430c/0f733c继续开放。有限100%不是整体复刻完成率，目标仍继续。

未编译、执行框架/数据库/应用、联网、安装、提交或发布；官网9文件、版本1.0.2、HEAD与function-map保持。

[机器记录](p0-p1-repair-round98.json) · [源码补丁](p0-p1-repair-round98.patch) · [有限差异清单v22](p0-p1-difference-backlog-v22.json)
