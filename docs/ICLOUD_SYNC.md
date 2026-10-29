# iCloud Drive 同步

免费开发者路径下的可选同步功能，无需 Apple Developer 付费会员或原厂账号，也不使用原版 Paste 的 CloudKit 容器。会占用你自己的 iCloud 存储空间；已发布的 1.0.0 不含此功能。

这是独立的文件同步，**不是原版 CloudKit 同步的复刻**。用户已选择此方式作为主要入口，原版 CloudKit 代码保留供自有签名构建使用，见 [CloudKit 迁移与测试](CLOUDKIT_MIGRATION.md)。本页的检查及 File Provider 上传证据只适用于文件同步，不能计入 CloudKit 验收。

## 开启与使用

1. 在每台 Mac 的系统设置中登录同一 Apple ID，并开启 iCloud Drive。
2. 使用包含最新改动的 Pasto 构建，进入 **设置 → 通用**，打开 **iCloud 同步** 开关即可；没有设置弹窗、文件夹选择或额外确认。
3. 应用自动创建并使用 `iCloud Drive/Pasto`；另一台 Mac 登录同一 Apple ID 并打开相同开关。
4. 首次合并已有内容，应用运行期间每 30 秒重试同步。开关旁显示简短状态，悬停可查看具体提示。若无法开启，先确认系统已开启 iCloud Drive，且同步目录可访问；应用不会伪造或创建系统的 iCloud 根目录。

默认关闭，不自动上传现有历史。设置页显示“iCloud Drive 数据已更新”只表示本次本地协调读写完成；实际上传、下载与设备间到达时间由 macOS 的 iCloud Drive 服务决定，不能据此认定另一台设备已收到。

开启后重新启动应用会恢复同步；关闭后重启保持关闭，反复切换开关不会重置设备同步身份。旧版本明确保存过的自定义目录继续使用，不会因升级而遗弃旧云文档；这类已有配置的其他 Mac 仍需指向原来的相同目录。新配置统一使用固定的 `Pasto` 目录。

## 范围与数据保护

- 同步保存的文本、富文本、图片等内容，以及来源信息、分组颜色、名称、顺序和成员关系。
- 快捷键、权限、排除规则、暂停、历史保留期限及 Stack 队列留在本机。某台 Mac 实际清理掉的历史仍会作为删除同步给其他设备，建议设置一致的保留期限。
- 文件路径不等于原文件传输：另一台 Mac 需要自行持有相应文件。
- 同一条记录同时编辑时，按时间、序号和设备标识确定一个较新版本，整条记录采用该版本；不同记录的修改可以保留。设备时钟异常可能影响冲突选择。
- 每台 Mac 写自己的文档；删除使用明确标记，未下载、暂时缺失或被用户移走的文档不表示清空数据。不要手动修改 `PastoSync-v1` 内部文件。
- 关闭同步不会删除本地或云端数据。默认关闭和普通启动都不会创建同步目录。
- 关闭同步会停止应用后续同步，不能撤回已经交给 macOS 处理的上传。首次开启旧归档时，不把开启时间当成新编辑，避免覆盖另一台 Mac 已经跟踪的新版本。
- 同步文档是明文，受 iCloud Drive 文件夹的访问和共享设置约束；不要将 Pasto 同步目录共享给其他人。大图片会增加空间与传输开销。

应用不需要原版 Paste 的凭据或 CloudKit 容器。本实现使用 iCloud Drive 中的 Pasto 文件夹，通过 Foundation `NSFileCoordinator` 读写文档，而不是在临时签名应用里伪造 CloudKit 权限。

## 验证

隔离测试：

```sh
bash replica/scripts/test-icloud-sync.sh
```

默认仅使用临时目录和合成内容，不访问真实 iCloud Drive 或系统剪贴板。`bash replica/scripts/test-icloud-drive-controller.sh` 覆盖默认不创建云目录、开关自动建目录、重启恢复、双客户端合并、删除传播、不可用云根目录、同名文件保护、越界符号链接、旧自定义路径兼容、取消排队任务及关闭状态持久化。同步核心和原生界面分别由同步脚本和 `test-ui-interaction.sh` 验证；本次结果见 [单开关验证](../reports/replica/icloud-single-switch-verification.md)。未变化实体复用原协议的摘要，payload 改动会使缓存失效，冷启动重新计算结果保持一致。历史版本的架构检查不计作当前源码的重新验证。

显式真实 iCloud Drive 探针：

```sh
bash replica/scripts/test-icloud-sync.sh --live-icloud
```

只创建独立的 `Pasto Sync Verification <随机标识>` 文件夹，写入生成的测试记录，检查系统上传状态和回读，结束时清理自己的测试目录，不读取或上传用户历史。Foundation 的上传状态接口不可用时，探针通过 macOS 自带的 `fileproviderctl evaluate` 独立核验自己的测试文件；正式应用不依赖或调用此命令。

本机检查发现：合成同步文档被识别为 iCloud 文档，协调写入及回读匹配。Foundation 上传状态接口返回 `NSCocoaErrorDomain 4355`，但 macOS File Provider 独立报告该同步文档 `isUploaded = 1`，真实上传探针通过；此前账户不可访问的提示未能证明需要重新登录。应用允许在上传状态元数据不可用时读取已下载文档，避免离线期间阻止已有内容合并。测试生成的云目录已清理。

当前没有第二台物理 Mac 的通过记录，不宣称跨设备端到端验收全部完成。真实跨设备验收还需：在两台 Mac 上分别新增、修改及删除合成内容，核对分组和原始内容；断开网络后分别编辑，恢复后验证收敛；确认关闭同步和退出账户后的状态。不要用用户真实剪贴板作为测试数据。

## 开源实现对照

核对版本：`IvyGain/Pasty@5ec620b` 的 [CloudSyncEngine](https://github.com/IvyGain/Pasty/blob/5ec620baa4eefa16531535ac03bc2dd11bb52954/Sources/Pasty/CloudSyncEngine.swift) 仍为占位实现，不能作为真实同步通过的依据。近似名称项目 `momenbasel/pesty@46031a5` 的 [ClipboardStore](https://github.com/momenbasel/pesty/blob/46031a544ce8b0fcb85851f28ece60b16eb74a3a/Sources/Pesty/Store/ClipboardStore.swift) 在直接下载构建中使用固定的 iCloud Drive/Pesty 目录，由开关切换。Pasto 参考固定目录与单开关交互，继续使用自己的本地数据库、按设备同步文档和合并协议，没有复制该项目代码。
