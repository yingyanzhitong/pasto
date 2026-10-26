import AppKit
import SwiftUI

@MainActor
public enum OriginalShortcutControlFunctions {
    /// Unknown characters are omitted, as in the original compact-map/reduce.
    public static func f_1001ef60c(_ modifiers: String) -> Text {
        let symbols: [Character: String] = ["⌃": "control", "⌥": "option",
                                             "⇧": "shift", "⌘": "command"]
        return modifiers.reduce(Text("")) { text, character in
            guard let name = symbols[character] else { return text }
            return text + Text(Image(systemName: name))
        }
    }

    @ViewBuilder
    public static func f_1001eda4c(_ presentation: (String, String?, Bool)) -> some View {
        if presentation.2 {
            f_1001ef60c(presentation.0).font(.footnote)
            Text(presentation.1 ?? "").font(.body)
        } else {
            Text(presentation.0).font(.body)
        }
    }

    public static func f_1001ee524() -> some View {
        Image(systemName: "xmark").font(.caption2)
    }

    @ViewBuilder
    public static func f_1001ed830(_ presentation: (String, String?, Bool), recording: Bool) -> some View {
        let label = HStack(spacing: 1) { f_1001eda4c(presentation) }
        if recording { label.help(OriginalShortcutMessages.value("general.action.cancel")) }
        else { label }
    }
}

public struct OriginalShortcutPrimaryButtonStyle: ButtonStyle {
    public init() {}

    public func f_1001ee748(_ configuration: Configuration) -> some View {
        let outline = RoundedRectangle(cornerRadius: 6, style: .continuous)
        return configuration.label
            .font(.body)
            .frame(width: 120, height: 24)
            .background(Color(nsColor: .controlColor))
            .clipShape(outline)
            .overlay(outline.stroke(.separator, lineWidth: 1))
    }

    public func makeBody(configuration: Configuration) -> some View { f_1001ee748(configuration) }
}

public struct OriginalShortcutRemoveButtonStyle: ButtonStyle {
    public init() {}

    public func f_1001ee604(_ configuration: Configuration) -> some View {
        configuration.label
            .font(.body)
            .foregroundColor(.primary.opacity(configuration.isPressed ? 0.5 : 0.85))
            .frame(width: 24, height: 24)
            .contentShape(Rectangle())
    }

    public func makeBody(configuration: Configuration) -> some View { f_1001ee604(configuration) }
}

/// The recovered label, primary style and assigned-only remove control.
@MainActor
public struct OriginalShortcutControls: View {
    public let presentation: (String, String?, Bool)
    public let state: OriginalShortcutRecorderState
    public let begin: () -> Void
    public let clear: () -> Void

    public init(presentation: (String, String?, Bool), state: OriginalShortcutRecorderState,
                begin: @escaping () -> Void, clear: @escaping () -> Void) {
        self.presentation = presentation
        self.state = state
        self.begin = begin
        self.clear = clear
    }

    @ViewBuilder
    public func f_1001ed1c4() -> some View {
        Button(action: begin) {
            OriginalShortcutControlFunctions.f_1001ed830(presentation, recording: state.isRecording)
        }
        .buttonStyle(OriginalShortcutPrimaryButtonStyle())
        if case .assigned = state {
            Button(action: clear) { OriginalShortcutControlFunctions.f_1001ee524() }
                .buttonStyle(OriginalShortcutRemoveButtonStyle())
                .help(OriginalShortcutRecorder.removeTitle)
        }
    }

    public var body: some View { ZStack(alignment: .topTrailing) { f_1001ed1c4() } }
}
