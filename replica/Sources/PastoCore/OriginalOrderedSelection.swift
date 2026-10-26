/// The ordered index/anchor value used by the original collection's input manager.
public struct OriginalOrderedSelection: Equatable, Sendable {
    public var selectedIndexes: [Int]
    public var itemCount: Int
    public var anchor: Int?

    public init(selectedIndexes: [Int], itemCount: Int, anchor: Int?) {
        self.selectedIndexes = selectedIndexes
        self.itemCount = itemCount
        self.anchor = anchor
    }

    public static func mode(modifierFlags: UInt) -> UInt8 {
        if modifierFlags & 0x20000 != 0 { return 2 }
        return modifierFlags & 0x100000 != 0 ? 1 : 0
    }

    /// f_10022df78: normal, command-toggle, and anchored range selection.
    public mutating func select(_ index: Int, mode: UInt8) {
        guard index >= 0, index < itemCount else { return }
        if mode == 0 {
            selectedIndexes = [index]
            anchor = index
        } else if mode == 1 {
            if let existing = selectedIndexes.firstIndex(of: index) {
                guard selectedIndexes.count > 1 else { return }
                selectedIndexes.remove(at: existing)
                anchor = selectedIndexes.last
            } else {
                selectedIndexes.append(index)
                anchor = index
            }
        } else if let anchor {
            let range = min(anchor, index)...max(anchor, index)
            var kept: [Int] = []
            var group: [Int] = []
            for value in selectedIndexes {
                if let previous = group.last, abs(previous - value) != 1 {
                    if !group.contains(where: range.contains) { kept.append(contentsOf: group) }
                    group = []
                }
                group.append(value)
            }
            if !group.contains(where: range.contains) { kept.append(contentsOf: group) }
            if anchor < index { kept.append(contentsOf: range) }
            else { kept.append(contentsOf: range.reversed()) }
            selectedIndexes = kept
        }
    }
}
