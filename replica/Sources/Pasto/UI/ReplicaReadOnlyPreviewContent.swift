import AppKit
import PastoCore
import SwiftUI

/// Content only: the native preview factory supplies the header and footer.
/// Nontext editing and the original per-kind metadata remain separate dependencies.
@MainActor
func makeReplicaReadOnlyPreviewContent(store: ClipboardStore, item: ClipboardItem) -> NSView {
    NSHostingView(rootView: ReplicaReadOnlyPreviewContent(store: store, itemID: item.id))
}

@MainActor
private struct ReplicaReadOnlyPreviewContent: View {
    @ObservedObject var store: ClipboardStore
    let itemID: UUID

    var body: some View {
        Group {
            if let item = store.items.first(where: { $0.id == itemID }) {
                if item.kind == .image, let image = itemImage(item) {
                    OriginalImageTextSelection(item: item, image: image)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if item.kind == .files {
                    fileContent(urls: itemFileURLs(item))
                } else {
                    ScrollView {
                        ReplicaItemContent(item: item, compact: false,
                                           linkPreviewsEnabled: store.preferences.linkPreviewsEnabled)
                            .textSelection(.enabled)
                            .frame(maxWidth: .infinity, alignment: .topLeading)
                            .padding(8)
                    }
                }
            } else {
                ContentUnavailableView("项目不存在", systemImage: "doc.questionmark",
                                       description: Text("这个项目已被移除。"))
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    @ViewBuilder
    private func fileContent(urls: [URL]) -> some View {
        // Original FileItemContentView installs Quick Look only for one URL.
        if urls.count == 1, let url = urls.first {
            if FileManager.default.fileExists(atPath: url.path) {
                NativeFilePreview(url: url)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                ContentUnavailableView("文件不可用", systemImage: "doc.questionmark",
                                       description: Text("文件可能已移动或删除。\n\(url.lastPathComponent)"))
            }
        } else if let image = NSImage(named: NSImage.multipleDocumentsName) {
            Image(nsImage: image)
                .resizable()
                .scaledToFit()
                .frame(width: 160, height: 160)
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
    }
}
