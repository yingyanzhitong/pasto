# 第一百二十六轮：当前设备工厂与采集消费者

按“修复P0→检查P1→修复P1”继续。原312150取当前设备的IOPlatformSerialNumber，按identifier查询首条Device；命中原样返回。查询失败在原32aee0释放错误、返回empty结果，因此工厂走未命中分支。未命中先读取机型显示名，再插入type2、identifier、name。新采集360d9c在内容写入之前调用工厂并设置同一个device对象。

Pasto此前按设备显示名称查找、未命中生成随机UUID。本轮接入当前设备工厂，只用于新采集miss：按identifier查询、batch20/limit1/offset0，hit不重命名或改type；miss按原顺序创建，并填写现有本地模型必需createdAt。向同一捕获对象设置device并同步显示标签。命中旧记录仍保留原设备，旧name/UUID归档helper及现有设备关系不批量改写。

标识provider每次读取IOPlatformExpertDevice的IOPlatformSerialNumber属性；有效String（包括空字符串）原样返回，service/property/cast失败返回Unknown，并释放service。实际字符地址及ADRP+ADD证明键是SerialNumber，不是最初猜测的UUID。机型provider读取hw.model，只在字符串两端trim非字母字符，按小写匹配MacBook/MacBook Pro/MacBook Air/iMac/Mac Pro；其他机型保留trim后的原大小写及内部符号。底层两次sysctlbyname忽略状态，按首次size建立零buffer，读取NUL前UTF8，解码失败为空。

3个既有生产文件5个精确增量，244文件不变；provider放在既有设备持久层文件中，生产文件总数仍247。14个原片段、11个实际调用、19个ARM字、4个真实selector、2个真实registry字符串、10个未变方法和4个共享源已绑定。本地SDK仅检查声明文本，不执行IOKit/sysctl或读取本机序列号。

18项新增检查，累计1998项Python/源码/Mach-O静态检查全部通过。初始运行有91项历史全文件/文件集合快照失败和1项旧签名error；初日志保留。将新helper收拢既有文件、2个历史测试/工具6处精确逆向隔离后通过。新的18项检查直接读取当前源码与原始字节，未把历史快照作为当前功能测试；Python例表为辅助源级模型，不冒充系统框架运行。

v39保留v38全部197记录178组，新增4个有限函数合同，同属当前设备工厂1组；360d9c消费者增量不重复计数。P0 77/77、P1 124/124、总201/201（100%）仅指已确认有限差异，整体P0/P1迁移率仍未知。raw-data异常后的命名日志及独立错误回调尚待核对，当前仍为P0整体复查，不提前处理P1。

仅本地修改。未编译、构建、安装、运行应用/框架、读取硬件、联网、提交、推送、打标签或发布；官网9文件、版本1.0.2、HEAD与function-map不变。
