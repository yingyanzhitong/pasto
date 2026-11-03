# 第六十九轮：分组上下文类型与未知类型回退

复查父合同发现：此前3b80f0有限比较仅覆盖正常History/Pinboard选择；真实Pasto board选择将所有已解析记录无条件当普通组。原版rawType2保留相同标识为Pinboard，rawType1保留相同标识为History，其他类型先记录诊断，再惰性调用History provider并返回History tag。本轮补上这一已证分支。

新增OriginalCollectionListContext枚举并接入实际选组subject的sink。helper保留两种正常case的输入标识，不支持类型只在记录本地日志后调用fallback closure；不复制网络遥测。UI将pinboard映射原UUID、history映射既有nil历史路由，原nil/未解析事件、强制同组重选及applySelectedList尾部不变。

类型来自真实生产链：托管ListEntity.rawType Int64→project的Int16(exactly:)或0→Store发布pinboards→选组sink。1/2与unsupported三种分类不会被溢出截断混淆；旧数据nil仍按此前适配规范成2。任意64bit溢出原数值日志无法保留；任意非canonical History标识/metadata在UI仍经本地nil适配，完整ListContext/模型/DI/ABI没有因此闭合。

| v13已确认有限差异 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 91 | 91 | 100% |
| 合计 | 160 | 160 | 100% |

v13逐条保留旧159记录与143组，补纳并修复3b80f0未知类型回退1条，现160条/144组。组数不是独立bug数，也不作进度分母。该百分比只表示有限已确认差异已修，不是原版全部函数或完整P0/P1模块完成。

两个未知继续保留：04430c的coder字段默认值、原ObjC bridge和当前同NSTextView super decode均可见，但真实归档输入/对象图和兼容消费仍未闭合。0f733c可证String桥接和setString副作用；机器码末尾mov x0,x21、B到已绑定objc_release，无写常量0，不能采信Ghidra return0为Int返回值。子审最初照伪码称Int0，主审据机器码纠正并获其撤回。未找到直接调用及常见指针不等于不可达，当前也没有生产调用，返回ABI/原间接消费者继续未知。

1067项源码/静态检查通过（新增13），绑定12原片段、2真实selector、13条ARM字和objc_release导入；测试核全Int16域及64位溢出的分类、诊断→惰性fallback、实际UI消费者/默认兼容、仅新块改变、v13旧记录保留，以及错误返回值推断的机器码反证。4旧测试按实际新类型块作segment比较，保留初5处旧hash/整方法断言日志。子审只读复核未发现有限类型/回退错接，不等运行时功能回归。

1生产文件修改、1新增、239不变；没有模型/存储/schema改动。官网9文件、1.0.2、HEAD和function-map不变；未编译、运行框架/数据库/应用、联网、提交或发布。目标保持进行中，下一项为一般history/group集合provider与标识/metadata的数据源对照，不反复重扫两个未知凑完成率。

[机器证据](p0-p1-repair-round69.json) · [有限差异清单v13](p0-p1-difference-backlog-v13.json) · [本轮源码补丁](p0-p1-repair-round69.patch)
