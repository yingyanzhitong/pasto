import Darwin
import Foundation

final class ValidationRecorder {
    static let shared = ValidationRecorder()
    private let lock = NSLock()
    private var entries: [String] = []
    var failures: [String] { lock.lock(); defer { lock.unlock() }; return entries }
    func fail(_ message: String, file: StaticString, line: UInt) {
        lock.lock(); defer { lock.unlock() }
        entries.append("\(file):\(line): \(message)")
    }
}

private func report(_ message: String, file: StaticString, line: UInt) {
    ValidationRecorder.shared.fail(message, file: file, line: line)
}

func expectEqual<T: Equatable>(_ actual: @autoclosure () throws -> T, _ expected: @autoclosure () throws -> T,
                               _ message: @autoclosure () -> String = "", file: StaticString = #fileID, line: UInt = #line) {
    do {
        let a = try actual(), b = try expected()
        if a != b { report("Expected \(String(describing: b).prefix(300)), received \(String(describing: a).prefix(300)). \(message())", file: file, line: line) }
    } catch { report("Unexpected error: \(error). \(message())", file: file, line: line) }
}

func expectTrue(_ value: @autoclosure () throws -> Bool, _ message: @autoclosure () -> String = "", file: StaticString = #fileID, line: UInt = #line) {
    do { if try !value() { report("Expected true. \(message())", file: file, line: line) } }
    catch { report("Unexpected error: \(error)", file: file, line: line) }
}

func expectFalse(_ value: @autoclosure () throws -> Bool, _ message: @autoclosure () -> String = "", file: StaticString = #fileID, line: UInt = #line) {
    do { if try value() { report("Expected false. \(message())", file: file, line: line) } }
    catch { report("Unexpected error: \(error)", file: file, line: line) }
}

func expectNil<T>(_ value: @autoclosure () throws -> T?, _ message: @autoclosure () -> String = "", file: StaticString = #fileID, line: UInt = #line) {
    do { if try value() != nil { report("Expected nil. \(message())", file: file, line: line) } }
    catch { report("Unexpected error: \(error)", file: file, line: line) }
}

func expectNotNil<T>(_ value: @autoclosure () throws -> T?, _ message: @autoclosure () -> String = "", file: StaticString = #fileID, line: UInt = #line) {
    do { if try value() == nil { report("Expected a value. \(message())", file: file, line: line) } }
    catch { report("Unexpected error: \(error)", file: file, line: line) }
}

func expectGreaterThan<T: Comparable>(_ actual: @autoclosure () throws -> T, _ expected: @autoclosure () throws -> T,
                                     file: StaticString = #fileID, line: UInt = #line) {
    do { if try actual() <= expected() { report("Expected a greater value", file: file, line: line) } }
    catch { report("Unexpected error: \(error)", file: file, line: line) }
}

func expectThrows<T>(_ expression: @autoclosure () throws -> T, file: StaticString = #fileID, line: UInt = #line) {
    do { _ = try expression(); report("Expected an error", file: file, line: line) } catch { }
}

struct ValidationFailure: Error { var message: String }

func requireValue<T>(_ value: @autoclosure () throws -> T?, file: StaticString = #fileID, line: UInt = #line) throws -> T {
    guard let value = try value() else { throw ValidationFailure(message: "\(file):\(line): Required a non-nil value") }
    return value
}

@main
struct ValidationMain {
    static func main() async {
        let suite = ClipboardStoreTests()
        if CommandLine.arguments.count == 4, CommandLine.arguments[1] == "--worker" {
            do {
                try await suite.runWorker(directory: URL(fileURLWithPath: CommandLine.arguments[2]), prefix: CommandLine.arguments[3])
                print("worker completed 30 durable writes")
            } catch { fputs("worker failed: \(error)\n", stderr); exit(1) }
            return
        }
        let tests: [(String, () async throws -> Void)] = [
            ("unicode-search-deduplication", suite.testUnicodeSearchDeduplicationAndIndependentRepresentations),
            ("pinboards-edit-trash-restore", suite.testPinboardsEditingTrashRestoreAndPermanentDeletion),
            ("history-limit-preserves-pins", suite.testHistoryLimitPreservesPinnedContentOutsideHistory),
            ("stale-store-three-way-merge", suite.testStaleStoresMergeItemsPreferencesAndDisjointFields),
            ("archive-corruption-safety", suite.testArchiveRoundTripMergeAndCorruptionDoesNotDestroyData),
            ("rtf-html-plain-text-write-loop", suite.testRichTextRoundTripPlainTextModeAndWriteLoopPrevention),
            ("rich-text-edit-format-reopen", suite.testRichTextEditingPreservesFormattingAfterReopen),
            ("rtf-only-text-extraction", suite.testRTFOnlyCaptureExtractsTextAndRetainsOriginalBytes),
            ("multiple-file-urls", suite.testMultiFileURLPasteboardPreservesSeparateItemsAndUnicodePaths),
            ("real-large-png-binary-roundtrip", suite.testActualLargePNGAndUnknownBinaryPayloadSurvivePersistence),
            ("privacy-pause-exclusion", suite.testCapturePrivacyPauseAndExcludedSourcePolicies),
            ("history-retention-age-boundaries", suite.testHistoryRetentionPermanentExpiredPinnedAndFreshBoundaries),
            ("refresh-pending-edits-no-op-io", suite.testRefreshPreservesPendingEditsWithoutNoOpWrites),
            ("two-independent-process-writers", suite.testTwoRealProcessesDoNotLoseConcurrentWrites)
            ,("multiple-selection-raw-and-text-order", suite.testMultiSelectionOrderRawRepresentationsAndAtomicFailure)
            ,("pinboard-reorder-duplicate-removal", suite.testPinboardReorderingDuplicationAndDeletingPinOnlyContent)
            ,("local-vision-ocr-real-pixels", suite.testLocalVisionOCRSearchPersistenceAndOriginalPayloadIsolation)
            ,("transient-opt-out-loop-guard", suite.testTransientOptOutStillRejectsReplicaWriteBack)
            ,("history-erasure-queue-persistence-merge", suite.testHistoryErasureAndQueuePreferencesSurviveReopenAndMerge)
            ,("address-stack-array-window-contracts", suite.testAddressStackArrayAndWindowContracts)
            ,("address-stack-table-contracts", suite.testAddressStackTableContracts)
            ,("address-ocr-preparation-word-geometry", suite.testAddressOCRPreparationAndWordGeometry)
        ]
        var results: [[String: Any]] = []
        for (name, run) in tests {
            let start = Date()
            let previous = ValidationRecorder.shared.failures.count
            do { try await run() }
            catch { ValidationRecorder.shared.fail(error.localizedDescription, file: #fileID, line: #line) }
            let failures = Array(ValidationRecorder.shared.failures.dropFirst(previous))
            results.append(["name": name, "passed": failures.isEmpty, "duration_seconds": Date().timeIntervalSince(start), "failures": failures])
        }
        let failed = ValidationRecorder.shared.failures.count
        let summary: [String: Any] = ["passed": failed == 0, "test_count": results.count,
                                      "failure_count": failed, "tests": results,
                                      "scope": "Temporary isolated stores and private named pasteboards; two independent worker processes; original app and user clipboard untouched."]
        do {
            let data = try JSONSerialization.data(withJSONObject: summary, options: [.prettyPrinted, .sortedKeys])
            FileHandle.standardOutput.write(data)
            FileHandle.standardOutput.write(Data("\n".utf8))
        } catch { fputs("report failed: \(error)\n", stderr); exit(1) }
        if failed != 0 { exit(1) }
    }
}
