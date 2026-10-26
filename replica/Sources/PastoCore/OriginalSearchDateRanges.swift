import Foundation

public struct OriginalSearchDateFilter: Hashable, Sendable {
    public let title: String
    public let range: Range<Date>

    public init(title: String, range: Range<Date>) {
        self.title = title
        self.range = range
    }
}

public enum OriginalSearchDateRanges {
    private static func range(_ start: Date, _ end: Date) -> Range<Date> {
        precondition(start < end)
        return start..<end
    }

    public static func f_1002d7694() -> Range<Date> {
        let start = Calendar.current.startOfDay(for: Date())
        return range(start, Calendar.current.date(byAdding: .day, value: 1, to: start)!)
    }

    public static func f_1002d7a14() -> Range<Date> {
        let end = Calendar.current.startOfDay(for: Date())
        return range(Calendar.current.date(byAdding: .day, value: -1, to: end)!, end)
    }

    public static func f_1002d7db8() -> Range<Date> {
        let now = Date()
        let components = Calendar.current.dateComponents([.calendar, .yearForWeekOfYear, .weekOfYear], from: now)
        let start = components.date!
        return range(start, Calendar.current.date(byAdding: .day, value: 7, to: start)!)
    }

    public static func f_1002d8300() -> Range<Date> {
        let now = Date()
        let components = Calendar.current.dateComponents([.calendar, .yearForWeekOfYear, .weekOfYear], from: now)
        let end = components.date!
        return range(Calendar.current.date(byAdding: .weekOfYear, value: -1, to: end)!, end)
    }

    public static func f_1002d8860() -> Range<Date> {
        let today = Calendar.current.startOfDay(for: Date())
        let start = Calendar.current.date(byAdding: .day, value: -30, to: today)!
        let end = Calendar.current.date(byAdding: .day, value: 1, to: today)!
        return range(start, end)
    }

    public static func f_1002d8ce0() -> [OriginalSearchDateFilter] {
        [
            .init(title: "Today", range: f_1002d7694()),
            .init(title: "Yesterday", range: f_1002d7a14()),
            .init(title: "This week", range: f_1002d7db8()),
            .init(title: "Last week", range: f_1002d8300()),
            .init(title: "Last 30 days", range: f_1002d8860())
        ]
    }
}
