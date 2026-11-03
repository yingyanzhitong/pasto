# 第一百二十一轮：选区发布的真实接收者

继续P0，尚未切换P1。本轮对上一轮“0679ac→0f2b18的Published接收者待证”取得新的绑定证据，没有新增推测性生产代码。

0679ac按已应用索引取得可选Item，跳过nil并按输入顺序收集identifier。结尾067c44调用DI resolver 0da768，067c48从stack+0x38重新装入x20，067c50才调用0f2b18。因此setter接收者是DI返回对象，不能把x20保存寄存器误认为原ItemCollectionView。只读子审起初作了该误判，主用真实ARM反证纠正后，子审已撤回。

keypath的signed-relative指针和symbolic type reference独立定位到ActiveSelection类型descriptor及名称；stored-wrapper keypath指向fae028，原生ivar元数据把同地址命名为_itemIdentifiers，projected getter也使用同一ivar元数据。由此确认实际发布的是ActiveSelection的identifier数组。

其projected publisher进入0b0b20的Combine组合/过滤/去重/sink管道，cancellable保存在接收对象+0x60；但最终sink closure函数指针和Output类型尚未绑定。相邻0b11ac即使形状相似，也不能据此接入。尚不能称该值等于复制OSD或本地UUID状态，继续保留具体待证项。

另保存采集查重的当前事实：latestState在revision不变时返回baseline，state再经本地/远端merge；recordCapture按state.nativeChecksum匹配后按UUID准备实体，原3214c8则构造checksum谓词并进入fetchLimit=1的原生查询。实际输入可达性及原fetch错误域尚需绑定，不把“代码不同”自动计为新bug，也不删兼容content或旧多组成员。

新增10项检查，合计1896项源码/Python/Mach-O静态检查全部通过。12原片段、7相对指针、2真实链指针、8ARM字和2调用目标已绑定。本轮247生产文件与243历史测试工具全部保持，无源码修复计数增长。v38保持P0 73/73、P1 124/124、总197/197（100%），仅代表已确认有限差异，整体P0仍未闭合。

继续按P0修复→P1检查→P1修复执行。未编译、构建、安装、运行、联网、提交、推送、打标签或发布；官网9文件、版本1.0.2、HEAD与function-map保持。
