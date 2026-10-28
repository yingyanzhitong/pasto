import AppKit

/// Recovered Stack table behavior. Presentation of an individual replica item is supplied by the UI.
@MainActor public final class OriginalStackTableController: NSObject, NSTableViewDataSource, NSTableViewDelegate {
    public let tableView: NSTableView
    public let scrollView: NSScrollView
    public var snippets: [ClipboardItem] = [] { didSet { snippetsRevision &+= 1 } }
    private var snippetsRevision: UInt = 0
    private var animatedSnippetsAwaitingRefresh: [ClipboardItem]?
    public var makeCell: ((ClipboardItem) -> NSView)?
    public var removeSnippet: (([UUID], Int) -> Bool)?
    public var removeActionTitle = ""
    private var heightConstraint: NSLayoutConstraint?

    public override init() {
        tableView = NSTableView(frame: .init(x: 0, y: 0, width: 264, height: 44))
        scrollView = NSScrollView(frame: tableView.frame)
        super.init()
        let column = NSTableColumn(identifier: .init("snippet"))
        column.width = 264
        tableView.addTableColumn(column)
        tableView.headerView = nil
        tableView.rowHeight = 44
        tableView.intercellSpacing = .zero
        tableView.backgroundColor = .clear
        tableView.columnAutoresizingStyle = .lastColumnOnlyAutoresizingStyle
        tableView.delegate = self
        tableView.dataSource = self
        scrollView.drawsBackground = false
        scrollView.hasVerticalScroller = true
        scrollView.autohidesScrollers = true
        scrollView.documentView = tableView
    }

    /// REA 0x100082b90: retain and reuse a height constraint on the enclosing scroll view.
    public func f_100082b90() -> NSLayoutConstraint {
        if let heightConstraint { return heightConstraint }
        let constraint = tableView.enclosingScrollView!.heightAnchor.constraint(equalToConstant: tableView.rowHeight)
        heightConstraint = constraint
        return constraint
    }

    /// REA 0x100083a20: the animator commits its constant on a later run-loop turn.
    public func f_100083a20() {
        let constraint = f_100082b90()
        constraint.animator().constant = tableView.rowHeight * CGFloat(min(10, max(1, snippets.count)))
        constraint.isActive = true
    }

    public func updateSnippets(_ values: [ClipboardItem]) {
        let preserveRemoval = animatedSnippetsAwaitingRefresh == values && snippets == values
        animatedSnippetsAwaitingRefresh = nil
        snippets = values
        if !preserveRemoval { tableView.reloadData() }
        f_100083a20()
    }

    public func didInsertSnippet(previousIDs: [UUID], updated: [ClipboardItem], at index: Int) {
        guard updated.count == previousIDs.count + 1, updated.indices.contains(index) else { return }
        var priorIDs = updated.map(\.id)
        priorIDs.remove(at: index)
        guard priorIDs == previousIDs else { return }
        if snippets.map(\.id) == previousIDs {
            snippets = updated
            animatedSnippetsAwaitingRefresh = updated
            NSAnimationContext.runAnimationGroup { context in
                context.duration = 0.15
                f_100083a20()
                tableView.insertRows(at: IndexSet(integer: index), withAnimation: .effectGap)
                if updated.count > 10 { tableView.scrollRowToVisible(index) }
            }
        } else {
            // The observed state may have reached the table before this notification.
            if snippets != updated {
                snippets = updated
                tableView.reloadData()
            }
            f_100083a20()
            if updated.count > 10 { tableView.scrollRowToVisible(index) }
        }
    }

    public func didConsumeHead(previousIDs: [UUID], remaining: [ClipboardItem]) {
        guard !previousIDs.isEmpty, Array(previousIDs.dropFirst()) == remaining.map(\.id) else { return }
        if snippets.map(\.id) == previousIDs {
            snippets = remaining
            animatedSnippetsAwaitingRefresh = remaining
            NSAnimationContext.runAnimationGroup { context in
                context.duration = 0.15
                tableView.animator().removeRows(at: IndexSet(integer: 0), withAnimation: .slideUp)
                tableView.scrollRowToVisible(0)
                f_100083a20()
            }
        } else {
            // A SwiftUI refresh may already have applied the model change.
            if snippets != remaining {
                snippets = remaining
                tableView.reloadData()
            }
            tableView.scrollRowToVisible(0)
            f_100083a20()
        }
    }

    public func f_100085230() -> Int { snippets.count }
    public func f_100085670(row: Int) -> Bool { false }

    public func tableView(_ tableView: NSTableView, rowActionsForRow row: Int,
                          edge: NSTableView.RowActionEdge) -> [NSTableViewRowAction] {
        guard edge == .trailing else { return [] }
        return [NSTableViewRowAction(style: .destructive, title: removeActionTitle) { [weak self] _, row in
            guard let self, self.snippets.indices.contains(row), let removeSnippet = self.removeSnippet else { return }
            let revision = self.snippetsRevision
            guard removeSnippet(self.snippets.map(\.id), row), self.snippetsRevision == revision else { return }
            self.snippets.remove(at: row)
            self.tableView.removeRows(at: IndexSet(integer: row), withAnimation: .slideUp)
            self.f_100083a20()
        }]
    }

    public func numberOfRows(in tableView: NSTableView) -> Int { f_100085230() }
    public func tableView(_ tableView: NSTableView, shouldSelectRow row: Int) -> Bool { f_100085670(row: row) }
    public func tableView(_ tableView: NSTableView, viewFor tableColumn: NSTableColumn?, row: Int) -> NSView? {
        guard snippets.indices.contains(row) else { return nil }
        return makeCell?(snippets[row])
    }
}
