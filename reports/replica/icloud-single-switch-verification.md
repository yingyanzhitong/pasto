# iCloud 单开关验证

日期：2026-10-29；本地源码与本机安装验证，未提交或发布。

## 完成内容

- 通用页仅保留 iCloud 同步开关和简短状态；移除“设置…”、详情弹窗、文件夹选择与确认弹窗。
- 首次开启自动使用 `iCloud Drive/Pasto`。默认关闭，未开启时不创建云目录。
- 保留旧自定义目录及同步身份；关闭后保留两侧内容。目录不可用时保持关闭并在行内提示，可悬停查看说明。
- 删除不再使用的详情视图，现有 CloudKit 引擎代码继续保留；没有新增 CloudKit 设置入口。

## 当前源码验证

| 检查 | 结果 |
| --- | --- |
| 同步控制器 | 23 项通过：自动目录、默认关闭、恢复及身份、合并与删除、旧路径、目录不可用、文件保护、越界链接、取消与关闭持久化 |
| 文件同步核心 | 38 项通过：两个隔离客户端与合成共享目录 |
| 原生界面回归 | 通过：渲染实际同步行及既有复制、分组、Stack、关闭行为 |
| Release 原生构建与签名校验 | 通过 |
| 本机安装与启动 | `/Applications/Pasto.app` 已更新；通用页实际 AX 与截图确认只有同步开关，无设置按钮或侧栏同步项 |
| 数据保护 | 更新前完成数据与应用备份；更新后 SQLite 完整性与记录/分组数量检查通过，保持已存保留期限及关闭的同步状态 |

本轮没有开启真实用户历史同步，没有上传用户剪贴板；没有重新进行真实云上传探针或第二台物理 Mac 验证。之前的合成上传证据只属于文件同步，不等于本轮跨设备或原版 CloudKit 验收。未增加任何原版完整函数迁移计数。

## 参考实现

- [Pasty CloudSyncEngine](https://github.com/IvyGain/Pasty/blob/5ec620baa4eefa16531535ac03bc2dd11bb52954/Sources/Pasty/CloudSyncEngine.swift)：目前是占位实现。
- [Pesty ClipboardStore](https://github.com/momenbasel/pesty/blob/46031a544ce8b0fcb85851f28ece60b16eb74a3a/Sources/Pesty/Store/ClipboardStore.swift)：直接下载构建使用固定 iCloud Drive 子目录，由开关切换；本轮仅参考该交互方式，没有复制其源码。
