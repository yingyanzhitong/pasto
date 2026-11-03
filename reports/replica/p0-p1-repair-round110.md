# 第一百一十轮：列表菜单移除输入和显示资格

本轮修复“从所有 Pasto 移除”点击时重读选区的问题。菜单构建时捕获同一输入数组，添加分组、创建后分配和全部移除共用；remove-all直接调用已接通的Store.assign(items:to:nil)原生事务，保留数组次序与实体。当前分组移除仍保留原目标UUID路径，不能与清除所有当前owner混同。

原07637c把closure+50/+58的callback/context传在栈上，09e8a8尾从fp+18读取并以captured array构造action。ADRP+ADD实际目标09f574，再跳09f250→09ef40，不是直接省略thunk；最终076330/09e608→3ba1e4事务→Writing+48→上轮native primitive。3ba2bc分别调用allSatisfy(3ba374→3ba4d0)与contains(3ba390当前list.rawType2)，再检context tag1及传入Collection非空。3b80f0 rawType1置bit62为history，rawType2置bit63为pinboard。isEmpty的metadata/witness来自传入items，不能误记成另一个VM集合。

Pasto普通local unshared组无CloudKit share metadata，故只在此子域将writable条件视为true；不宣称共享权限迁移。资格读取原生list/type，不解payload/color，旧值输入保留显式适配；history搜索仍是history上下文，不添加query空限制。最近删除视图保留Pasto适配门。from-this目标绑定、完整menu布局/DI/fault/reentrant和共享权限尚未闭合。

20原片段、16实际branch、18ARM字及3ADRP目标绑定；3生产文件5精确增量，244生产文件不变，6共享源及6方法保持。15新增检查，最终1689项Python源码/Mach-O静态检查通过。首轮2项失败均为历史校验隔离：旧rawhash需只逆本轮增量，reverse需在本轮marker存在时才生效以保持幂等；已修正隔离，初日志保留。没有运行Swift、原二进制或CoreData。

v33完整保留v32的187条/170组，新增两独立有限差异并修：P0 70/70、P1 119/119，合计189/189（100%）。该分母是已确认有限差异，不能视为Pasto整体迁移率。完整模型/DI/错误、兼容blob/cache-miss、创建返回、from-this、Stack/选区/image父合同及04430c/0f733c继续开放，目标仍进行中。

未编译、构建、安装、运行、联网、提交、推送、发布或部署。官网9份本地改动、1.0.2版本、HEAD和function-map保持。
