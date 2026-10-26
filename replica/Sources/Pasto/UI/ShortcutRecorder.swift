import SwiftUI
import PastoCore

@MainActor
struct ReplicaShortcutRecorder: View {
    @Binding var shortcut: PastoCore.KeyboardShortcut?
    let label: String
    let error: (String) -> Void
    let recordingChanged: (Bool) -> Void

    var body: some View {
        OriginalShortcutRecorderView(shortcut: Binding(get: { shortcut?.originalValue }, set: { value in
            shortcut = value.flatMap { PastoCore.KeyboardShortcut(originalValue: $0) }
        }), errorChanged: error, recordingChanged: recordingChanged)
        .accessibilityLabel("\(label)快捷键")
        .accessibilityValue(shortcut.map {
            OriginalShortcutFunctions.f_1001e9774(verbose: true, modifierRawValue: $0.modifierRawValue)
                + OriginalShortcutFunctions.f_1001e7e50(keyCode: $0.keyCode)
        } ?? "")
        .onDisappear { recordingChanged(false) }
    }
}
