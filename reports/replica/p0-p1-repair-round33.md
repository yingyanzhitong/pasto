# P0/P1 源码修复：第三十三轮

继续先修P0，再检查P1，最后修P1。本轮恢复剪贴板项的序列化兼容运行时名称。

原Item类元数据绑定_TtC9PasteCore14PasteboardItem，真实dyld父类绑定NSObject，全部四个实例方法不含classForCoder/classForArchiver/classForKeyedArchiver覆盖。当前类型此前仅使用PastoCore.OriginalPasteboardItem默认命名。现添加原ObjC兼容名注解，实际归档对象仍是同一Swift类型；NSArray根、nonsecure convenience API、types/data和MD5路径不变。未换成代理归档类或全局类名映射。

本机macOS26.2缓存的静态证据将NSObject三层默认归档类选择、归档器instance/class映射检查、$classname与$classes写入及class_getName真实导入串联。libobjc旧Swift类名解析器对_TtC模块/类型长度解析后使用%.*s.%.*s格式。原元数据由此在正常默认、无swizzle/映射环境下对应PasteCore.PasteboardItem及NSObject父类名。没有把已有解码alias当编码样本。

为保留旧Pasto本地归档，decodeItems增加PastoCore.OriginalPasteboardItem及其mangled名的实例解码映射；既有原版两名继续保留。Swift源码类型名、显示品牌和JSON/plist的Codable键不变。

| 已确认有限差异 | 已修复 | 分母 | 比例 |
| --- | ---: | ---: | ---: |
| P0 | 60 | 69 | 86.96% |
| P1历史依赖 | 8 | 81 | 9.88% |
| 合计 | 68 | 150 | 45.33% |

计旧322ae4及其3216bc共享fallback身份记录2条，属于同一根因，不是2个独立功能/bug。余P0 9、P1 73，共82条差异及2未知。完整函数迁移仍false，原始v7清单不改写。注解的编译/链接/运行时注册、归档对象图/字典顺序、Foundation版本及最终MD5字节没有运行验证；不能把类名源码修复升级为全字节等价。

516项Python源码/C/Mach-O数据检查通过，新增8项；6个原函数片段、原类NSObject绑定和全部实例方法、262个系统缓存字节块共18,919字节及6个真实方法入口已绑定。2个旧生产文件变化、225个不变；1个旧测试精确允许注解和旧解码别名，其他原约束保留。初次新测试误以为Ghidra片段保留了key立即数，改为读取真实ARM MOVZ/MOVK参数后通过，首次日志保留；生产未为错误断言回退。

数据与删除安全仍唯一in_progress，继续恢复/删除父合同及实体生命周期；P1尚未开始独立检查。未编译、构建、安装、运行应用/框架、联网、提交、推送或发布。官网9文件、1.0.2、HEAD及function-map不变。见[JSON](p0-p1-repair-round33.json)、[补丁](p0-p1-repair-round33.patch)。
