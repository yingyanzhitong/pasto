import ApplicationServices
import Combine
import Foundation

/// Permission observation is separate from the original explicit modal request actions.
public final class OriginalAccessibilityService {
    public init() {}

    public func f_100ae5e74() -> Bool {
        AXIsProcessTrusted()
    }

    public func f_100ae5e90() -> AnyPublisher<Bool, Never> {
        let initial = Just(f_100ae5e74())
        let changes = Timer.publish(every: 1, on: .main, in: .common)
            .autoconnect()
            .map { [weak self] _ in
                guard self != nil else { return false }
                return AXIsProcessTrusted()
            }
        return initial.merge(with: changes)
            .removeDuplicates()
            .eraseToAnyPublisher()
    }
}
