import AppKit

/// Recovered Stack table behavior. Presentation of an individual replica item is supplied by the UI.
@MainActor public final class OriginalStackTableController: NSObject, NSTableViewDataSource, NSTableViewDelegate {
    public let tableView: NSTableView
    public let scrollView: NSScrollView
    public var snippets: [ClipboardItem] = []
    public var makeCell: ((ClipboardItem) -> NSView)?
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

    public func f_100085230() -> Int { snippets.count }
    public func f_100085670(row: Int) -> Bool { false }

    public func numberOfRows(in tableView: NSTableView) -> Int { f_100085230() }
    public func tableView(_ tableView: NSTableView, shouldSelectRow row: Int) -> Bool { f_100085670(row: row) }
    public func tableView(_ tableView: NSTableView, viewFor tableColumn: NSTableColumn?, row: Int) -> NSView? {
        guard snippets.indices.contains(row) else { return nil }
        return makeCell?(snippets[row])
    }
}
