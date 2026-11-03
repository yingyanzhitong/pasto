# P0/P1 源码修复：第三十五轮

本轮对齐真实本地采集的原生内容→即时预览→来源→时间戳顺序。原360ff8先type/checksum，删除旧data、新建编码并关联data，再322504生成预览及31ed94写rawPreview；37b034随后调用来源字段更新，再交History更新时间。

Pasto现在从add进入同一事务worker，计算新checksum并匹配已保存值，准备实际Item。数据关系建立后才调用原有本地预览生成/编码器并写rawPreview，接着采样sourceProvider，最后通过同一repo的restoreHistoryItems逐项Date/setTimestamp。capture传入的preview提示清空以确保生成；普通手工值/导入和CreateItem路径保留原适配。既有单参数mutate只转发原policy给真实worker，不另开事务或提前保存。

实际被替换的目标ID保存在这一次repo上，通用保存仍强制apply相同值项，但不再次替换data；key、identifier、checksum和timestamp已等值时跳过重复setter。上轮通用结果selector移除，原生对象身份直接驱动后续保存。Schema及迁移目标定义没有变化。

补核3187b8真实结构名为LinkPreview，319778对应链接预览提供者；文件初始预览走312ae4→312874。不能把链接完成回调猜成文件异步预览。用户排除的联网预览仍不接入，本轮使用现有离线链接与本地文件/图片/颜色/文本元数据方法。

| 已确认有限差异 | 已修复 | 分母 | 比例 |
| --- | ---: | ---: | ---: |
| P0 | 61 | 69 | 88.41% |
| P1历史依赖 | 8 | 81 | 9.88% |
| 合计 | 69 | 150 | 46.00% |

本轮关闭旧360ff8本地即时更新顺序有限记录1条；余P0 8/P1 73共81差异及2未知。完整原实体子类/DI、跨进程context、重入/错误和entitySequence仍未闭合，Item.content也仍重复保存payload。完整函数迁移标记保持false，function-map不改；不把有限正常本地链升级为全ABI/字节/性能等价。

540项源码/原C/Mach-O静态检查通过，新增12项，14个原函数片段及3个预览类型descriptor/name绑定。3个旧生产文件变化、225个不变，无新生产文件。12个旧测试改为沿实际worker、原生Date或新同repo跟踪消费者验证；上轮完整文件增量证明在phase35-before冻结，新增检查确认其余Store方法和网络方法整文件可逆不变。初次528项中的8失败/14定位错误已作为工具观测摘要保留，原始首份日志未单独保留；当前540项全部通过。没有为满足旧的调用形态而恢复错误事件顺序。

未编译、构建、运行应用/框架、执行CoreData/迁移、安装、联网、提交、推送或发布；官网9文件、1.0.2、HEAD和function-map保持不变。下一步继续P0恢复/删除的实体序列与真实List消费者、剩余快捷键/采集边界；P1仍等待P0。见[JSON](p0-p1-repair-round35.json)、[补丁](p0-p1-repair-round35.patch)。
