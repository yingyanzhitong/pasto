# 第181轮：可空定位与菜单保留

2026-11-01。顺序P0修复→P1检查→P1修复；本轮P0共享源不变，P2/联网排除。

原03f574在协调器+58/+60安装041bc0→0407f8弱SearchBar定位回调。上下文2f78f8捕获弱协调器，2f8418→2f7e50读取回调。0407f8在owner或textLayoutManager缺失时返回OptionalCGRect.none；manager存在则layoutViewport，复用046e28并将editor矩形转到同SearchField，零矩形也是some。真实getter/布局/转换selector、nil/valid标志均由机器码绑定。本机SDK的NSTextView.h明确声明nullable/weak textLayoutManager，缺失是有效API状态。

原041190在非空行构建后先创建/复用菜单并保存，再调用定位回调；none只释放临时行并返回，保留旧菜单/旧行/回调/任务，第一次none也保留新建但未显示的菜单。此前Pasto把manager缺失和空行合并处理，直接关闭菜单，并且在定位后才创建菜单。

本轮由真实SearchBar安装weak可空定位回调，nil manager返回nil；Coordinator先保存菜单，再请求anchor，none直接返回，some零矩形正常交付。几何计算仍用原helper；原调用者多一次field→SearchBar再交给菜单的转换，当前沿同窗口field→window的等价坐标组合保持，不修改P2样式。几何移到owner回调后移除不再使用的editor参数和请求前读取；不增加Task/yield/全局owner回退。当前实际Task持有SearchBar及安装pair，未宣称任意旧协调器替换或私有context ABI全部同构。

2生产文件6精确增量，245份不变，247源逆恢复/旧快照幂等、354历史Python输入还原。11原片段、8完整机器范围、190直接分支、4真实weak/ARC导入及3真实AppKit selectors绑定；14邻接方法与11共享源保持。6条有限要求审计，新增18检查；84项定向及完整2680项源码/静态检查通过，审计后18项复验通过。3旧测试文件8精确调整可回放。

v85新增并修0407f8一条有限记录、1组，并给已有041190增加菜单定位保留合同，不重复增加函数分母。237记录208组/14额外完成合同：P0 81/81（100%），P1 156/156（100%），总237/237（有限100%）。这是已确认差异修复率，不是全部原函数或模块迁移完成率。0f733c仍未知，剩余正常菜单show/keyboard及真实context消费者继续核对；不把私有布局或名义上的optional分支当作新功能缺失。

官网9文件、版本1.0.2、HEAD及function-map保持。未编译、构建、安装、运行应用/框架、联网、提交、推送、发布或部署。
