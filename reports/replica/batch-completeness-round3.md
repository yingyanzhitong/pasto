# 既有迁移完整度检查：第3轮

函数台账标记 1,651 / 81,123 = 2.0352%，另有 410 项部分迁移。历史完整标记中的旧摘要仍须核对，标记比例不代表Pasto整体功能完成率。

截至本轮累计逐项对照 134 个唯一地址（总分母的 0.1652%），其中 116 完整可复用、2 明确差异、16 证据不足。本轮新增 33 个唯一地址，重复复核以最新有证据的结果覆盖。

- NSCoding 编码/解码两项存在原键 `data` 与现键 `dataByType` 的差异，保留为部分迁移。
- 图像元数据与动态颜色各有一个此前待证项补充原指令后完成对照。
- 搜索、绘制及窗口入口的部分业务分支相符；原执行器诊断或闭包边界证据不足，列待证。

本轮没有产品源码修改、编译、运行或测试。完整来源见 [机器可读汇总](batch-completeness-round3.json)、[快捷键](batch-core-shortcut-coding-completeness.json)、[图像](batch-image-completeness-3.json)、[窗口](batch-window-completeness-3.json) 和 [搜索文本](batch-search-text-completeness.json)。
