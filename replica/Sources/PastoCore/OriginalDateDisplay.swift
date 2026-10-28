import Foundation

@MainActor
public enum OriginalDateDisplay {
    public enum Format {
        case named(relativeTo: Date)
        case abbreviated(relativeTo: Date)
        case absolute
    }

    private static var relativeFormatterSlot: RelativeDateTimeFormatter?
    private static var componentsFormatterSlot: DateComponentsFormatter?
    private static var absoluteFormatterSlot: DateFormatter?
    private static let relativeFormatterInitialized: Void = f_100309c40()
    private static let componentsFormatterInitialized: Void = f_100309c7c()
    private static let absoluteFormatterInitialized: Void = f_100309cd0()

    private static var relativeFormatter: RelativeDateTimeFormatter {
        _ = relativeFormatterInitialized
        return relativeFormatterSlot!
    }

    private static var componentsFormatter: DateComponentsFormatter {
        _ = componentsFormatterInitialized
        return componentsFormatterSlot!
    }

    private static var absoluteFormatter: DateFormatter {
        _ = absoluteFormatterInitialized
        return absoluteFormatterSlot!
    }

    public static func f_100309c40() {
        let formatter = RelativeDateTimeFormatter()
        formatter.dateTimeStyle = .named
        relativeFormatterSlot = formatter
    }

    public static func f_100309c7c() {
        let formatter = DateComponentsFormatter()
        formatter.includesApproximationPhrase = false
        formatter.maximumUnitCount = 1
        formatter.unitsStyle = .abbreviated
        componentsFormatterSlot = formatter
    }

    public static func f_100309cd0() {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        absoluteFormatterSlot = formatter
    }

    public static func f_100309d18(_ components: DateComponents) -> NSCalendar.Unit? {
        if let value = components.year, value > 0 { return .year }
        if let value = components.month, value > 0 { return .month }
        if let value = components.day, value > 0 { return .day }
        if let value = components.hour, value > 0 { return .hour }
        if let value = components.minute, value > 0 { return .minute }
        if let value = components.second, value > 0 { return .second }
        return nil
    }

    public static func f_100309e0c(_ date: Date, format: Format) -> String {
        switch format {
        case .named(let reference):
            return relativeFormatter.localizedString(for: date, relativeTo: reference)
        case .abbreviated(let reference):
            let components = Calendar.current.dateComponents(
                [.year, .month, .day, .hour, .minute, .second], from: date, to: reference)
            if let unit = f_100309d18(components) {
                componentsFormatter.allowedUnits = unit
                if let text = componentsFormatter.string(from: components) { return text }
            }
            return relativeFormatter.localizedString(for: date, relativeTo: reference)
        case .absolute:
            return absoluteFormatter.string(from: date)
        }
    }
}
