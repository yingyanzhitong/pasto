# 第五十五轮：原始字符串标识符往返

原版查询只设置fetchAttributes=[]，随后按SDK uniqueIdentifier依次追加String数组。Pasto已移除额外store过滤和私有前缀门，保留顺序、重复、空和非UUID值，仍按原始结果数限制100条并在迭代后检查取消。UI所需UUID只在后续本地native fetch后映射。

SDK写入直接使用记录ID，删除按原输入每100条切片，系统定向重建转发全部原字符串；不再拼接/剥离domain，不要求已有UI request。target工作自身原有空ID过滤、active/取消、重试及ack时序不变，四个原属性、文本上限、日期、expiry和update flag保留。

旧Pasto索引仍可能带前缀，因此增加每本地index的兼容marker：未标记时不恢复旧state，在同一named index清理成功后才写标记；失败不会提前置true。不修改剪贴板历史、分组或原IndexingState schema，本轮未实际执行迁移。

| v11有限清单 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 69 | 89 | 77.53% |
| 合计 | 138 | 158 | 87.34% |

关闭3条旧有限记录e2930/e48a0/f3c8c，后两条共享同一转发修复，不是三个独立bug。分母不变，余20条已知差异和两个未知。builder/delete及兼容marker为相关局部推进，不升级完整函数。named index/domain、完整weak owner/ack、FRC/DI/ABI仍partial。

888项源码/静态检查通过，新增18项，绑定17原片段及已有SDK删除字节证据。初870有9处旧断言失败和1定位错误；8旧测试更新真实raw-ID接线或保留历史整方法证据，继续核当前UUID映射、取消/错误尾及SDK flags。新检查覆盖原始ID往返、限数、重复/无效值、不变的状态/重试/错误，以及兼容marker成功/失败分支。

1份生产文件修改、232份不变；官网9文件、版本1.0.2、HEAD和function-map不变。未执行defaults/Spotlight/数据库、编译、运行、联网、提交或发布。

[机器证据](p0-p1-repair-round55.json) · [补丁](p0-p1-repair-round55.patch)
