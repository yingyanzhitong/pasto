# 第四十一轮：P1 应用与设备原生来源

原30e070/30ed6c依赖来源实体的items反向关系。原有Pasto只有Application值记录和条目上的设备名，本轮补入真实ApplicationEntity/DeviceEntity及Item.sourceApplication/device可选Nullify关系，字段/默认值/唯一约束/标识索引以原v10.mom为据。旧Application编码记录、Item内容和既有UUID不改。

旧六种模型构造均关闭新来源图，新增上一版带ItemData的模型候选；推断迁移后以sourceGraphVersion执行一次回填，所有关系完成后在同一save中写标记，再次打开跳过全量解码。没有运行迁移。旧设备仅有名称，没有vendor/hardware ID，因此按既有名称创建持久本地UUID；不能据此宣称已恢复原设备身份或完整type/version工厂。

实际采集在内容/预览、来源采样之后、历史Date之前写原生来源。事务记录已处理ID，generic commit不重复处理该条；普通仅时间变化时不查来源。Application值记录更新同步原生名称/icon/color，删除由真实inverse关系维护。候选现在用真实context字典fetch：name-only、distinct、items.@count>0、原正则、name升序，并过滤缺失/非String/空名；错误沿Persistence/Store/UI provider抛给原逐组catch。没有另设候选值缓存。

| 已确认有限差异 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 69 | 69 | 100% |
| P1 | 25 | 81 | 30.86% |
| 合计 | 94 | 150 | 62.67% |

关闭6条旧叶记录（30e070/30ed6c/30f380/30f3a0/2dfb18/2dfd4c）；共享查询链不是6个独立新bug。剩56差异和2未知。07d0e0、2e00a0及availableFilters/optional-source初始化父链继续开放，原类/DI/ABI、完整设备/来源工厂、跨进程和错误重入不冒称完成。

最终源码复查将实体构造统一为先设置properties、再设置唯一约束；补断言后重新运行660项检查通过。660项源码/静态检查通过，新增19项。绑定12原函数片段、原MOM三实体的相关字段和4个原ObjC selector/fixup链；覆盖旧模型分支、回填标记、inverse、采集顺序、复制不重复来源写、实际错误交付。修改5旧生产文件、新增1个，225旧文件未变。8旧测试仅扩明确新模型参数、允许单独来源hook或冻结历史整段证明，当前关键语义仍检查。首641有12处旧源码形态断言，扩660有1处测试误定位key闭包，失败日志保留，按实际调用修正后通过。

未执行数据库、迁移、CoreData/AppKit或应用；未编译、构建、安装、联网、提交、推送或发布。官网9文件、版本1.0.2、HEAD与function-map不变。继续索引内容投影和生命周期。见[JSON](p0-p1-repair-round41.json)与[补丁](p0-p1-repair-round41.patch)。
