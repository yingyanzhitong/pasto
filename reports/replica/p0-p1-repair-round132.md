# 第一百三十二轮：P1 内容读取错误诊断与编辑提交复用

执行顺序保持：P0 已确认差异源修复阶段收口 → P1 当前入口检查 → P1 确证差异修复。没有跳回 P2 或联网模块。

本轮修复原 3724f0 的两条具体本地诊断：读取对象抛 NSError/Swift Error 时，使用该索引记录持有的命名日志器，以 level 2 记录 `Failed to load item content: ` 与 localizedDescription 后返回 nil；取到错误类型对象时，以 level 2 记录原 object-not-found 文案后返回 nil。日志器名为原二进制真实字符串 `init(_:coordinator:)`，不是推测的实体名；构造返回、闭包捕获 +0x20、两层转发与 d4df0 的 level 2 均绑定实际 ARM 指令。现有实体名校验仍是原 dynamic-class cast 的本地模型适配，不声称 Swift ABI 相同。

只有 content() 给共享 read 传入此诊断对象；imageData() 保持旧默认入口。原始数据 getter 的既有共享 decoder、some([])→typed fallback 及外层 fetch 以外的异常处理保持；并未把所有异常都改成原 fetch-error 日志，也未接入独立网络遥测。

继续检查发现：原3724f0在 decoded representations 为空时还有 raw-size/prefix/types 的 level 2 诊断；primary-empty typed-preview 路径另有包含 previewLength/usedPreviewFallback 等字段的详细诊断。当前仍缺这两条，已明确登记待修。后者文案说 empty 不意味着最终返回必为空，不会据此错误抑制成功 fallback 的诊断。详细字段及完整触发门下一步继续对照。

文本编辑保存上层按原证据复用：先关闭编辑状态、提取编辑器内容并提交，再刷新原内容；外层内容 commit 后才恢复预览头、隐藏编辑头、发 false 状态及结束回调。不会凭“保存失败应留在编辑态”的主观假设改动已一致顺序。绑定六个当前未变方法；不把有限顺序一致冒称完整 VM、Undo、观察或错误父合同完成。

1 个生产文件、4 处精确增量，其余246文件不变。11原反编译片段、17真实ARM字、5二进制字符串及6复用方法绑定；2074项源码/Python/Mach-O静态检查全部通过，新增12项。两份历史测试/工具只加5处精确逆隔离，旧proof保持；新增测试直接检查当前生产实现。未编译、构建、安装或执行应用/系统框架。

有限差异清单仍是201函数记录、179组。因同一旧函数新发现两条待修诊断，仅重开该函数一次：P0 77/77（100%），P1 123/124（99.19%），合计200/201（99.50%）。这是已确认有限差异修复比例，不能代表全P0/P1或全部原函数迁移完成度；两个未知地址继续保留，整体迁移率未知。

版本1.0.2、HEAD、function-map、官网及README下载链路的9份既有修改均保持；未联网、提交、推送、发布或部署。所有修复留在本地。
