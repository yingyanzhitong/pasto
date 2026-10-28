import AppIntents

/// One automatic shortcut with the seven recovered phrases; bundle metadata is still required.
struct PastoShortcutsProvider: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(
            intent: PastoCreateItemIntent(),
            phrases: [
                "Create \(.applicationName) item",
                "Save \(.applicationName) item",
                "Add \(.applicationName) item",
                "Create text item with \(.applicationName)",
                "New text item in \(.applicationName)",
                "Save to \(.applicationName)",
                "Add to \(.applicationName)"
            ],
            shortTitle: "Create Pasto Item",
            systemImageName: "square.and.pencil"
        )
    }
}
