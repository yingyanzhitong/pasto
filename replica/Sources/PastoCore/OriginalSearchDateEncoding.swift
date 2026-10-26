import Foundation

public enum OriginalSearchDateEncoding {
    public static func f_1002d9d2c(_ range: Range<Date>) -> OriginalSearchQueryNode {
        let start = Int(range.lowerBound.timeIntervalSince1970.rounded(.down))
        let end = Int(range.upperBound.timeIntervalSince1970.rounded(.up))
        return .filter(3, "\(start) \(end)")
    }

    private static let dateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .none
        return formatter
    }()

    public static func f_1002d8e9c(_ value: String) -> String? {
        for preset in OriginalSearchDateRanges.f_1002d8ce0() {
            if f_1002d9d2c(preset.range) == .filter(3, value) { return preset.title }
        }
        let parts = value.split(separator: " ")
        guard parts.count == 2, let start = Int(parts[0]), let end = Int(parts[1]) else { return nil }
        return dateFormatter.string(from: Date(timeIntervalSince1970: Double(start)))
            + " to " + dateFormatter.string(from: Date(timeIntervalSince1970: Double(end)))
    }

    public static func title(for range: Range<Date>) -> String {
        guard case let .filter(_, value) = f_1002d9d2c(range) else { preconditionFailure() }
        return f_1002d8e9c(value) ?? value
    }
}
