import AppKit
import Foundation

/// REA 0x100011138: the controller's windowDidLoad implementation, including super.
@MainActor public final class OriginalStackWindowController: NSWindowController {
    public static let stackFrameAutosaveName = "com.wiheads.paste.paste-stack-frame"

    public override func windowDidLoad() { f_100011138() }

    public func f_100011138() {
        super.windowDidLoad()
        window?.level = .statusBar
        window?.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        window?.isMovableByWindowBackground = true
        window?.setFrameAutosaveName(Self.stackFrameAutosaveName)
    }
}

/// Address-level reconstructions used by the real UI, not placeholder exports.
public enum OriginalStackFunctions {
    @MainActor public static func f_1000114ec() -> Bool { f_1000114fc() }
    @MainActor public static func f_1000114f4() -> Bool { f_1000114fc() }

    /// Original helper checks MainActor isolation and returns false for both window selectors.
    @MainActor public static func f_1000114fc() -> Bool { false }

    /// Original in-place reversal swaps both ends and preserves Swift Array copy-on-write.
    /// The decompiler's ulong return is an ABI recovery artifact; callers use the mutated array.
    public static func f_10008468c<T>(_ values: inout [T]) { values.reverse() }
}
