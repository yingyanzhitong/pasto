# 第五十九轮：强制重选同一分组

迁入真实Optional列表标识及消费者：同一非nil标识且force为真时先发送nil，随后始终发送目标标识。原03a900在nil时直接跳过解析，03a9fc在解析不到列表时不发布selectedList；当前消费者保留这两个门，不把nil解释成历史，不额外生成空collection。

历史使用固定非nil标识sharedPasteboardHistory。成功解析历史/UUID组后复用原有选择tail，取消删除、更新选择、安装collection的代码整段不变；普通tab/reveal/closed路径均到force true，失效组回退也使用真实标识流。搜索query/debounce和collection本体未变。

| v12有限清单 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 76 | 90 | 84.44% |
| 合计 | 145 | 159 | 91.19% |

本轮关闭039c50有限合同1条，余14条差异及2项未知。原持久标识wrapper/偏好、通用all-list实体解析、原列表模型及FRC/DI/ABI尚未完整迁移，不计完整父函数完成。

937项源码/静态检查通过，新增10项；13原片段与12条ARM字节绑定。5份旧测试跟进真实consumer或冻结历史证据继续核当前方法，初927的5断言/2定位及新937初始化定位错误日志保留，修正后全绿。2份生产修改、231份不变；官网9文件、1.0.2、HEAD和function-map不变。未编译、运行框架/应用、访问数据库、联网、提交或发布。

[机器证据](p0-p1-repair-round59.json) · [补丁](p0-p1-repair-round59.patch)
