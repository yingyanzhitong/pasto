import Foundation
import PastoObjC

public struct OriginalObjCExceptionError: Error {
    public let name: String
    public let reason: String?
}

/// Swift Result transport around the original synchronous Objective-C exception boundary.
public enum OriginalObjCExceptionBridge {
    public static func withResult<T>(_ operation: () throws -> T) throws -> T {
        var result: Result<T, Error>?
        let exception = PRObjCExceptionCatcher.catchException(in: {
            do { result = .success(try operation()) }
            catch { result = .failure(error) }
        })
        if let exception {
            throw OriginalObjCExceptionError(name: exception.name.rawValue, reason: exception.reason)
        }
        guard let result else {
            preconditionFailure("Objective-C exception boundary returned without a result")
        }
        return try result.get()
    }

    public static func f_1002ff9c8(_ operation: () throws -> Void) throws {
        try withResult(operation)
    }

    public static func f_1002ffc68(_ operation: () throws -> Data) throws -> Data {
        try withResult(operation)
    }
}
