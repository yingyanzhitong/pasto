import AppKit

/// The original search menu first drops rich-text groups, then keeps only the
/// four ordinary edit actions and separators. It does not normalize separators.
@MainActor
public enum OriginalSearchMenu {
    public static func f_10021b124(_ item: NSMenuItem) -> Bool {
        if item.action == NSSelectorFromString("changeLayoutOrientation:") { return true }
        if let menu = item.submenu,
           menu.items.contains(where: { $0.action == NSSelectorFromString("changeLayoutOrientation:") }) {
            return true
        }
        if let menu = item.submenu,
           menu.items.contains(where: { $0.action == NSSelectorFromString("highlight:") }) {
            return true
        }
        if let menu = item.submenu {
            for child in menu.items {
                if child.action == NSSelectorFromString("changeFont:") ||
                    child.action == NSSelectorFromString("orderFrontFontPanel:") ||
                    child.action == NSSelectorFromString("showFonts:") { return true }
            }
        }
        return false
    }

    public static func f_10021bf44(_ items: inout [NSMenuItem], from: Int, to: Int) {
        items.removeSubrange(from..<to)
    }

    @discardableResult
    public static func f_10021ad80(_ menu: NSMenu) -> Int {
        var items = menu.items
        if let first = items.firstIndex(where: f_10021b124) {
            var write = first
            for read in (first + 1)..<items.count where !f_10021b124(items[read]) {
                if read != write { items.swapAt(read, write) }
                write += 1
            }
            f_10021bf44(&items, from: write, to: items.count)
        }
        menu.items = items
        return 0
    }

    private static func isRetained(_ item: NSMenuItem, actions: Set<Selector>) -> Bool {
        if item.isSeparatorItem { return true }
        guard item.submenu == nil, let action = item.action else { return false }
        return actions.contains(action)
    }

    public static func f_10021c148(_ items: [NSMenuItem], actions: Set<Selector>) -> Int? {
        items.firstIndex { !isRetained($0, actions: actions) }
    }

    public static func f_10021c304(_ items: inout [NSMenuItem], actions: Set<Selector>) -> Int {
        guard let first = f_10021c148(items, actions: actions) else { return items.count }
        var write = first
        for read in (first + 1)..<items.count where isRetained(items[read], actions: actions) {
            if write != read { items.swapAt(write, read) }
            write += 1
        }
        return write
    }

    public static func f_10021b56c(_ menu: NSMenu) {
        f_10021ad80(menu)
        let actions = Set(["cut:", "copy:", "paste:", "selectAll:"].map(NSSelectorFromString))
        var items = menu.items
        let count = f_10021c304(&items, actions: actions)
        f_10021bf44(&items, from: count, to: items.count)
        menu.items = items
    }
}
