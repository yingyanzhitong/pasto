import AppKit
import Foundation

public enum OriginalPasteboardPolicies {
    public static let accessRequestNotification = Notification.Name("pasteboardHistoryManagerDidRequestAccess")

    public static func permitsBackgroundRead(_ pasteboard: NSPasteboard) -> Bool {
        if #available(macOS 15.4, *) {
            // The source uses accessBehavior (NSInteger) on 15.4+. Resolve the
            // same getter when building with an SDK that predates its header.
            let selector = NSSelectorFromString("accessBehavior")
            guard pasteboard.responds(to: selector), let implementation = pasteboard.method(for: selector) else {
                return false
            }
            typealias Getter = @convention(c) (AnyObject, Selector) -> Int
            let getter = unsafeBitCast(implementation, to: Getter.self)
            return getter(pasteboard, selector) == 2
        }
        return true
    }

    public static func f_10037b278(_ first: Set<String>, _ second: Set<String>) -> Bool {
        first == second
    }

    @MainActor
    public static func f_10037ba14(allTypes: [String], excludedApplications: Set<String>, ignoredTypes: Set<String>,
                                  diagnostics: OriginalNamedDiagnostic) -> Bool {
        guard let sourceBundleID = NSWorkspace.shared.frontmostApplication?.bundleIdentifier else {
            diagnostics.f_1000d468c().f_1000d4db8("Undefined frontmost application, skipping pasteboard change")
            return false
        }
        let ignored = sourceBundleID == "org.mozilla.firefoxdeveloperedition"
            ? excludedApplications.contains(sourceBundleID)
            : excludedApplications.contains { sourceBundleID.contains($0) }
        if ignored {
            diagnostics.f_1000d468c().f_1000d4db8("Ignored application \(sourceBundleID), skipping pasteboard change")
            return false
        }
        for type in allTypes {
            if ignoredTypes.contains(where: { type.contains($0) || $0.contains(type) }) {
                diagnostics.f_1000d468c().f_1000d4dd4("Ignored pasteboard type \(type), skipping pasteboard change")
                return false
            }
        }
        return true
    }

    @MainActor
    public static func f_10037c22c(type: String, allTypes: [String]) -> Bool {
        let sourceBundleID = NSWorkspace.shared.frontmostApplication?.bundleIdentifier
        if sourceBundleID?.lowercased() == "com.microsoft.excel" {
            return ["public.utf16-plain-text", "public.utf8-plain-text"].contains(type)
        }
        if f_10037b278(Set(allTypes), ["public.file-url", "public.png"]), type == "public.file-url" {
            return false
        }
        // The last identifier is truncated in the original static string too.
        return !["com.microsoft.ObjectLink", "com.microsoft.Link-Source", "com.microsoft.DataObjec"].contains(type)
    }

    public static func permitsRemoteType(_ type: String, allTypes: [String]) -> Bool {
        !allTypes.contains("com.apple.is-remote-clipboard")
            || ["public.utf8-plain-text", "public.text", "public.rtf"].contains(type)
    }
}
