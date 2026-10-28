import AppKit

/// The original animates its entire MainView in an unflipped window coordinate space.
/// Hosting and the top resize handle remain children of that same moving content.
@MainActor
final class ReplicaPanelContentView: NSView {
    var canInterpretSearchInput: (() -> Bool)?
    var onSearchText: ((String) -> Void)?
    override var isFlipped: Bool { false }

    private var collectionFocusTarget: NSView? {
        guard let panel = window as? ReplicaPanel, let collection = panel.collectionFocusTarget,
              collection.window === panel else { return nil }
        return collection
    }

    override func becomeFirstResponder() -> Bool {
        guard let window, let collectionFocusTarget else { return false }
        return window.makeFirstResponder(collectionFocusTarget)
    }

    override func viewDidMoveToWindow() {
        super.viewDidMoveToWindow()
        if let window, let collectionFocusTarget {
            window.initialFirstResponder = collectionFocusTarget
        }
    }

    override func mouseDown(with event: NSEvent) {
        super.mouseDown(with: event)
        if let window, let collectionFocusTarget {
            window.makeFirstResponder(collectionFocusTarget)
        }
    }

    @discardableResult
    func tryInterpretSearchKeyEvent(_ event: NSEvent) -> Bool {
        guard canInterpretSearchInput?() == true,
              event.modifierFlags.intersection([.command, .control, .function]).isEmpty,
              event.specialKey == nil, let characters = event.characters, !characters.isEmpty,
              characters.unicodeScalars.allSatisfy({
                  !CharacterSet.controlCharacters.contains($0) && !(0xF700...0xF8FF).contains(Int($0.value))
              }) else { return false }
        keyDown(with: event)
        return true
    }

    override func keyDown(with event: NSEvent) {
        if super.performKeyEquivalent(with: event) { return }
        let specialKey = event.specialKey
        if specialKey == .tab || specialKey == .backTab {
            super.keyDown(with: event)
        } else {
            interpretKeyEvents([event])
        }
    }

    override func insertText(_ insertString: Any) {
        guard let text = insertString as? String, text != " " else { return }
        onSearchText?(text)
    }
}
