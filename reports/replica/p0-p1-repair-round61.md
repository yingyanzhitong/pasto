# 第六十一轮：可选候选数据源与真实服务消费

启动时由store factory捕获实际ClipboardPersistence/context构造本地候选源，并安装到searchIndex的可选属性。筛选任务现在经过UIState→index→core聚合，再把返回的nodes交给View，不再直接预读store或无条件生成类型候选。

原版按type、app、device、date、group顺序读取；四次重读可选provider，callback重入时能替换或移除后续源。缺源返回空候选，日期仍在；源抛错只省略对应字典key，后续继续。主审从ARM确认C反编译删除的四处错误分支：释放Swift错误、置空结果、合流继续；2e0a08对nil输入删除key。两日期边界使用FCVTZS向零取整，UI继续保留截断后合法的空range。

复用既有应用/设备/分组的托管查询、排序、distinct、非空过滤和错误传播，不新增内存fallback、日志、reset或save。原DI ABI、完整AppDelegate、SDK owner/ack/FRC和列表观察仍未闭合。

| v12有限清单 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 80 | 90 | 88.89% |
| 合计 | 149 | 159 | 93.71% |

关闭07d0e0本地注册和2e00a0聚合两条旧有限记录，余10条差异及2项未知。不是完整原函数迁移率。

957项源码/静态检查通过，新增12项；11原片段、26ARM字及既有DI metadata/witness、托管查询证据绑定。5旧测试跟进真实服务或冻结历史文件后继续核当前相关方法；初945十处旧位置/hash断言和956改进前日志均保留，最终957通过。

5份生产修改、228份不变；官网9文件、1.0.2、HEAD和function-map不变。未编译、运行框架/应用、访问数据库、联网、提交或发布。

[机器证据](p0-p1-repair-round61.json) · [补丁](p0-p1-repair-round61.patch)
