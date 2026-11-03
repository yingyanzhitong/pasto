# P0 → P1 源码修复：第十六轮

| 范围 | 已修有限差异 / 固定差异分母 | 进度 |
| --- | --- | --- |
| P0 | 41 / 64 | 64.06% |
| P1（P0依赖） | 5 / 81 | 6.17% |
| 合计 | 46 / 145 | **31.72%** |

本轮补已计dispatcher分支，不重复加分；仍有99条差异及2个未知入口。不是完整原函数或产品完成率。

## 本轮修改

新增真实接入handleKey的2348a8导航分类器，每次只读取分类结果一次。按原优先级识别Control+f/右箭头、Control+b/左箭头、Control+e/Command+下箭头、Control+a/Command+上箭头。Control字母分支只要求Control位，不把其他modifier一概排除。

相邻移动按原227b54读取Command/Shift选择mode：Command的mode1回退，Shift覆盖为mode2；首尾定位只按Shift扩展，保持不动画。未识别的键返回false，保留现有外层fallback，未为分页、Tab等未证组合增加行为。

修复一个可证分流冲突：到达集合输入且未编辑时，Control+Command+A原来在更早的Command+A分支执行全选；原分类返回2，随后选择index0/mode0/animation0。现在全选入口排除Control/Option，由真实导航分类器处理该组合。Option+Command+A也不再作为普通全选，无匹配时回退false；不据此声称整个AppKit菜单交付等价。

## 验证与边界

344项源码及原C/ARM数据静态检查通过，新增8项，旧336项未改。修改1个现有生产文件、新增1个已接线组件，其他223个与本轮备份一致。6个原片段和5段ARM数据已核，包含Control位、返回码2和边界选择参数。

旧反例绑定before文件与方法摘要，修复后的classifier及consumer另绑最终摘要，已纠正审查中“旧branch配新文件hash”的混绑。该冲突是修复后的有限一致，不是把旧差异误称从未存在。

实际键盘、输入法、菜单/performKeyEquivalent拦截与完整responder链没有运行验收。零项策略、不可见cell滚动和完整preview生命周期继续保留。当前转入P0面板搜索关闭链，迁真实约束、easeOut动画与完成副作用；切换模块不表示快捷键模块已完成。

未编译、运行AppKit/应用、联网、提交或部署；版本、全函数台账不变，官网等仍仅保留本地。

[完整记录与源码绑定](p0-p1-repair-round16.json) · [源码补丁](p0-p1-repair-round16.patch)
