# 第五十六轮：监听句柄替换与可用性复核

索引初始化进入监听分支时，原f14cc直接创建新Task并替换+120句柄，健康state复用的f00dc也相同。Pasto已移除额外“必须active且旧句柄为nil”的门，保留无store兼容返回。不在factory增加旧句柄的cancel/await，停止函数原有显式取消保持。完整旧/新任务、provider stream与并发回调生命周期仍未据此判等价。

可用性旧记录已复查：efccc确实在配置恢复、observer和ID请求前判断SDK可用性；false分支会willThrow，父f2214清active，当前已有实现可直接复用。原e19c8也会提前构造SDK index，所以旧“构造器先创建index”解释不足以单独证明当前仍有差异。没有误改为静默返回，也不称typed Error ABI完整一致。

| v12有限清单 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 71 | 90 | 78.89% |
| 合计 | 140 | 159 | 88.05% |

新增并修复1条observer创建有限合同，复用关闭1条旧availability记录，旧v11 158条完整保留；不是新写两个函数。余19条已知有限差异和两个未知，原SDK owner/ack、FRC/DI/ABI及完整原版分类仍未闭合。

899项源码/静态检查通过，新增11项，绑定11原片段、真实c3eb68→f3b00→f340c descriptor及既有actor字段证据。初888有5处旧断言失败，4旧测试更新真实factory guard或保留历史方法证据，并继续核当前raw-ID、callback、状态与取消合同。新检查覆盖旧句柄存在/停止期间的安装门、真实callback、availability错误传播和两初始化路径。

1份生产文件修改、232份不变；官网9文件、版本1.0.2、HEAD与function-map不变。未执行defaults/SDK/数据库、编译、运行、联网、提交或发布。

[机器证据](p0-p1-repair-round56.json) · [补丁](p0-p1-repair-round56.patch)
