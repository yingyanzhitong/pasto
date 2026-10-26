public final class OriginalInitializedValue<Value> {
    private var value: Value?

    public init() { value = nil }

    public func f_1000dae58() -> Value {
        guard case let .some(value) = value else {
            preconditionFailure(String(describing: Value.self) + " must be defined")
        }
        return value
    }

    public func f_1000dafe8() -> Value? { value }

    public func f_1000db054(_ newValue: Value) {
        guard case .none = value else {
            preconditionFailure(String(describing: Value.self) + " has already been set")
        }
        value = .some(newValue)
    }

    public func f_1000db2dc<Member>(_ keyPath: KeyPath<Value, Member>) -> Member {
        f_1000dae58()[keyPath: keyPath]
    }
}
