# 离线迁移第九轮：面板生命周期和搜索取消

2026-10-29。只读取已有反编译代码、原二进制元数据并修改源码、运行 Python 源码检查；未编译、构建、安装、运行应用或原函数、联网、修改用户历史、提交或推送。

## 修复与原证据

原 `0x100037948 → 0x100037704` 的 Esc 逻辑先看当前内容上下文：搜索时取空 query nodes、写回搜索模型，再调用 SearchBar.onDismiss；历史或分组上下文则 performClose。Pasto 的多个 Esc 消费者原来统一直接 hidePanel，即使有有效搜索条件也直接收起。

现统一取消入口保留删除确认优先级、sheet/modal 等保护及已有 popover 处理，然后：

- 有效搜索非空：清空文本、筛选及 nodes，退出搜索并归还面板初始响应者，立即返回，保留面板。
- 有效搜索为空：沿现有 hidePanel 收起。

判断使用 `isSearchQueryEmpty`，不是搜索框是否可见；原 `0x10007df7c` 同样用有效 query 决定 search context。搜索编辑器、面板 key handler 和 popover Esc 监视器都接到同一入口。取消搜索不更换分组、不删除历史；用户要求的面板内确认仍优先消费 Esc。

为避免仅凭变量名猜分支，本轮静态遍历原 Mach-O 的 `__swift5_types` 相对指针：`0x100d755f8 → 0x100cad74c` 为 ItemCollectionContext 枚举描述，字段描述 `0x100d48fc0` 的三个 payload case 顺序确认为 `search / history / pinboard`，无空 case。结合原函数的高两位 tag 比较，确认清空搜索为 tag 0、关闭后恢复只处理 history 为 tag 1。该解析没有执行原程序，原字节和摘要见 [机器记录](offline-migration-p0-round9.json)。

## 直接复用与剩余差异

已有 show/hide transitionGeneration、旧 completion 失效保护、关闭中重开、0.15 秒展开及 0.2 秒 easeInEaseOut 收起、nil responder 回退、屏幕变化几何、关闭后 10 秒搜索清理、重开时注销观察者并取消清理、DidRestore 不改搜索/分组等子行为，本轮沿真实消费者复核后直接复用。没有为每个原 wrapper 新增空壳方法。

失焦回调仍有明确差异：原版同步检查一次 suppression、sheets 和全局 modal 后关闭；当前另有异步处理、菜单/key/预览/父窗口排除及鼠标/失活监视器，不能说已一比一恢复。suppression 的有效置位来自 Handoff 域，本轮按离线范围不迁入。原 NSWindowController、Published isVisible/onDidShow 与自有 onWillShow 激活时序、show 直接隐式 frame 与 animator 代理、强弱捕获以及搜索 120ms Combine 投影，也继续保持 partial。静态几何和代数检查不代表实际动画或焦点验收。

## 检查与进度

**89 / 89** 项 Python 源码、台账和静态证据检查通过，本轮新增 12 项。覆盖原上下文 metadata、原 Esc 分支、清除后提前返回、确认优先级、真实 Esc 接线、展开/关闭顺序、过期 completion、10 秒任务、restore 作用域、重开注销与 responder 回退。没有进行 Swift/ObjC 编译或 AppKit 交互测试。

本轮核对 **33 个原地址**，新增 **2 条 partial** 映射，partial 合计 **432**，新增完整迁移 **0**。九轮去重累计 **264 / 81,123 = 0.3254%**。历史完整标记 **1,648 / 81,123 = 2.0315%** 仍含过期证据，不是当前 Pasto 完成验收。库存检查 2,089 条映射，没有缺失源码引用；12 条既有证据地址/格式缺口保留，不以新测试冒充旧构建证据。

P0 未闭合的模型、DI、actor 诊断、事务错误、窗口事件及生命周期边界继续排队；下一批按实际功能链核对 P1 搜索与筛选的已有归一化、条件组合、建议和取消代码，以复用和明确差异修正推进，不因结束一批宣称模块完成。
