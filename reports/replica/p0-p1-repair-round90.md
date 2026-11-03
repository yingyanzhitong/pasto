# 第九十轮：编辑入口保留原生条目

上一轮接通正文的同context对象观察，同时留下UUID工厂将查询失败/缺项都折为空的边界。本轮从真实编辑生产入口传递已捕获实体，移除这一入口的第二次UUID查询，不凭空为原版增加查询错误分支。

原0655cc先遍历全部输入、按31c2ec过滤并保留原元素；过滤完成后空结果beep，否则第二轮依次交3bb280。3bb280→3bb290的Router witness仍传同一首参；003da0登记窗口后构造3c25dc，后者和正文3c0390均直接用原首参建立3c1c84观察，对同一实体取context/objectID，不按ID重查。

Pasto的Cmd+E和本地WritingTools改为使用appliedRestoreItems句柄；过滤时读取当前类型但保留原句柄，全部筛完再逐项路由。router将同一input交预览factory/文本content；ClipboardRestoreItem内新增观察factory，直接捕获原PastoItemEntity，正文由它构造观察源。原恢复内容resolve闭包不改。观察器仍在窗口登记之后构造，registry、transition、beginEditing、present、焦点顺序及关闭回调保持。

显式旧值句柄的观察factory返回nil，不会再次调用UUID/CoreData查询，但仍保留Store.$items缓存订阅。未传句柄的普通/popover预览仍走旧UUID工厂，其查询错误/缺项回退问题并未全局消除。标题栏、非文本内容、写回操作实体身份及归档投影仍为适配。WritingTools原先就先作文本筛选再经editItems筛选，本轮保留双层过滤及额外投影，不声称只解码一次或性能改善。

绑定10个原片段、11条真实机器调用和1条Router间接调用，复用既有router与optional选区、原生观察证据。1356项源码/静态检查通过，新增15项。首次套件因旧签名/摘要产生37失败和4错误，实际执行1327项，包含setup失败导致未执行项；日志保留。4个历史测试/工具仅逆变换本轮14个精确hunk，新检查直接核当前入口/同对象捕获/显式nil不fallthrough与窗口时序；此前1341及最终1356均通过。3生产文件改动，244个保持，无新生产文件或schema/Package变化。

| 已确认有限差异 | 已修复 | 分母 | 进度 |
| --- | ---: | ---: | ---: |
| P0 | 70 | 70 | 100% |
| 额外P1 | 96 | 97 | 98.97% |
| 合计 | 166 | 167 | 99.40% |

本轮补已有编辑实体父合同，不新增完整函数或有限差异分母。原完整模型/DI/ABI、普通preview及写回身份、投影错误与观察重入、3544dc父合同、分组mutation、Stack失效/owner、选区观察及04430c/0f733c仍开放。该比例只描述v20有限差异，不是全产品迁移完成度，整体目标继续进行。

主智能体独自修改，复用1个既有低模型智能体只读核原链和当前生产调用。未编译、构建、运行框架/数据库/应用、联网、安装、提交或发布；官网9文件、1.0.2、HEAD与function-map保持。

[机器记录](p0-p1-repair-round90.json) · [源码补丁](p0-p1-repair-round90.patch) · [有限差异清单v20](p0-p1-difference-backlog-v20.json)
