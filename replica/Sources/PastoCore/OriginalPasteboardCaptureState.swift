import AppKit
import Foundation
import OSLog

@MainActor
public protocol OriginalPasteboardCaptureDelegate: AnyObject {
    func originalPasteboardShouldRead(_ types: [String]) throws -> Bool
    func originalPasteboardDidRead(_ state: OriginalPasteboardCaptureState) throws
}

/// Local replacement for the original lazy logger dependency. Resolving the
/// sink is deferred until the first diagnostic, as in the source initializer.
public protocol OriginalPasteboardEventLogging {
    func record(scope: String, message: String)
}

private struct OriginalLocalPasteboardEventLogger: OriginalPasteboardEventLogging {
    func record(scope: String, message: String) {
        Logger(subsystem: "com.pastereplica", category: scope).debug("\(message, privacy: .public)")
    }
}

extension OriginalDependencyValues {
    public var pasteboardEventLogging: any OriginalPasteboardEventLogging {
        OriginalLocalPasteboardEventLogger()
    }
}

@MainActor
public final class OriginalPasteboardLogDependency {
    private let dependency = OriginalDependency(\OriginalDependencyValues.pasteboardEventLogging)

    public func resolve() -> any OriginalPasteboardEventLogging {
        dependency.f_1000da768()
    }
}

@MainActor
public final class OriginalPasteboardCaptureState {
    private final class WeakState {
        weak var value: OriginalPasteboardCaptureState?
        init(_ value: OriginalPasteboardCaptureState) { self.value = value }
    }
    private static var active: [NSPasteboard.Name: WeakState] = [:]

    public let pasteboard: NSPasteboard
    public weak var delegate: (any OriginalPasteboardCaptureDelegate)?
    public var items: [OriginalPasteboardItem] = []
    public var lastChangeCount: Int
    public private(set) var lastWriteSucceeded = false
    var persistChangeCount: ((Int) -> Void)?
    public var pollTimer: Timer?
    public var syncTimer: Timer?
    public let diagnostics = OriginalNamedDiagnostic.f_1000d4624(name: "Pasteboard")
    public var diagnosticName: String { diagnostics.name }
    public let loggingDependency = OriginalPasteboardLogDependency()

    private init(pasteboard: NSPasteboard, changeCount: Int) {
        self.pasteboard = pasteboard
        self.lastChangeCount = changeCount == 0 ? pasteboard.changeCount : changeCount
    }

    public static func f_100378664(changeCount: Int, pasteboard: NSPasteboard = .general) -> OriginalPasteboardCaptureState {
        OriginalPasteboardCaptureState(pasteboard: pasteboard, changeCount: changeCount)
    }

    public func f_10037875c(_ items: [OriginalPasteboardItem]) {
        let objects = items.map { item -> NSPasteboardItem in
            let object = NSPasteboardItem()
            for type in item.f_10037da6c() {
                if let data = item.f_10037e5e0(forType: type) {
                    object.setData(data as Data, forType: NSPasteboard.PasteboardType(type))
                }
            }
            return object
        }
        pasteboard.clearContents()
        lastWriteSucceeded = pasteboard.writeObjects(objects)
        lastChangeCount = pasteboard.changeCount
        Self.current(for: pasteboard)?.lastChangeCount = lastChangeCount
    }

    public static func register(_ state: OriginalPasteboardCaptureState) {
        active[state.pasteboard.name] = WeakState(state)
    }

    public static func current(for pasteboard: NSPasteboard) -> OriginalPasteboardCaptureState? {
        active[pasteboard.name]?.value
    }
}
