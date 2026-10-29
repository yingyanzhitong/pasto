import Foundation

/// History capacity's piecewise slider mapping, recovered from 0x10035bb8c/0x10035ba90.
public enum OriginalHistoryCapacity {
    public static func days(for position: Double) -> Int? {
        guard position.isFinite, position >= 1, position < 6 else { return nil }
        let value = position > 4 ? position.rounded(.towardZero) : position
        if value < 2 { return Int((value - 1) * 6 + 1) }
        if value < 3 {
            let days = Int((value - 2) * 3 + 1) * 7
            return days < 28 ? days : 30
        }
        if value < 4 {
            let days = Int((value - 3) * 11 + 1) * 30
            return days < 346 ? days : 365
        }
        if value == 4 { return 365 }
        return value == 5 ? 0 : nil
    }

    public static func position(for days: Int) -> Double {
        switch days {
        case 1..<7: return 1 + Double(days - 1) / 6
        case 7..<30: return 2 + (Double(days) / 7 - 1) / 3
        case 30..<365: return 3 + (Double(days) / 30 - 1) / 11
        case 365: return 4
        case 0: return 5
        default: return 0
        }
    }
}
