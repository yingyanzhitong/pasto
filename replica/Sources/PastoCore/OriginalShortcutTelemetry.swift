import Foundation

public typealias OriginalShortcutTelemetryConfiguration = (
    isEnabled: Bool, distributionType: String, tracesSampleRate: CGFloat
)

/// Configuration and construction recovered independently of the Sentry sinks.
/// Error capture and breadcrumb delivery remain separate migration work.
public final class OriginalShortcutTelemetry {
    public static let configuration = OriginalInitializedValue<OriginalShortcutTelemetryConfiguration>()

    public let isEnabled: Bool
    public let distributionType: String
    public let tracesSampleRate: CGFloat

    private init(isEnabled: Bool, distributionType: String, tracesSampleRate: CGFloat) {
        self.isEnabled = isEnabled
        self.distributionType = distributionType
        self.tracesSampleRate = tracesSampleRate
    }

    public static func f_10019b694() -> OriginalShortcutTelemetry {
        OriginalDependencies.f_1000d80e0(file: "PasteTelemetry/DI+PasteTelemetry.swift", line: 13, column: 19) {
            f_10019b6f0()
        }
    }

    public static func f_10019b6f0() -> OriginalShortcutTelemetry {
        let configuration = Self.configuration
        if configuration.f_1000dafe8() == nil {
            configuration.f_1000db054((isEnabled: false, distributionType: "unknown", tracesSampleRate: 0))
        }
        return OriginalShortcutTelemetry(
            isEnabled: configuration.f_1000db2dc(\OriginalShortcutTelemetryConfiguration.isEnabled),
            distributionType: configuration.f_1000db2dc(\OriginalShortcutTelemetryConfiguration.distributionType),
            tracesSampleRate: configuration.f_1000db2dc(\OriginalShortcutTelemetryConfiguration.tracesSampleRate)
        )
    }

    /// Keep the existing local diagnostic adapter while the original Sentry
    /// error/breadcrumb methods are unresolved. This is not their replacement.
    func localDiagnostic(_ diagnostic: OriginalShortcutDiagnostic) {
        OriginalGlobalShortcutMonitor.writeDiagnostic(diagnostic)
    }
}
