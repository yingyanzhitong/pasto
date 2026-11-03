# 第一百一十七轮：先复制，再准备恢复事务

继续P0。原37a144的真实顺序为：37aa3c获取缓存writer → 37875c清空并写入 → setInteger:forKey:保存changeCount → 2ff310构建事务并performAndWait，捕获37b620/37ade4更新恢复记录。x21为零直接进入Undo清理；非零先释放错误，再汇合到同一Undo和DidRestore路径。37aa3c仅初始化/返回Pasteboard实例，不能当作数据库准备步骤。

Pasto原先在系统剪贴板写入前调用prepareRestoration，内部验证/读取revision、锁与事务准备失败会阻止复制，还跳过Undo和通知。本轮仅把这一语句移到write/count之后的do/catch内。准备与record/save的Swift错误现在共享原事务的错误落点，失败不取消已完成的剪贴板写入，仍清理Undo和发送两路恢复通知。复制消费者保持write返回→copied handler→hide。原生及旧值/ID共用此顺序，无新增模式flag/异步等待。

选区解析、空输入、表示生成及metadata/availability算法保持；发生在表示处理中的错误仍按既有入口传播，不混同写后事务错误。没有吞并全部ObjC异常或承诺框架实际运行结果。

8原片段、10真实BL、6指令字和3选择器绑定，包括defaults setter而非误称getter；10既有方法及6共享源保持。仅1生产文件1精确方法增量，实际只移动prepare语句，246生产文件不变。新源码检查可精确把语句移回并还原baseline。

19新增检查包括从实际生产语句位置派生的成功、prepare失败、record/save失败轨迹，以及旧快照prepare失败导致复制和清理全被跳过的反例；并核实原cbz x21的错误分支汇合。最终1821项源码/Python/Mach-O静态检查全绿。首2失败为第116轮直接hash/方法历史断言，1error为新测试do定位也匹配undo注释；唯一换行标记修正后又因含开括号令共享body定位到catch，移除标记中的括号后定点与全套通过。2历史测试工具5精确隔离改动，原proof不改；初/第二次失败日志保留。生产没有因测试定位问题改动或回滚。

既有低模型只读复核输入强持、真实原调用及错误分支，未发现明确反例。下一P0预查发现原writer为manager+88懒缓存，当前每次new writer额外读count，但写后已同步captureState防自采集；不能由此臆断完整DI或盲建全局强缓存，继续绑定poll/start/owner和custom pasteboard生命周期。该预查仅记录证据，未修改writer实现或声称实测提速。

37a144为既有记录，本轮额外消费者修复不重复计数。v37保持P0 72/72、P1 124/124，总196/196（100%）；仅已确认有限差异，完整Pasto迁移率仍未知。继续P0父合同后检查P1再修P1；P2及联网排除。完整metadata/model/context/DI/fault/save和两未知仍未闭合。

未编译、构建、安装、运行、联网、提交、推送、标签或发布；官网9文件、1.0.2、HEAD及function-map保持。
