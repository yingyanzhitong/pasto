import AppKit
import SwiftUI

/// Paste 0x10005889c / 0x100058d74: fixed sidebar and content split items.
@MainActor
struct OriginalSettingsSplitView: NSViewControllerRepresentable {
    let sidebar: AnyView
    let detail: AnyView

    func makeNSViewController(context: Context) -> NSSplitViewController {
        let controller = NSSplitViewController()
        let navigation = NSSplitViewItem(sidebarWithViewController: NSHostingController(rootView: sidebar))
        navigation.canCollapse = false
        navigation.minimumThickness = 200
        navigation.maximumThickness = 200
        let content = NSSplitViewItem(viewController: NSHostingController(rootView: detail))
        content.minimumThickness = 440
        content.maximumThickness = 440
        controller.splitViewItems = [navigation, content]
        return controller
    }

    func updateNSViewController(_ controller: NSSplitViewController, context: Context) {
        (controller.splitViewItems[0].viewController as! NSHostingController<AnyView>).rootView = sidebar
        (controller.splitViewItems[1].viewController as! NSHostingController<AnyView>).rootView = detail
    }
}
