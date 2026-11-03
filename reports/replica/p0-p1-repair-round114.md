# 第一百一十四轮：Stack 按行传递原生实体与读取预览

原085324 tableView:viewForTableColumn:row:进入086658，从snippets[row]加载并retain实体，然后以同对象调用0519f8。Cell按有无outlet先由051d2c/31eba8取rawType图标，再设两行，最后051ec8/31ebc8读取rawPreview并解码文字；没有先把整个队列转DTO或按UUID重查。

本轮Core table以strong ClipboardRestoreItem数组存行，makeNativeCell在请求行时收到对应句柄。snippets值属性、makeCell和旧update/insert/consume接口保留shim，原生路径的IDs、count、height和通知只使用句柄。State依既有stackIDs顺序返回强持输入或旧值wrapper，不去重；capture和多选加入不再先resolvedItem。插入、反转、head消费和SwiftUI刷新都交同native数组，保既有动画顺序、revision/stale-row适配。

Cell保现有布局，按原outlet顺序读取图标和文字。Native icon直接读当前rawType，Native文字直接读当前rawPreview；原text/link/image Unknown/color/files格式分支抽成共享函数，经严格源码重构比较与旧分支完全相同，多文件标题才懒读同句柄previewTitle。旧值renderer和初始化接口保留。上下文copy/preview仍在用户动作时使用值适配，未称该路径也已完整native。

10原片段、13真实branch、5ARM字及5选择器绑定，12既有方法和5共享源保持。6生产文件26精确增量，241生产文件不变，cell layout及table初始化原文保持；3处Swift旧调用源码作静态接口对照，未改或运行。既有低模型只读复核同实体/顺序/访问级别/闭包及tuple比较，无明确源码问题。

24新增检查，最终1755项Python源码/Mach-O静态检查全绿。首轮5项旧源码快照断言失败，通过4历史测试和1链工具仅逆隔离本轮增量修复，初日志保存。初编辑脚本因两处相同行匹配停止，后续只在当前文件等于已知中间态时继续；无用户文件回滚。证据脚本init定位曾混入self.init，已限定声明修正。没有Swift/框架/CoreData执行。

v36原样保留192条/175组，新增086658有效row输入和051ec8有效本地preview读取两有限合同，实际table→cell→formatter同entity链保守计1组；既有0519f8消费者额外修复不重计。P0 70/70、P1 124/124、总194/194（100%）。此分母是已确认有限差异，整体迁移及完整函数验收仍未完成。

永久删除/fault与原Stack owner/DI、Nib reuse/invalid-row traps、全部codec/重入、ID-only入口、UUID持久化/map适配和上下文动作仍开放；不因为避免DTO就自动清队列或称生命周期等价。分组旧成员兼容/blob/cache错误、其余选择/模型/image父合同及04430c/0f733c继续pending。P2及联网排除。

未编译、构建、安装、运行、联网、提交、推送、标签或发布。官网9份本地改动、1.0.2、HEAD和function-map保持。
