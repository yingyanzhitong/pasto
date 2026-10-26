import Foundation

@MainActor
public final class OriginalSearchInputHistory {
    public struct Snapshot: Equatable {
        public let nodes: [OriginalSearchQueryNode]
        public let selection: NSRange

        public init(nodes: [OriginalSearchQueryNode], selection: NSRange) {
            self.nodes = nodes
            self.selection = selection
        }
    }

    private var undo: [Snapshot] = []
    private var redo: [Snapshot] = []
    private var timer: Timer?
    private var pending: Snapshot?
    public private(set) var current: Snapshot
    private let interval: TimeInterval

    public init(nodes: [OriginalSearchQueryNode] = [], interval: TimeInterval) {
        current = Snapshot(nodes: nodes, selection: NSRange(location: 0, length: 0))
        self.interval = interval
    }

    deinit { timer?.invalidate() }

    public func f_1002f5e18(_ snapshot: Snapshot, immediate: Bool) {
        guard snapshot != current else { return }
        if immediate {
            f_1002f5fe8()
            undo.append(current)
            current = snapshot
        } else {
            if pending == nil { pending = current }
            current = snapshot
            f_1002f60fc()
        }
        redo.removeAll()
    }

    public func f_1002f5fe8() {
        timer?.invalidate()
        timer = nil
        if let pending { undo.append(pending) }
        pending = nil
    }

    public func f_1002f60fc() {
        timer?.invalidate()
        timer = Timer.scheduledTimer(withTimeInterval: interval, repeats: false) { [weak self] _ in
            Task { @MainActor [weak self] in self?.f_1002f5fe8() }
        }
    }

    public func f_1002f61f0() -> Snapshot? {
        f_1002f5fe8()
        guard let snapshot = undo.popLast() else { return nil }
        redo.append(current)
        current = snapshot
        return snapshot
    }

    public func f_1002f63b8() -> Snapshot? {
        guard let snapshot = redo.popLast() else { return nil }
        undo.append(current)
        current = snapshot
        return snapshot
    }

    public func f_1002f6550() {
        undo.removeAll()
        redo.removeAll()
        timer?.invalidate()
        timer = nil
        pending = nil
    }
}
