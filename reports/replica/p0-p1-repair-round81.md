# 第八十一轮：Stack以出现次数排队，不按ID去重

批量检查Stack及OCR输入后，确认Stack重复项是新的有限差异。原08339c得到首条历史实体后，在方向选定的索引插入单个对象；089a18以同lower/upper范围调用0898fc，后者实际写新count和对象，没有按实体身份去重。08413c消费head范围0..1，08499c/084bc4按指定行仅减一个。绑定8个原函数及8条实际ARM指令，明确是源码/机器码证据，未执行原应用。

此前Pasto的addToStack在ID已存在时直接返回；同时Stack右键移除及粘贴成功使用removeAll，同ID项会被一起删除。本轮移除入队去重门，并让原生表格cell工厂同时传item和row；唯一生产调用者同步更新，捕获当时的有序expectedIDs。两个context动作和trailing行操作共用removeRow，只移除该索引，保留现有序列/回调revision保护、slideUp及高度更新顺序。context闭包弱持controller。

例如当前队列[A]再次接受A，原版为[A,A]，旧版仍[A]，本轮改为[A,A]；移除第二行后剩[A]。这是源码结构说明，没有运行Swift或UI。队首消费、反转、捕获订阅、插入/移除动画和Prefs数组逻辑保持；本地UUID队列持久化及stale-row保护仍是明确适配，不冒称完整原版内存实体生命周期。

OCR本轮只复用核对当前安全边界：识别async返回后的saveRecognizedDocument核expected image bytes，文本复制writer还会重新核图片字节，不编辑OCR/writer源码。这不构成完整OCR原函数等价或运行识别回归结论。

| 已确认有限差异 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 94 | 95 | 98.95% |
| 合计 | 163 | 164 | 99.39% |

v17保留v16全部163条/147组，新增并修复08339c重复入队这一有限合同。08339c整函数及完整Stack仍未完成；3544dc、Stack实体/Store值队列寿命、DI/模型替换、原UI分组选区producer和04430c/0f733c继续开放。不以该清单比例冒充全产品迁移率。

1232项Python源码/静态检查通过（新增16），覆盖实际入队、重复ID的数组及Prefs路径、cell工厂调用/声明参数、context及trailing动作的captured行、单行callback及revision门、原头/行删除证据、原有动画与OCR安全门不变，并核v17保留旧记录。3个旧测试/工具仅隔离6个精确增量，原证据摘要未改。首次1216项有25处旧形态/摘要失败，后剩1处Aux旧摘要，调整范围后最终全绿，日志保留。

245生产文件中3个修改、242不变，无新增生产文件、schema/Package/AppMain或预览样式更改。官网9文件和1.0.2/HEAD/function-map保持。未编译、构建、框架/数据库/应用运行、联网、安装、提交或发布；当前转入Stack批次继续核对，不把其他pending模块视为完成。

[机器证据](p0-p1-repair-round81.json) · [差异清单v17](p0-p1-difference-backlog-v17.json) · [源码补丁](p0-p1-repair-round81.patch)
