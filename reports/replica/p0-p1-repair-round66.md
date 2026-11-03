# 第六十六轮：Stack 原始类别图标与实际消费者

实际Stack cell imageProvider已去掉来源应用rawIcon及通用SF图标，按托管Item.rawType读取原0..5域：文件3→icon.file，颜色2/文本5→icon.text，链接4→icon.link，未知0/图片1→icon.unknown。原imageView可选→设置image→textField两行→snippet文本的既有顺序保持，named资源缺失按原失败分支处理。UUID查询是现有模型适配，缺记录/查询错误显示unknown，不冒称原实体/ABI完整迁移。

四种图标原先不是独立PNG，而是CSI INLK链接到压缩灰度图集。本轮用独立Python工具静态解析BOM变量/单叶树、显式atom键和crop矩形，提取四个facet、八份1×/2×记录及三块必需图集。所有保留rendition、key和atlas原字节一致；不解码或重编码像素，尺寸20px/40px、灰度及template标志保留。原2,850,696bytes完整目录只在忽略的.local，独立子目录为43,032bytes，置于自有BNDL中由SwiftPM复制、通过Bundle.module查找，再按asset name加载。原素材不属于MIT，NOTICE已说明。

| v12有限差异清单 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 89 | 90 | 98.89% |
| 合计 | 158 | 159 | 99.37% |

关闭0519f8的有限图标provider/资源缺口，不代表整个Stack cell/Nib/窗口完成。剩FRC365e18，另有未知04430c/0f733c；完整父合同继续partial。现有24pt imageView和44pt行是此前Nib适配，本轮未改变或计作原布局验收。

1023项源码/静态检查通过，新增16项；绑定四原片段、四条真实smallString、两个selector、九条ARM指令、REA原目录SHA。纯Python重现与资源文件/manifest逐字节相同；检查BOM范围/计数、所有INLK键/crop、像素块一致性、1×/2×元数据、缺atlas失败、独立包与实际消费者。一项旧测试改为冻结历史hash并核对实际原工厂，初1007检查的三处旧整文件/编辑集合断言已留日志。低模型只读复核独立重现相同资源，无可证错接或缺引用。

3份生产修改、3份新增，232份不变；SwiftPM只增加copy资源，NOTICE记录素材边界。官网9文件、1.0.2、HEAD、function-map不变；未编译、运行CoreUI/AppKit/SDK/数据库/应用、联网、提交或发布。静态BOM/字节一致与接线检查不等于运行时加载或肉眼像素验收。

[机器证据](p0-p1-repair-round66.json) · [补丁（含资源二进制补丁）](p0-p1-repair-round66.patch)
