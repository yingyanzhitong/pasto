# 应用内更新

1.0.6 起入口位于“关于 Pasto”。检查更新读取 GitHub 最新正式 Release，确认后使用 Sparkle 2.10.1 的原生界面下载、安装和重启。更新包使用完整 Universal DMG，兼容 Intel 和 Apple 芯片。

已发布的 1.0.5 及更早版本没有此功能，需要先手动安装 1.0.6。应用内更新代码、打包和签名测试与真实线上版本升级验收分别记录。

## 更新源与签名

- 更新源地址固定为 `https://github.com/yingyanzhitong/pasto/releases/latest/download/appcast.xml`，跟随最新正式 Release，预发布不会改变此地址的目标。
- 发布时使用 Sparkle 官方 `sign_update`，对 DMG 和 appcast 分别进行 Ed25519 签名。公钥固定在 `replica/Assets/UpdatePublicKey.txt`，写入应用的 `SUPublicEDKey`。
- `SURequireSignedFeed` 和 `SUVerifyUpdateBeforeExtraction` 开启，更新源及安装包验证成功后才能解包和安装。发布脚本也会使用嵌入公钥验证归档签名，阻止错误私钥发布。
- 私钥通过 `PASTO_UPDATE_PRIVATE_KEY` Actions Secret 提供，是 Base64 编码的 32 字节 Ed25519 seed。签名工具从标准输入接收私钥，私钥不放入命令行、应用或仓库。
- Sparkle 二进制框架及签名工具固定版本和 SHA-256。框架中的符号链接、更新辅助程序及原始许可随应用打包。

应用启动时不会自动安装更新。打开“关于 Pasto”会异步读取版本摘要，六小时内复用结果。用户点击“下载并安装”后由 Sparkle 显示更新过程。安装前的正常退出会经过已有 `applicationShouldTerminate` 数据保存逻辑，保存失败时取消退出。

## 发布

正式版 Actions 在原有 Universal DMG、SHA256SUMS.txt 和 release-manifest.json 之外上传 appcast.xml。所有附件上传后下载核对，再公开 Release。缺失私钥或私钥与嵌入公钥不匹配时，正式版构建失败，阻止发布不可信更新源。

本地验证签名时，从项目外的安全存储将私钥传入进程环境，不在终端输出私钥。可以通过 `create-update-feed.py --archive <DMG路径> --version <正式版本>` 生成更新源。更新密钥必须持久备份，重新生成公钥会导致已经安装的客户端无法信任后续更新，轮换需遵循 Sparkle 的密钥迁移流程。

## 辅助功能授权

更新包的 Ed25519 签名用于证明下载来源。macOS 通过应用的代码签名身份判断辅助功能权限归属。当前应用仍为临时签名，因此更新后可能需要重新开启辅助功能授权。稳定保留授权需要相容的 Developer ID 签名身份和 Bundle ID，并经过真实跨版本更新验证。

参考 [Sparkle 更新发布文档](https://sparkle-project.org/documentation/publishing/) 和 [Apple 代码签名身份说明](https://developer.apple.com/documentation/technotes/tn3127-inside-code-signing-requirements)。

## 本机实测

2026-11-04 的隔离应用实测完成了 Sparkle 下载、安装及重启。更新前系统授权返回 true，更新后的新进程返回 false，当前临时签名构建未通过“更新后无需重新授权”验收。详情见 [测试记录](../reports/replica/in-app-update-accessibility-test-2026-11-04.md)。
