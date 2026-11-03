# 第四十轮：P1 搜索回调顺序和原生分组候选

输入变更现在先保存内部节点，再按恢复标志决定是否写历史。需要正常化时按原builder→display/range→publish→清建议执行；不需要正常化则保留允许编辑的返回值。撤销/重做在设置恢复标志和内部节点后，构建/显示原选择、发布、清建议，最后复位标志；nil snapshot仍无副作用。实际shouldChange及Undo/Redo回调保持接线，Pasto用于表示“已处理”的Bool和IME保护保留。

分组候选复用P0已有ListEntity图，直接发NSFetchRequest<NSDictionary>，读取identifier/name，rawType==2；非空query使用原MATCHES[cd]正则，按name升序；仅缺失或非String字段的行丢弃，空组、重名及空String不额外过滤或去重。取数错误沿真context→Persistence→Store→UI provider传播，由已有建议器逐组catch处理。筛选弹层在其呈现边界将这组错误折空；其完整原异步availableFilters/DI父合同继续开放。应用和设备候选仍待迁移。

| 已确认有限差异 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 19 | 81 | 23.46% |
| 合计 | 88 | 150 | 58.67% |

关闭5旧记录：7370、7c14及30e6bc/30f3c0/2dfe58共用查询链。共享三记录不是3个新独立bug。剩62差异及2未知；完整Swift ABI、原DI/optional-source为空的初始化时机、跨进程/重入和完整模块未验收，不是全函数完成率。

641项源码/静态检查通过（新增18、另纳9个已有检查）。绑定21原函数片段、既有callback-slot证据和3个真实ObjC selector：从原二进制ADRP/LDR读取selref并验证format6 fixup链可达，分别为setResultType、setPropertiesToFetch、setSortDescriptors；本机SDK字典结果raw2。没有执行数据库、AppKit或原应用。

修改6生产文件、224个未变，模型/迁移和恢复事务未改。5个旧测试仅把历史整文件/摘要/旧内存predicate证据绑定修前快照，当前关键方法继续检查；新的查询/回调测试检查实际生产方法。首次614出现7处旧全文/摘要断言；扩展641还有1处旧内存predicate引用，失败日志保留，按新的真实来源更新后通过。快照脚本遇只读SDK绝对路径后中止，已跳过外部文件并按既有摘要补齐快照，SDK未修改。

官网9文件、版本1.0.2、HEAD与function-map不变。未编译、构建、安装、运行应用/原生API、联网、提交、推送或发布。继续应用/设备候选和索引投影/生命周期。见[JSON](p0-p1-repair-round40.json)及[补丁](p0-p1-repair-round40.patch)。
