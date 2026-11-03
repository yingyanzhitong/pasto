import AppKit
#if canImport(FoundationModels)
import FoundationModels
#endif

@MainActor
public enum OriginalWritingTools {
    /// Paste 0x1002171cc: model availability on 26+, selector support on 15.2–25.
    public static func isAvailable() -> Bool {
        if #available(macOS 26, *) {
            #if canImport(FoundationModels)
            return SystemLanguageModel.default.availability == .available
            #else
            return false
            #endif
        }
        guard #available(macOS 15.2, *) else { return false }
        return NSText.instancesRespond(to: NSSelectorFromString("showWritingTools:"))
    }

    /// The nil-sender callers of 0x1002160fc. Both sleep continuations send the action.
    public static func showAfterDelay() {
        Task { @MainActor in
            try? await ContinuousClock().sleep(for: .milliseconds(500))
            if #available(macOS 15.2, *) {
                NSApp.sendAction(NSSelectorFromString("showWritingTools:"), to: nil, from: nil)
            }
        }
    }
}
