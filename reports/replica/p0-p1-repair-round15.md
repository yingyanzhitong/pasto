# P0 → P1 源码修复：第十五轮

| 范围 | 已修有限差异 / 固定差异分母 | 进度 |
| --- | --- | --- |
| P0 | 41 / 64 | 64.06% |
| P1（P0依赖） | 5 / 81 | 6.17% |
| 合计 | 46 / 145 | **31.72%** |

本轮补已计输入父合同分支，不重复计分；仍有99条差异及2个未知入口。不是完整原函数或产品完成率。

## 本轮修改

全选、相邻移动和首尾定位读取collectionOwner实际已应用的items。查询值已改变、原集合更新尚在排队时，不再把新visibleItems当成眼前选区。全选替换完整有序选择，anchor和primary均为最后一项；无实际owner时不操作。

Space预览和Return粘贴通过已有appliedSelectionItems解析：按有序选择在已应用items中查找，缺失项跳过。保留当前空输入guard、选择mode、相邻动画和边界不动画的行为，没有重写preview或粘贴服务。

原SelectAll的06ba24调用228ee8；后者先22b1cc取得manager count，再用229138(0,count)生成索引范围。ARM确认count从manager+8读出并经x1返回。reload从dataSource取count并写入manager，真实DataSource入口读取applier.items.count；原最后索引写入端点后同步更新cells，不reveal。

## 审查与验证边界

原末字节参与“最后索引是否存在”的门控，不能直接拿来与Pasto独立allowsEmptySelection策略比较。此次修复不证明零项后续生命周期或所有modifier组合一致。原069778的066068是粘贴业务；未匹配键走super，不能称为通用选区更新。导航实际链227cc4→228498→227b54→2348a8→228c78已绑定，分页/Tab等未闭合映射没有凭缺少显式case判成缺功能。

注册接口1eaa64的成功/替换/失败和日志在已审范围内一致；当前OSStatus被GlobalHotKey/AppMain实际消费，是保留的本地API扩展。本轮不造未调用的void包装，也不将该签名差异静默从原分母删去。

336项源码及原C/ARM静态检查通过，新增10项，旧326项未改。只改1个生产文件中的五个方法，其他223个与本轮备份一致；17个原片段、4段ARM数据和既有applier数据源证据已绑定。

未编译、运行AppKit/应用、联网、提交或部署。真实键盘输入、零项后续策略、不可见cell滚动及完整preview时序未做运行验收；版本与全函数台账不变，官网等仍仅保留本地。

[完整记录与源码绑定](p0-p1-repair-round15.json) · [源码补丁](p0-p1-repair-round15.patch)
