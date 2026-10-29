# Paste → Pasto：CloudKit 同步迁移与测试

当前仅为本地源码，未提交、安装或发布。**原版使用 CloudKit，不是此前独立实现的 iCloud Drive 文件同步；二者不等价。真实 CloudKit 云端验收尚未完成。**

## 原版证据与当前接入

依据已落盘的 REA/Ghidra 伪代码与原应用 `v10.mom` 模型，不访问原版用户数据库。证据文件、行号、函数片段摘要及当前源码摘要见 [证据清单](../reports/replica/cloudkit-migration-evidence.json)。

| 原版路径 | Pasto 当前接入 | 验证边界 |
| --- | --- | --- |
| `0x1003a2c80`：private/shared 两个 CKSyncEngine，独立序列化状态、订阅 | 实际 SDK 引擎与 delegate、作用域隔离、首次拉取后补传 | 已编译；真实服务端未验证 |
| `0x1003b1290` / `0x1003b27ec`：读取/保存 State.Serialization | JSON 序列化 checkpoint，与内容同一次本地事务保存；损坏状态重新拉取 | 本地持久化失败检查通过；真实引擎事件未运行 |
| `0x10038f904` / `0x10038fa04`：系统字段重建、属性与父引用 | CKRecord 系统字段归档、类型字段、父记录及级联引用 | 真实 CKRecord 离线往返通过 |
| `0x10038e594` / `0x1003b4edc`：外部二进制 → CKAsset | 原始剪贴板编码作为 ItemDataEntity.rawPasteboardItems 附件 | 百万字节 CKAsset 本地往返通过；未证明真实上传 |
| `0x1003b6618` / `0x1003b41b8` / `0x1003b4c14`：实体类型、身份与关系 | 六类实体、业务标识与引用映射；缺失关系暂存 | 已测试类型、身份、父子队列及乱序到达 |
| `0x100394f08`：冲突字段合并与 clipboard capacity 分支 | 保留服务器 system fields，较新字段合并与较小正数容量选择 | 仅覆盖已恢复的合同；全函数所有操作数及异常分支未闭合 |
| `0x10039c30c`：按发送 scope 筛选、父记录确认后发送 | 持久队列、父记录延迟、发送中再次编辑的 generation 隔离 | 隔离模拟回执通过；真实调度尚未验证 |
| `0x100398880` / `0x10039e014`：账户变化与同步元数据清理 | 清理状态并暂停，保留用户本地历史，重新开启需用户确认 | 本地状态检查通过；未真实退出 Apple ID |
| `0x100398d9c`：区域删除与首次拉取恢复 | 首轮忽略历史 zone deletion，后续按 scope 清理投影 | 本地状态检查通过 |
| `0x10039a8b8` / `0x10039e1a8`：拉取映射、回执、冲突与重试 | 两阶段关系投影、丢记录/区域恢复、SDK backoff；未闭合的破坏性错误保留编辑并停止 | 定向合同通过，不能标记整函数完整迁移 |

业务记录是 `DeviceEntity`、`ApplicationEntity`、`ListEntity`、`ListMetadataEntity`、`ItemEntity`、`ItemDataEntity`。不把整个 Pasto JSON 归档当作一条云端附件。`ObjectMetadata` / `ObjectPendingMapping` 的对应状态保存在本机，不当作业务记录上传。

## 明确差异与未完成项

- Pasto 使用自己的 CloudKit 容器及 `Pasto` zone；不复用原厂 team、容器或签名，不连接原版云数据。
- 2026-10-29 最新源码已切换自有 Core Data / SQLite 模型，文档、本地基线与检查点按变更保存；复制链路恢复保存、Undo 清理、恢复通知、退出激活的顺序。旧 JSON 保留为迁移备份。原版整个模型、全部关系与事务错误分支尚未逐一闭合，不能称 ABI/逐函数一比一。参见 [复制事务对齐报告](../reports/replica/copy-coredata-alignment.md)。
- 新建历史列表使用 Pasto 稳定 ID；ItemData/Metadata 子记录名采用 Pasto 自有稳定后缀。原版计算身份后缀、完整 parent 策略仍待进一步恢复，不能将其猜测标为原版合同。
- private/shared SDK 管道已接入，但完整 CKShare、接受邀请及共享协作 UI 未迁移；不能据此把共享协作标为支持。
- generic conflict 的 `rawType == 1` 分支仅在已恢复的 clipboard 合同中使用；图片、缺失日期及 ItemData 的未闭合冲突会保留本机编辑并暂停，不猜测服务器胜出后丢弃编辑。对所有实体类型的确切语义及全部错误分支仍需真实对照。不得把定向通过数解释为全冲突组合通过。
- 初始本地分组/来源没有原版时间戳时用较早的基线，避免把“开启同步时间”伪造为新编辑；本机权限、快捷键等偏好不上传。历史保留容量按原版 clipboard attributes 作为同步字段。
- 附件缓存按内容摘要复用并保留重试所需文件；与原版临时 UUID 路径不同，后续需补充受在途操作约束的回收策略。
- 当前签名预检有效身份为 **0**；未取得 Pasto 自有团队、CloudKit 容器和有效描述文件。没有真实 SDK 云端传输、两台物理 Mac、服务端冲突、限流或推送唤醒通过记录。

## 本地验证

```sh
bash replica/scripts/test-cloudkit-sync.sh
python3 replica/Tests/Native/test_cloudkit_signing.py
bash replica/scripts/test-cloudkit-live.sh --preflight
```

定向 harness 使用真实 CKRecord、CKAsset、引用和系统字段编码器，服务端由隔离的内存字典模拟；不初始化 CKContainer，不联网、不读用户历史。另编译真实探针以检查 SDK 调用，但编译不算执行。当前 **67 项合同检查通过、7 项签名配置校验通过**；最终构建和回归结果见[本轮验证记录](../reports/replica/cloudkit-sync-verification.json)。此前独立 iCloud Drive 的 33 项不计入以上数字。

## 接通自有 CloudKit 与真实合成数据探针

需要 Apple Developer 的有效团队、为 Pasto Bundle ID 开启 iCloud/CloudKit、创建自有容器和匹配的 macOS 描述文件，本机存在对应签名身份。私钥留在本机钥匙串；配置不写入 Git。参见 [Apple 官方 CKSyncEngine 示例](https://github.com/apple/sample-cloudkit-sync-engine) 的项目配置要求。

`replica/scripts/build-app.sh` 现支持可选环境变量：`PASTO_SIGNING_IDENTITY`、`PASTO_CLOUDKIT_PROFILE`（路径）、`PASTO_CLOUDKIT_CONTAINER`、`PASTO_CLOUDKIT_ENVIRONMENT`（默认 Development）。提供不全、过期或不匹配时拒绝构建；无这些配置时保持原有临时签名构建，并在设置中禁用 CloudKit。

真实探针另需 `PASTO_CLOUDKIT_TEST_BUNDLE_ID` 与开发环境描述文件匹配，再执行：

```sh
bash replica/scripts/test-cloudkit-live.sh --synthetic-only
```

探针在临时目录创建两个客户端，只访问随机 `Pasto-Verification-*` zone 的合成记录，验证新增、附件、更新、删除，随后清理自己的 zone。不会读取已安装 Pasto 的数据；不会修改原版容器。该测试即使通过，也只证明**一台 Mac 的两个客户端经过真实服务端交换**，不能替代第二台物理 Mac 的验收。

## 进度计数

本轮新增完整原函数计数为 **0**：上述复合函数均还有未闭合的分支或存储适配差异，未更新全局逐函数台账。历史台账标记为 **2.0315%（1,648 / 81,123）**，其部分摘要已过期，不是本轮重新核验的完整迁移率，也不是当前 CloudKit 完成率。新增隔离用例通过率不等于原函数迁移百分比。
