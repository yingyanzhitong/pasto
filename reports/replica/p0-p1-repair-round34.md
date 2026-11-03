# P0/P1 源码修复：第三十四轮

继续先修P0，再检查P1，最后修P1。本轮将原360ff8的数据实体替换接入本地存储，完整父合同仍partial，**不增加已完成记录**。

新增真实ItemDataEntity/rawPasteboardItems，Item.data为必需单关系、Cascade，反向item可选单关系、Deny；本地Item增加rawType/rawPreview。实体定义和原v10.mom静态资源逐项比对。替换路径依次写类型/摘要、删除旧data、新建编码data、关联，再存已准备好的预览。repo复用同一事务context，不拆开保存或重置。

真实采集的结果ID交给同一次commit，作为强制apply/replacement输入；即使内容值相等也会替换原生数据。普通时间戳恢复没有该输入，payload相同且data存在时仍跳过原生数据编码和旧content编码。读取真实rawPasteboardItems及rawPreview，保留有序类型、旧多项/原始容器和OCR旁路字段；相同的旧JSON/type-order字节直接保留，变化时用稳定JSON键排序，避免读取本身造成多项值反复变化。

五个旧schema均显式关闭新图以保留旧model hash。inferred mapping只给Item设置迁移policy，在关系创建阶段填好必需data，再由NSMigrationManager验证并保存临时目标；成功后才replace旧库。policy仅读sourceContext，旧content、UUID、nativeIdentifier和组关系不改写，已存raw容器字节优先原样放入新data；旧imagePreviewMetadata可转换为rawPreview。没有通过把data设为optional来掩盖必需关系。

| 已确认有限差异 | 已修复 | 分母 | 比例 |
| --- | ---: | ---: | ---: |
| P0 | 60 | 69 | 86.96% |
| P1历史依赖 | 8 | 81 | 9.88% |
| 合计 | 68 | 150 | 45.33% |

仍剩P0 9/P1 73共82差异及2未知。预览生成仍在ClipboardStore值层发生于原生替换之前；source采样、Date/清理与原实体Sequence/DI的完整交接尚未完成，值metadata也仍复制保存payload。360ff8不升级为完整，function-map不改。下一批继续同一事务的原生内容→预览→来源/时间调用顺序，不能用新关系存在冒充完整父链。

528项Python源码/原C/模型资源/SDK声明静态检查通过，新增12项。初始旧测试因新callback默认闭包和旧调用/schema字面定位失败；callback采用与现有policy一致的可选nil形式，9个旧测试精确接新形态或将旧整文件增量检查绑定phase34-before，旧顺序/错误/保存检查保留。首份失败日志保留。新增1生产文件，修改3旧文件，224旧文件未变；Store通过精确撤去本轮callback接线还原到基线的检查，其他功能/网络方法未改。

必需关系inferred migration、实际Deny/Cascade、原生读写往返、Swift类型检查和应用性能没有执行，静态通过不能据此宣布成功迁移了用户存储。未编译、构建、运行应用/框架、安装、联网、提交、推送或发布；官网9文件、版本1.0.2、HEAD及function-map不变。见[JSON](p0-p1-repair-round34.json)、[补丁](p0-p1-repair-round34.patch)。
