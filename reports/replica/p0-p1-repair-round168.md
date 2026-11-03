# 第一百六十八轮：原生List编辑事件与创建后编辑交付

保持P0修复→P1检查→P1修复。本轮沿039618→03baf8→03b4c0及0243ec菜单事件，补齐实际标签消费者099740/099838→09aafc→08c35c。原版0.2秒延迟后发送所创建的同一List，只有owner是weak；没有Pinboard兼容缓存存在/UUID/已删除判断。旧Pasto的缓存前置门和持久字符串token请求与此不同。

## 当前实现

创建结果经ClipboardPinboardTarget.listTarget保留同一nativeObject，延迟闭包显式强持target、weak self，直接发送PassthroughSubject。右键重命名使用同一原生事件。移除tabRenameRequest的Published字符串/UUID token状态，缺项事件不会保留到未来重放；旧label beginRequest配置接口只保展示/测试兼容，应用生产路径传nil。

Toolbar在初始配置后安装订阅，Cancellable由视图持有，weak owner并在MainActor同步交给tabBar；dismantle时取消。每个实际tab/cell保存原生target，消费者按NSManagedObjectID相等找到已有cell，缺项直接返回；不再用identifier/UUID或Store.pinboards找编辑目标。原机器码09aab4明确把099838作为回调传给弱owner包装。

找到cell后先清TabBar window的firstResponder，再按frame(-17,0)滚动0.15秒；动画completion强持cell，调用原有label.beginEditing。0.2/0.15常量、-17指令、实际ObjectID/数组lookup/动画调用和completion目标已绑定。原label configure/begin/cancel/commit、创建/改名/颜色/删除/排序等15方法逐字复用；没有重写编辑器或样式。

未用颜色优先保留用户指定策略；原324a80是八色随机。当前palette、原生typed创建、Store策略及原生列表读投影保持，不把用户适配说成原版行为或给它新增完整函数计数。

## 检查与剩余

22原片段、74实际调用、8完整机器范围及3真SDK导入（Subject.send、asyncAfter、weak load）已绑定；6生产文件17处精确增量，241文件保持。247生产文件逆恢复、历史输入幂等及7旧测试/工具12模式重放通过。新增12项直接检查当前源码/机器码，完整2489静态检查通过。首7失败是旧token/缓存门及旧方法摘要；定向104项余1旧菜单断言，均留日志。历史boardButton仅对完整精确方法体做逆恢复，不把{}全局替换；新测试直接核当前事件，不逆成旧路径。

未编译或执行AppKit/CoreData/Combine，不称真实动画/窗口或功能回归通过。Pasto target包装、native cell查找仍为自有applier适配，完整布局、ARC和框架重入保留父合同。原097828末尾1b9460乐观数组移动已定位为remove(source)→insert(min(destination,count))，但必须核清数据订阅与占位拖放的先后，避免当前同步metadata更新后再重复移动；本轮未猜改。

v74仍226记录201组/12额外完成合同，367f78只追加部分跟进。P0已确认差异81/81（100%）、P1 144/145（99.31%），合计225/226（99.56%）；两unknown04430c/0f733c和整体完成度继续开放。

版本1.0.2、HEAD、function-map及官网/下载九文件保持，仅本地修改，不编译、构建、安装、运行、联网、提交推送或发布。
