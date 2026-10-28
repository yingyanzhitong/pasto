# 既有迁移完整度检查：第8轮

台账标记 **1,650 / 81,123 = 2.0339%**，部分迁移411。历史完整标记仍存在证据过期；不能用此比例代替Pasto整体功能完成率。

近期累计逐项对照 **261 个唯一地址**（总分母 0.3217%）：216 完整可复用、3 确定差异、42 待证。本轮新增 25 个唯一地址。

新发现临时图片清理 `0x100384e6c`：原版单文件读取属性失败会跳过并继续，当前整个循环退出。按原ARM证据将其从migrated改为partial；现有两个NSCoding键差异继续保留，产品源码未改。

另 344 条历史逐地址记录的原C和源码摘要未变且近期未判差异/待证，其中 281 条不在近期逐项清单；可优先复用旧审阅，不构成运行等价证明。

本轮未编译、运行、测试或发布。逐项见[汇总](batch-completeness-round8.json)、[本地化](batch-localization-completeness-8.json)、[数据](batch-core-completeness-8.json)、[图像](batch-image-completeness-8.json)、[窗口](batch-window-completeness-8.json)。
