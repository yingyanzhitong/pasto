# 第一百四十一轮：分组定位读取当前实体归属

继续P0修复→P1检查→P1修复，本轮P1分组动态目标；上一轮批量编辑入口复用后，未继续重复扩大编辑函数计数。

核对分组菜单现有缓存producer后，确认导航目标3b83c4仍有独立差异。原函数要求恰一个已解析项目，直接读取同一实体timestamp，再读取list关系并严格检查rawType==2；历史优先、所属分组其次，按当前列表标识省略当前目标。旧Pasto通过selectedItems先解ClipboardItem旧归档，再store.pinboardOwner从缓存Pinboard求归属；原生字段有效但旧归档损坏、或native owner已变而缓存值滞后，目标会被阻断或过期。

现ClipboardRestoreItem.listNavigationMembership在主actor按需读timestamp、list、rawType和identifier，无archive解码、Pinboard缓存查找或额外fetch。State从已应用collection取得handles；无owner时沿现有visible entry.restoreItem兼容桥。单项门之后原生分支先返回历史/owner目标；只有无native实体的旧值才resolvedItem并复用原历史/owner尾。实际reveal动作也取applied handle.id保存offset/pending focus，不再第二次解旧DTO。查询清除、当前context等待及清pending后按新snapshot定位的既有方法不改。

保留明确适配：Pasto tab仍以UUID标识，owner.identifier不能桥接UUID时无可导航组；原版返回List实体、比较String，完整标识/模型/DI/fault身份未宣称等价。旧多组数据、命名、未用颜色及面板内删除规则不变。完整generic集合缓存/异常、其余菜单/图像VM/任务与两个未知仍排队。

2生产文件3精确增量，其余245文件不变。绑定6原反编译片段、10 ARM字、4实际调用及timestamp/list/identifier三条真实selector链；7旧方法及4集合/引用源保持。新增16项源码检查，完整2198项源码/Python/Mach-O静态检查全部通过。首次有3历史整文件快照和2旧DTO形状断言失败，首轮日志保留；只对快照逆隔离本轮3增量，定位键盘测试改为直接检查当前handle路径，同时保留旧值/顺序断言。4既有测试/工具共8模式10替换，未执行Swift/ObjC编译或系统框架。

v50保旧208记录186组及8额外已修合同，新增3b83c4有限差异1条并修，至209记录187组。P0 77/77（100%）、P1 132/132（100%）、总209/209（100%）只是已确认有限差异修复清单；完整P1父合同和04430c/0f733c仍未闭合，整体迁移率未知，目标继续。

版本1.0.2、HEAD、function-map及官网/README下载9份改动保持。仅本地代码/报告与源码测试，未编译、安装、运行、联网、提交、推送、发布或部署。
