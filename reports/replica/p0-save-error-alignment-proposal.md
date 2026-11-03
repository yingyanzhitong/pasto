# P0 恢复保存失败后续行为：待确认草案

本文件只提出可审阅的改动，未应用到应用源码。

原函数37a144在恢复事务返回Swift error时释放错误，仍继续清Undo并发DidRestore；Pasto当前try recordRestoredItems会直接抛出，跳过这两步。原ARM证据及范围见第二十七轮记录中37a144，前轮round22已绑定真实errorRelease与汇合路径。

草案只在写板完成后的recordRestoredItems外加do/catch，使事务失败仍执行既有Undo清理和DidRestore通知；写板前的reload、找不到选中ID等错误保持现有路径。当前持久化层失败rollback不由此草案改写；该项不代表原全部事务行为已对齐。

尚未修改生产文件、function-map、版本，未编译运行应用或提交。需要用户将“只读复查”范围切换到源码修复后才能应用；依据AGENTS.md第37、45—46行。

[查看补丁](p0-save-error-alignment.patch)
