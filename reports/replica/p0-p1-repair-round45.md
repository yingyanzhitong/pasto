# 第四十五轮：P1 已完成索引状态恢复

新增原五字段Codable状态（schemaVersion/totalItems/indexedItems/oldestTimestamp/invalidItems），通过标准UserDefaults固定indexingState保存JSON，indexedStoreID单独保存String。模型不是闲置声明：真实启动、批次SDK成功和显式reset均已连接。

启动只在原已完成正常域尝试恢复：版本为5（OS26.4起6），旧/新来源均非nil且不同时拒绝，indexedItems>=totalItems且totalItems>0，再用原epoch query探测。结果非空继续使用状态，probe error按原分支也不认定索引丢失；结果为空才沿现有reset。健康恢复不读全量内容、不delete或重新index，继续安装history观察。probe await期间收到full delegate reset，会重新检查恢复许可，避免覆盖显式reset。

全量通过真实Store取ID字典，按timestamp降序、可选严格timestamp<before、不设request limit；nativeIdentifier外增加旧key fallback是Pasto兼容适配。取数后依原非空ID过滤计invalid，按100输入ID逐批live fetch、SDK普通flag=false写入，成功后按live.count推进、取该批最老有效Date并保存；未取消完成时原2ea410将indexed置total，缺失ID不阻止完成标记。定向flag=true链不改。取消/失败不会为失败批次推进状态，但现有needsReset错误策略仍与原不同。

**incomplete状态的oldestTimestamp续传尚未接入**：当前全量仍请求before:nil，不能宣称完整持久恢复已完成。原active/stop/wait、观察安装时机、query命名空间、weak SDK owner/ack、完整CoreData actor/FRC/实体/DI及typed-preview回退继续开放。

| 固定有限差异清单 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 42 | 81 | 51.85% |
| 合计 | 111 | 150 | 74.00% |

只关闭旧2f00dc的合法已完成/健康分支，不把模型/批次链的新增代码扩报为多个完整函数。剩39条已确认差异及2未知，所有full-function标记仍false。

731项源码/静态检查通过（新增17）。绑定28原片段、4真实selector/fixup、原state字段/Config keypath、健康query字节和writer数组捕获ARM；核对默认JSON键、状态门、原counter字段映射、批次成功/失败顺序、重置与await重入，以及明确Python分支fixture。Python fixture不是执行Swift或UserDefaults。修改3生产文件、新增1文件，229原文件未变；3旧测试只接当前批次入口、沿新helper检查availability顺序，或允许新增full-reset恢复标记，其余旧合同继续验证。首714有2旧源码断言/1旧定位错误，失败日志保留，更新后731全绿。

使用主智能体+1个用户已授权的低模型只读agent核取数及ARM；主审重新核验并校正回调数组/offset解释。确认2e1bac writer捕获完整SDK item数组，空textContent不从writer输入剔除；中间过滤数组用于诊断。寄存器restore在终结continuation分支，非writer路径。撤回此前待查的提交过滤疑点，不额外计分。

未运行Swift/ObjC/CoreData/CoreSpotlight、defaults、应用或迁移；未编译、构建、安装、联网、提交、推送或发布。官网9文件、版本1.0.2、HEAD及function-map不变。

证据：[JSON](p0-p1-repair-round45.json)、[补丁](p0-p1-repair-round45.patch)。
