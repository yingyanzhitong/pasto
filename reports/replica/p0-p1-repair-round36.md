# P0/P1 源码修复：第三十六轮

本轮修复2处明确边界，并复核复用3条已经实现的本地恢复/删除记录。执行顺序仍为先修P0，再检查P1，最后修P1。

键位翻译保留缺少ASCII source时的原有失败路径；其余layout属性原版没有Swift式nil早退。现在nullable原始属性交给C桥，直接CFDataGetBytePtr后进入UCKeyTranslate，actionDisplay=3、modifiers/options/dead state=0、容量4和结果筛选保持原路。没有用新的precondition或猜测的nil结果替代原生API行为。source通过withExtendedLifetime覆盖翻译，输出长度通过固定宽度传回Swift；新增头文件实际导出到现有PastoObjC依赖。

图片准备的实际生产调用改为默认根，在使用时取FileManager.default.temporaryDirectory，再单String追加images；默认不再预建PasteReplica父目录。hasDirectoryPath、创建中间目录false、错误记录后仍返回URL及图片写入/过期清理算法不变。显式测试根注入仍保留，品牌文件名前缀继续Pasto。没有运行目录创建、清理或原生键盘接口。

3614c0/364014/364074原记录的已证有限差异是本地History容量/首实体refresh，以及对应恢复/删除生产交付。当前沿真实recordRestoredItems→mutate→同事务repo原生目标→倒序Date/setTimestamp→实际List.rawAttributes容量→first-history refresh→条件save检查，删除则区分history（含空输入）和普通group。原无share门用已绑定C/ARM证明输入透传，不猜普通本地项必须克隆。这3条的生产文件本轮未改，直接复用现有实现；不是3个新独立bug或3次相同功能重写。

| 已确认有限差异 | 已修复 | 分母 | 比例 |
| --- | ---: | ---: | ---: |
| P0 | 66 | 69 | 95.65% |
| P1历史依赖 | 8 | 81 | 9.88% |
| 合计 | 74 | 150 | 49.33% |

关闭5条既有有限记录，分母不变。P0尚余1eaa64的返回状态适配、378df4许可前额外读取及37ade4预建实体Sequence/context交接；P1剩73，合计76差异及2未知。完整函数/原实体子类/DI/ABI、跨进程/重入错误和全部存储行为未升级；37ade4没有因底层恢复链已经对齐而自动关闭。历史3记录有明确无share、正常有效本地实体的范围，不能外推到共享或失效对象。

554项Python源码/C/Mach-O/SDK声明检查通过，新增14项，绑定14个原函数和4个真实原生导入。新增C实现与头文件2个，修改4旧生产文件，224旧文件未变；1旧测试精确冻结上轮projection整文件增量检查，同时仍核对实际当前helper。初次旧测试有1处旧默认根断言，新测试有3处注释/SDK文本编码/循环字面定位问题，按实际源码修正后通过，失败日志保留；生产算法未为这些断言回退。

未编译、构建、运行Swift/ObjC/Carbon/CoreData、执行迁移/目录操作、安装、联网、提交、推送或发布。官网9文件、1.0.2、HEAD与function-map保持不变。继续P0剩余三处；P1独立检查尚未开始。见[JSON](p0-p1-repair-round36.json)、[补丁](p0-p1-repair-round36.patch)。
