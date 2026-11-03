# 第一百六十三轮：原生分组读取补齐与实时标签待修

继续P1实际消费者，确认此前全P1并未完成：当前菜单读取原生List集合，但PanelViews.boardTabs与选择installListSelectionDelivery仍从store.pinboards兼容缓存解析。原TabBar的ListCollectionViewModel lazy lists通过0cec3c和ListsRepository witness+10走367f78，按List默认请求创建原生FRC；menu则是另一+18槽36805c→36c094，额外设置rawType2。已经绑定三个真实fixup指针和原构造调用，不能将菜单源已迁当成原全List标签流已迁。

本轮先修共享读取的具体缺口：原生List存在但没有Pinboard兼容实体行时，原project只遍历兼容行，丢失原生组。现保留已有行的映射/原生字段覆盖和缺native fallback，补入未删除、rawType严格2且标识可映射UUID的缺失原生组，取原生name/rawAttributes/metadata.index，再按已有sortOrder及UUID tie规则排序。现有重复兼容ID不被去重，仍由Store.validate拒绝；只避免重复补入同ID新组。不写数据库、创建兼容行或改动原生字段。

继续保留Pasto值API的UUID范围及非原生colorHex默认（#FF9500）；有效原生rawAttributes仍优先，nil/无效颜色显示不冒原版全状态一致。history与其它rawType不在“新增普通本地组”补入范围，已有兼容未知type及fallback不改。这只是read/reload桥修复，实时tab/list publisher、history顺序/名称、原生选择和重命名/颜色/删除/排序输入仍要迁；不把刷新后能读到等同即时流完成。

1生产文件1完整方法增量，246文件保持，247逆恢复通过；6创建/邻方法与5个真实UI/读者/集合共享源逐字保持。绑定12原函数片段、三protocol指针及两原构造调用；新增8项定向检查，完整2428源码/静态检查通过。初次唯一旧“project不变”摘要失败，精确隔离本轮方法后通过；2旧工具/测试3模式4替换重放绿。新测试直接检查当前补入门、字段、无写入及尚未迁移的实际UI门。无CoreData或UI执行，不冒运行回归。

v69新增一个367f78已确认差异记录并保留pending，225条已有修复不撤回；现226记录201组，额外合同仍12。有限进度P0 81/81（100%）、P1 144/145（99.31%）、总225/226（99.56%）。分母增长来自发现新差异，整体迁移完成度仍未证；04430c/0f733c两个未知保留。

下一步按同一原生链接全List publisher与持有对象的标签消费者，核03a538 selectedIndex/集合删除后邻近选择，再改动作输入。具体计划存本地phase-163/native-tab-migration-plan.json。所有改动只留本地，版本1.0.2、HEAD、function-map和官网/下载九文件保持，不编译构建安装运行、联网、提交推送发布。
