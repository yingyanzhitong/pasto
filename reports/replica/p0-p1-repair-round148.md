# 第一百四十八轮：发现 List 插入校验入口缺口

继续P0修复→P1检查→P1修复。147轮已修Stack关闭链，本轮先核搜索待证入口，未取得足以关闭04430c/0f733c的新直接consumer，未猜改。随后转查更关键的原生分组模型插入验证，确认新增一条P1差异并排到当前修复首位。本轮是新证据与清单进展，未修改生产代码，不把检查通过冒充修复完成。

原ListEntity类地址100f97ec8的真实instance method表明确包含validateForInsert:，IMP329ec0直接调用329980。后者在非deleted、valueForKey:(metadata)为空且有managedObjectContext时，按list:<identifier>查询既有metadata；没有则取原Metadata集合最后一项index+1（空集合为0，有有符号溢出门），创建并附着metadata。所有这些条件分支最后都进入super.validateForInsert:。已解真实valueForKey:/setMetadata:/index/setIndex:四个selector，不能把该getter误称primitiveValueForKey:。

同时发现反编译陷阱：Ghidra把329ec0错误分支标为unreachable并给出return1，但原ARM329ef0检查Swift错误寄存器x21，329f14在有NSError输出参数时写错误，329f24以cset w0,eq返回成功/失败。后续必须保留super错误传播，不能逐字照搬伪代码的永远成功。

Pasto的ListEntity模型目前managedObjectClassName为NSManagedObject，全部当前Swift源没有validateForInsert override。makeList/insertPinboard只为自己创建的对象预填metadata，不能代替原持久化插入校验入口，也没有该入口的既有metadata查找/复用/缺失恢复分支。正常UI helper已有的成功路径保持；差异范围是缺失metadata的native插入验证与错误返回，不声称普通新建分组现在必定失败。

修复顺序：先迁实际List managed subclass和model绑定并保旧模型候选；再完整迁metadata查找/复用/新建/附着、排序/空集合/溢出及super错误；只用源码与ARM检查，不编译或执行CoreData。原Syncable字段默认值、Metadata默认排序与fetch错误边界需进一步绑清，不用更改两个helper代替真正入口。

本轮12原片段、19 ARM字、真实类方法表及4 selector已绑；8项新增静态审查通过。247生产文件和295个既有Python文件全部字节保持；147轮2290项通过的代码/测试输入保持，本轮未重复运行整套，不宣称2298项全跑。未改旧测试断言或制造仅为转绿的源码改动。

v57保旧214记录192组及9额外合同，新增329980一条待修，至215记录193组。已确认有限差异：P0 77/77（100%）、P1 137/138（99.28%）、合计214/215（99.53%）。分母因新确认缺口增加；整体P0/P1迁移率仍未知，两个unknown保留，目标继续。

官网/README下载9文件、1.0.2、HEAD和function-map保持。未编译、构建、安装、应用/框架执行、联网、提交、推送或发布。
