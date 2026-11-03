# 第四十三轮：P1 原生延迟索引记录

原371998构造SearchableItemEntity时保留content/imageData闭包；faafc/fc0ec/37582c复制记录不求值，e3ce8到SDK序列化才调用content并截前5000。本轮新增ClipboardSearchRecord携带这九项业务能力，Entry只保留记录及转发字段。实际Store的全量、history和定向SDK写入均走searchIndexRecords：从原生关系读app/device可空名称、timestamp、rawType及唯一owner（仅rawType==2）的identifier，分组key不再多值，nil序列化为空String。类型名按原版保留Unknown/Image/Color/File/Link/Text。

闭包只捕获reader，reader只持coordinator、objectID与构造时kind；每次求值新建private context（原并发类型raw1，已用本机SDK验证），performAndWait中按ID取当前对象，再解码其ItemData。正常text/unknown逐项compactMap plain string并按原序空格连接；正常文件内容按全部URL.path空格连接，链接按首URL.absoluteString加可选已存preview.name。图片记录content=nil、imageData独立读取，移除此前猜测的预注OCR文本，OCR识别/编辑源码本身未改。

Pasto已有title/local UUID/cache版本仍从旧值记录适配，未改schema或存储内容。完整typed-preview空文本/富文本、预览损坏/诊断/错误树继续保留原有plainText适配，尚未迁移完成。SDK空内容筛选、整体OCR/indexer、持久状态/availability/owner/ack/FRC父链继续开放。闭包/实体/Swift ABI与运行中的跨context/故障/临时ID/释放行为未验收。

| 固定有限差异清单 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 38 | 81 | 46.91% |
| 合计 | 107 | 150 | 71.33% |

关闭8条旧共享投影/延迟合同：2faafc、2fc0ec、371998、371e9c、3724f0、375210、375244、375274；3724f0旧记录只涵盖正常非空多文本。共享调用链不是8个独立bug；所有完整函数标记仍为false。余43已确认差异及2未知。

692项源码/静态检查通过（新增22）。绑定23原函数片段、existingObjectWithID:error:实际selector/fixup链及SDK私有队列枚举；核对真实Store消费者、复制不求值、按ID新context读取、所有元数据/键、5000截取顺序、空String与nil，以及ASCII多文本/缺值/空项/重复项反例。Python语义fixture不冒充Swift或原生执行。修改3生产文件、新增1文件，228原文件未变；3旧测试接当前record facade，或冻结历史整builder/投影证明，当前flag断言保留。首次670有4旧源码形态断言失败，其工具结果及说明可追溯；修正后692全绿。

未运行Swift/ObjC、CoreData/CoreSpotlight、应用或迁移；未编译、构建、安装、联网、提交、推送或发布。官网9文件、版本1.0.2、HEAD和function-map不变。

证据：[JSON](p0-p1-repair-round43.json)、[补丁](p0-p1-repair-round43.patch)。继续P1搜索与筛选。
