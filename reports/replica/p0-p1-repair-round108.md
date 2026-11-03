# 第一百零八轮：预览分组菜单和默认创建

本轮迁移P1预览分组的实际消费者。07c378的VM+70构建时读取当前Item，用于原菜单状态；+a0→3c24a8/3c24b8则在同队列新建List集合、读取后释放，与列表3b8c94缓存集合不同。点击既有组后+e0→3c2ee0→3c4164/3c4304→3c3590重新读取VM的Published当前Item，以真实Writing+28移动到闭包强持的List目标。31原片段、20实际branch、7真实format6 VM/仓库指针与12ARM字绑定上述分界，不把构建时数组误当click写入对象。

Native预览菜单现在不以Store.items缓存记录存在为前提，每次创建并读取原生List集合，按当前native name/colorCode显示；勾选以菜单构建时input的type2 owner与目标native List相等为准，点击弱持header并读取self.input当前值交原生writer。header收到native观察事件时先更新当前handle，再处理删除或显示；legacy值菜单完整旧尾保留，其他5个header方法和6共享源不变。支持已证本地未共享组和既有canonical颜色，不据此宣称全部权限/任意损坏属性一致。

原+e8→3c36f0创建默认命名分组后调用分配，3c3790明确读取1c6aa4默认名称。本轮native分支先用同默认名称创建，再取当前预览项并分组，不再额外弹NSAlert命名。旧值接口保原modal；新建目标目前仍以返回的Pasto UUID解析回native List，完整原生返回/事务边界未闭合。

3生产文件、6精确增量，244生产文件保持；2历史测试工具只逆隔离本轮增量。既有1630项先通过；20项新检查首轮有1个测试使用固定100字符截断而漏掉完整to:board.id，已改为真实native分支边界，初日志保留；最终1650项Python源码/Mach-O静态检查全部通过。未执行Swift/ObjC/CoreData或应用测试，不能称实际功能回归通过。

移除菜单虽已读取当前handle，Store的nil-target仍落UUID适配，不能记为原生unassign完成。原VM+f0→3c3894/3c38e8→Writing+48→364094→363a3c已绑定，原primitive再以当前type2 owner进入36299c并处理孤立非历史删除；下一步沿此真实入口迁移。完整模型/DI、权限共享、fault/错误/owner以及两未知04430c/0f733c继续开放。

v31原样保留v30全部183条/167组，新增并修07c378菜单交接、3c36f0默认创建两个独立有限合同：P0 70/70、额外P1 115/115、合计185/185（100%）。该比例仅是已确认差异清单，不是Pasto总体完成率，没有完整函数升级。P2仍排除。

未编译、构建、安装、运行框架/应用/CoreData、联网、提交、推送、标签、发布或部署。9个官网/下载本地改动、版本1.0.2、HEAD和function-map保持。
