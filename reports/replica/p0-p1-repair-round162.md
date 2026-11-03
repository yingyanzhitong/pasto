# 第一百六十二轮：新分组的原生创建生命周期

本轮先检查P1创建父合同再修复。原367c5c生成UUID并调用写入者，368560对新List执行initWithContext、identifier/name、尝试永久ID、可失败的属性编码、rawType2，未手工创建metadata或覆盖日期；真实完整函数39个BL和六个ObjC selector已绑定。原List/Metadata实际类及awake/validateForInsert已在149迁入：元数据缺失时按list:<identifier>首查复用，否则全metadata按index排序取末值+1创建，空为0，溢出按原checked行为。此前helper预建metadata、写裸identifier/值层index并覆盖createdAt，使真实校验分支一直被跳过。

现新UI/intent组直接创建PastoListEntity，保原identifier/name、永久ID错误消费、属性编码失败nil和rawType2顺序，不再提前造metadata或Date。每个事务repository只记住本次创建的同一List；值层synchronize对这些同对象跳过metadata/index写，既有/不匹配对象仍保严格metadata guard。保存触发已有实体校验和原awake，不手工额外validate。

成功save及cursor更新后，只从记住的对象投影实际metadata.index，更新返回状态并按既有值排序策略排列；不二次fetch/save，save错误路径仍原诊断/逐项校验/rollback/原错误传播，不执行该投影。Store同样从返回target原对象读取实际index，返回原target与更新后的值；不按UUID重查实体。去掉保存前的分组max+1计算，以事务内0占位值避免提前执行错误排序/溢出；该占位在保存后、发布前被原生实际值替换。旧兼容Pinboard blob可能保留初次占位，但现有读取project始终以原生metadata覆盖，后续值写入仍正常；不为重写兼容blob加第二次保存。

13个legacy/邻方法逐字保持，旧归档/历史makeList预填路径暂保，不把这条新组路径推广为全部创建来源。用户要求的优先未用颜色、UUID/值API及tie排序保持；未换模型、未执行迁移。

3生产文件7处精确增量，244生产文件不变，247文件逆增量恢复和5旧工具/测试10模式10替换重放通过。8原函数片段、39BL/6真实selector、既有实际List校验证据绑定；新增12项定向检查，完整2420项静态检查通过。首次3失败6错误包含旧手工metadata/固定let和返回形状、历史摘要以及新测试catch定位；保留首轮日志。旧业务检查直接更新为typed创建/真实校验，历史摘要只逆本轮增量，新测试直接检查当前实现。第二组曾通过后，进一步移除原父链没有的提前max+1；最终整组再次通过。均未编译/运行CoreData或应用，不能称运行功能回归通过。

v68在既有368560追加一项有限合同，地址计数仍225记录200组，额外合同11→12。有限P0 81/81、P1 144/144、总225/225（100%）；本轮不重复加函数。完整P0/P1及两个未知04430c/0f733c未闭；161的setter void仍保局部适配性质，不被本轮升级。下一步继续P1真实List collection与原生分组缺兼容值行时的消费者边界，以及其他错误/状态链。

版本1.0.2、HEAD、function-map与官网/下载九文件保持。仅本地修改，不编译构建安装、运行应用/系统框架、联网、提交推送或发布。
