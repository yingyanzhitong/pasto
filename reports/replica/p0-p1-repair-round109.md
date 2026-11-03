# 第一百零九轮：原生分组移除和孤立清理

本轮接通Store.assign(items:to:nil)的native数组分支，预览菜单现有current-handle移除调用直接进入同对象事务。原preview VM+f0→3c3894/3c38e8→Writing+48→364094→363a3c已绑定；363a3c按Sequence输入顺序、不去重，只有当前owner非nil且rawType2才以当前owner交36299c。该pinboard分支只在当前owner相等时清list，再检查timestamp与当前list均nil才经3646ec删除；删除context来自Item自身，nil Objective-C receiver不做操作。无owner/非group输入不能被额外孤立删，未见order设置。共17原片段、13真实branch、2真实指针、6选择器、10ARM字和3完整直接调用清单绑定。

新repo按原序列先执行全部native KVC/删除，再给兼容层返回对象。已有cache仅重投影owner/order，不额外读payload archive；缺cache仍用既有item decoder。Native unassign保留原timestamp和displayOrder列，assignedItemIDs防止normalize后的nil order被写成0；unassignedItemIDs使Item兼容apply仅在content变更时编码旧兼容blob后return，不再覆盖Data/source/title/time/rawPreview/checksum等native字段。实际删除ID仅传给Item update的alreadyDeletedKeys，构造fetch keys前移除，避免二次UUID查询/删除；其他实体和默认删除仍用空集，业务输入数组无去重。

2生产文件、8精确增量，245生产文件不变；7个既有assign/restore/legacy-delete方法和6共享源保持。2历史测试工具仅隔离本轮增量，既有1650先通过；24项新增检查首轮有1个测试用错泛型signature且把参数当作body内容，已纠正定位，初日志保存；最终1674项Python源码/Mach-O静态检查全绿。独立只读复核确认owner门、own-context、markers和tuple接口，未用Swift/ObjC或CoreData运行验证。

本轮不是完整零archive路径：兼容content blob仍可能编码payload，缺cache解码也会失败；这类错误发生在native mutation后/save前，既有事务不自动rollback，完整错误/fault/DI/owner仍开放。历史rawType1移除、混合/旧值及列表其他remove消费者不据此宣称完成。下一步对照列表“从此/所有分组移除”实际捕获/当前list路由，再复用本轮primitive；原生创建返回桥、Stack/选区和image父合同以及两未知04430c/0f733c继续。

v32原样保留v31全部185条/169组；新增并修363a3c输入及36299c pinboard owner/orphan两条有限合同，以实际direct-call origin合为1保守组：P0 70/70、额外P1 117/117、合计187/187（100%）。这是已确认差异清单比例，不是Pasto整体完成率；没有完整函数升级，P2仍排除。

未编译、构建、安装、运行应用/框架/CoreData、联网、提交、推送、标签、发布或部署。9个官网/下载本地改动、版本1.0.2、HEAD与function-map保持。
