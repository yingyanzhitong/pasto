# 第179轮：搜索建议任务的实际owner与取消收尾

2026-11-01。顺序仍为P0修复→P1检查→P1修复；本轮未新增P0差异，P0共享源保持。

## 原链与修复

真实async descriptor c255a0指向041cc8，再进入040e34→040ec4。040ec4在MainActor弱读原SearchBar，nil不进入请求；非nil将同对象存入任务帧+0x38，子请求040fc0→041058→0410ec→041190完成后，040f44从帧取同owner并objc_release。Ghidra040f44未显式打印该release，但真实指令和导入已绑定。

Pasto此前任务弱读coordinator、field、editor，未持有实际SearchBar；即使这些对象仍存在，实际owner可能已消失。现configure在首次与更新两分支设置弱suggestionOwner；Task只弱读同SearchBar，成功后withExtendedLifetime持到请求结束。通过owner当前安装的field/coordinator处理捕获时的context，不再额外要求三个弱对象存活。未增加yield、sleep或后台调度；既有同步本地provider与渲染在MainActor Task内执行，未声称完整原私有async帧ABI。

原041190先完成2df190候选生成，再判断Task取消或raw候选为空，两者走同一分支：关闭/移出窗口并置nil菜单。该块不取消或置nil当前suggestionsTask，后者可能已经是新请求。Pasto原来生成前检查取消，生成后取消直接返回，不清旧菜单。现移除生成前取消门；生成后取消/空结果仅dismissSuggestionMenu，不影响新Task。普通无context/显式关闭仍取消Task、清slot后清菜单，两种收尾分开。

## 验证

2个生产文件5个精确增量，其他245份保持；247源逆恢复与旧快照幂等通过。14个反编译片段、10完整机器范围、118直接分支、8真实weak/ARC/Task导入，以及async descriptor绑定；14邻接方法和9共享源保持。8项有限要求审计关闭，新增17项源码/机器码/协议模型检查；68项定向与完整2645项静态检查通过，审计后17项复验通过。2旧测试文件8个精确调整可回放，350份历史Python输入可还原。

## 进度与剩余

v83增加040ec4、041190两条已修有限记录及1组，旧记录不变。234记录206组/13额外完成合同：P0 81/81（100%），P1 153/153（100%），合计234/234（有限100%）。该比例只表示已确认差异修复率，**不是全部原函数或P0/P1模块迁移完成率**。

实际viewModel/lazy0da768/已安装optional provider与当前直接store Provider仍须对照，非空正常菜单的anchor缺失/复用及上下文交付也未冒称完整。0f733c声明/消费者仍未知，整体目标继续；不把通用query枚举分支当作缺少query建议的证据。

官网9文件、应用1.0.2、HEAD、function-map和用户已有改动保持。未编译、构建、安装、运行应用/系统框架、联网、提交、推送、发布或部署；静态检查不等同应用功能回归。
