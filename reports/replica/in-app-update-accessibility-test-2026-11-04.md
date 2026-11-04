# Sparkle 更新后的辅助功能授权测试

测试于 2026-11-04 在本机 macOS 26.2 完成。

## 结果

“更新后无需重新授权”未通过。真实 Sparkle 更新安装及重启完成，更新后的应用没有继承原授权。

| 阶段 | 版本 | 系统 AXIsProcessTrusted 返回值 |
| --- | --- | --- |
| 手动授权后、开始更新前 | 1.0.0 | true |
| Sparkle 更新、重启后的新进程 | 1.0.1 | false |

从开始更新到新版进程启动约 4.421 秒。旧版 PID 为 62368，新版 PID 为 62437。系统设置中的开关在更新后仍显示开启，但新版进程报告未受信任。

## 测试条件

- 使用独立的 Pasto Update Test 应用，Bundle ID 和安装路径在两版本间保持一致。
- 使用与当前 Pasto 相同的临时签名模式，Sparkle 2.10.1 下载完整 DMG，验证 Ed25519 签名后解包、安装及重启。
- 更新源与安装包由本机 127.0.0.1 服务提供，测试更新源和 DMG 均经过签名。该临时 HTTP 地址仅用于本机隔离测试，正式应用保持 GitHub HTTPS 更新地址。
- 测试前经用户确认，在系统设置给旧版授权，并在进程内验证返回 true。未以系统设置开关外观代替真实系统接口检测。
- 旧版和新版临时签名 DR 不兼容，双向 codesign 要求测试均以状态 3 失败。未更改系统 TCC 数据库，未重置权限。
- 未更换用户正在使用的 /Applications/Pasto.app，未访问剪贴板历史。测试结束后已移除测试应用的辅助功能授权，并停止隔离应用和本机更新服务。

## 证据

项目忽略目录 `.local/sparkle/permission-update-test/` 保留 `events.jsonl`、`result.json`、两版本签名及 DR 输出、`identity-comparison.json`、测试源码和签名 DMG。`events.jsonl` 包含 begin-update、download、extract、install-and-relaunch、installing 和新版 launch 记录，以及进程内授权状态。

该结果验证本机临时签名构建的实际行为。Developer ID 签名版本及其他 macOS 版本未在本轮测试。

Apple 对临时签名与跨版本身份的说明见 [TN3127](https://developer.apple.com/documentation/technotes/tn3127-inside-code-signing-requirements)。
