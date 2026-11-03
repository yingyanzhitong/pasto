# P0 → P1 源码修复：第十轮

| 范围 | 已修有限差异 / 固定差异分母 | 进度 |
| --- | --- | --- |
| P0 | 37 / 64 | 57.81% |
| P1（P0依赖） | 5 / 81 | 6.17% |
| 合计 | 42 / 145 | **28.97%** |

本轮修复2条已证有限差异：普通失焦回调 `018c84` 和本地展开完成接线 `0b07f0`。已计的 `0b098c` 补充采样后激活动作不重复加分。尚有103条差异和2个未知入口；上述比例不是完整函数或产品完成率。旧比较结论覆盖仍为654/656（99.70%），不能当迁移完成率。

## 本轮实现

失焦由真实窗口delegate同步交给弱owner，检查附加sheet和全局modal后启动关闭。删除了此前的main.async以及菜单、key window、预览/祖先窗口额外跳过条件；保留已有关闭过程的可见性和重入保护。原一次性suppression的已见设置来源为排除的Handoff，本轮不迁该业务，也不声称所有分支等价。

展开回调改为真实 `panelDidShow`：只有动画完成且generation仍匹配时，才在外观/搜索焦点工作之后交付。AppMain此时采样 `frontmostApplication`，按原非自身条件存储previous，然后调用零参数 `NSApp.activate()`。正常展开不再提前激活；modal分支仍激活并返回。没有为原Published链制造未消费的状态字段，完整父合同继续待证。

## 证据与检查

261项Python源码及原C、ARM64、SDK声明静态检查通过。原委托→弱回调→关闭链、onDidShow生产消费者、采样/激活顺序和旧generation失效条件均有绑定。旧focus测试只更新接线字面预期，保留原非自身、无旧target回退及关闭清理断言。

另纠正编辑键分析：`3bb290` 调用的是router existential的witness服务，`+48/+50` callback只是实参；不能根据callback setter猜测编辑目标。已从生产构造的metadata/witness两槽绑定到`PasteRouting.Router`，实际进入`003da0`的独立预览窗口展示，true分支调用`07be8c`。这条编辑路由和会话仍待接入，不计修复。Shift-E为系统Writing Tools入口，0.5秒等待失败分支同样发action，不是应用自有模态框。

本轮修改2个生产文件，其余219个与本轮备份一致；新增2个静态测试文件。未编译、安装、运行应用/框架、联网、提交或发布；版本和全函数台账不变。实际光标、popover、前台切换及动画没有运行验收。官网、README和Actions仍按用户决定仅保留本地。

[完整记录与源码绑定](p0-p1-repair-round10.json) · [源码补丁](p0-p1-repair-round10.patch)
