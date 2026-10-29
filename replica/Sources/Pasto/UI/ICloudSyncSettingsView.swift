import AppKit
import SwiftUI

@MainActor
struct ICloudSyncSettingsView: View {
    @ObservedObject var sync: ICloudDriveSyncController

    var body: some View {
        Form {
            Section("iCloud Drive") {
                Toggle("同步历史与收藏分组", isOn: Binding(get: { sync.isEnabled }, set: { sync.setEnabled($0) }))
                    .disabled(!sync.canSync)
                Text("同一 Apple ID 下，在其他 Mac 的 Pasto 中选择相同的 iCloud Drive 文件夹。默认关闭，开启后合并已有内容并同步新增、编辑和删除。")
                    .font(.caption).foregroundStyle(.secondary)
                if !sync.canSync {
                    Text("独立演示或测试数据目录不启用云同步，请在正常启动的 Pasto 中设置。")
                        .font(.caption).foregroundStyle(.secondary)
                }
            }
            Section("同步文件夹") {
                if let folder = sync.folderURL {
                    Text(folder.path).font(.caption).textSelection(.enabled)
                        .lineLimit(3).frame(maxWidth: .infinity, alignment: .leading)
                } else {
                    Text("尚未选择文件夹").foregroundStyle(.secondary)
                }
                HStack {
                    Button("选择文件夹…") { sync.chooseFolder() }.disabled(!sync.canSync || sync.isBusy)
                    if let folder = sync.folderURL {
                        Button("在 Finder 中显示") { NSWorkspace.shared.open(folder) }
                    }
                }
            }
            Section("同步状态") {
                HStack(alignment: .top) {
                    if sync.isBusy { ProgressView().controlSize(.small) }
                    Text(sync.statusText).font(.caption).textSelection(.enabled)
                }
                if let date = sync.lastSyncDate {
                    LabeledContent("最近更新", value: date.formatted(date: .abbreviated, time: .standard))
                        .font(.caption).foregroundStyle(.secondary)
                }
                Button("立即同步") { sync.syncNow() }.disabled(!sync.isEnabled || sync.isBusy)
            }
            Section("同步范围") {
                Text("同步文本、图片等已保存内容及收藏分组。快捷键、来源排除、权限、暂停和 Stack 队列保留在本机。文件路径对应的原始文件不会自动复制到其他 Mac。")
                    .font(.caption).foregroundStyle(.secondary)
                Text("同步文档以明文保存到你的 iCloud Drive，会占用 iCloud 空间。关闭同步不会删除任何一侧的内容；跨设备到达时间由 iCloud Drive 决定。")
                    .font(.caption).foregroundStyle(.secondary)
            }
        }.formStyle(.grouped)
    }
}
