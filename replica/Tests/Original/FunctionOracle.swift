import AppKit
import CryptoKit
import Darwin
import ImageIO
import MachO
import ObjectiveC
import UniformTypeIdentifiers
import Vision
import PastoCore

// Recovered from arm64 stores/strides; do not substitute the Codable replica type.
private struct OracleWord {
    var text: String
    var confidence: Float
    var boundingBox: CGRect?
}

private final class Sentinel: NSObject {
    let value: Int
    init(_ value: Int) { self.value = value }
}

private func digest(_ data: Data) -> String { SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined() }
private func dataResult(_ data: Data?) -> [String: Any] {
    guard let data else { return ["nil": true] }
    return ["nil": false, "bytes": data.count, "sha256": digest(data)]
}
private func wordResult(_ text: String, _ confidence: Float, _ box: CGRect?) -> [String: Any] {
    ["text": text, "confidence": confidence,
     "box": box.map { [$0.origin.x, $0.origin.y, $0.size.width, $0.size.height] } as Any? ?? NSNull()]
}
private func equalWords(_ a: [OracleWord], _ b: [RecognizedWord]) -> Bool {
    a.count == b.count && zip(a, b).allSatisfy {
        $0.text == $1.text && $0.confidence == $1.confidence && $0.boundingBox == $1.boundingBox
    }
}
private func errorResult(_ error: Error) -> [String: Any] {
    let error = error as NSError
    return ["domain": error.domain, "code": error.code, "user_info_empty": error.userInfo.isEmpty]
}

@main struct FunctionOracle {
    @MainActor static func main() throws {
        precondition(MemoryLayout<OracleWord>.size == 57 && MemoryLayout<OracleWord>.stride == 64)
        precondition(MemoryLayout<Data>.size == 16 && MemoryLayout<Error?>.size == 8)
        let path = CommandLine.arguments[1]
        guard dlopen(path, RTLD_NOW | RTLD_LOCAL) != nil else { fatalError(String(cString: dlerror())) }
        var imageSlide: Int?
        for index in 0..<_dyld_image_count() where String(cString: _dyld_get_image_name(index)) == path {
            imageSlide = _dyld_get_image_vmaddr_slide(index)
        }
        guard let slide = imageSlide else { fatalError("Original image was not loaded") }
        func address(_ virtual: UInt64) -> UnsafeRawPointer { UnsafeRawPointer(bitPattern: Int(virtual) + slide)! }
        let boolean = unsafeBitCast(address(0x1000114fc), to: (@convention(c)(UInt64, UInt64, UInt64) -> UInt64).self)
        let prepare = unsafeBitCast(address(0x1002d4ba0), to: (@convention(thin)(Int, Data) -> Data?).self)
        let mapper = unsafeBitCast(address(0x1002d576c), to: (@convention(thin)([VNRecognizedTextObservation]) -> [OracleWord]).self)
        let wrapper = unsafeBitCast(address(0x1002d4738), to: (@convention(thin)(Data, Int) throws -> [OracleWord]).self)
        var results: [String: [[String: Any]]] = [:]
        func record(_ id: String, _ input: [String: Any], _ original: Any, _ replica: Any, _ equal: Bool) {
            results[id, default: []].append(["input": input, "original": original, "replica": replica, "equal": equal])
            precondition(equal, "Original/replica mismatch: \(id), input \(input)")
        }
        for hasWindow in [false, true] {
            func window() -> NSWindow? {
                guard hasWindow else { return nil }
                return NSWindow(contentRect: .init(x: 0, y: 0, width: 264, height: 76),
                                styleMask: .borderless, backing: .buffered, defer: false)
            }
            let originalWindow = window(), replicaWindow = window()
            let pointer = oracle_create_window_controller(originalWindow.map { Unmanaged.passUnretained($0).toOpaque() })!
            let controller = Unmanaged<NSWindowController>.fromOpaque(pointer).takeRetainedValue()
            _ = oracle_call_context(address(0x100011138), Unmanaged.passUnretained(controller).toOpaque(), 0)
            let replica = OriginalStackWindowController(window: replicaWindow)
            replica.f_100011138()
            func properties(_ window: NSWindow?) -> [String: Any] {
                guard let window else { return ["window": false] }
                return ["level": window.level.rawValue, "collection_behavior": window.collectionBehavior.rawValue,
                        "movable_by_background": window.isMovableByWindowBackground,
                        "autosave_name": window.frameAutosaveName, "visible": window.isVisible]
            }
            let expected = properties(originalWindow), actual = properties(replicaWindow)
            record("Paste:0x100011138", ["has_window": hasWindow], expected, actual, NSDictionary(dictionary: expected).isEqual(to: actual))
        }
        for selector: UInt64 in [19, 23] {
            let expected = boolean(0, 0, selector) != 0
            let actual = OriginalStackFunctions.f_1000114fc()
            record("Paste:0x1000114fc", ["selector": selector, "executor": "MainActor"], expected, actual, expected == actual)
        }
        for (virtual, function, actual) in [
            (UInt64(0x1000114ec), "Paste:0x1000114ec", OriginalStackFunctions.f_1000114ec()),
            (UInt64(0x1000114f4), "Paste:0x1000114f4", OriginalStackFunctions.f_1000114f4())
        ] {
            let method = unsafeBitCast(address(virtual), to: (@convention(c)(UInt64, UInt64) -> UInt64).self)
            let expected = method(0, 0) != 0
            record(function, ["executor": "MainActor", "selector_thunk": true], expected, actual, expected == actual)
        }
        for count in [0, 1, 2, 3, 4, 17, 257] {
            for shared in [false, true] {
                // Duplicate identities cover equality-independent swapping. Each input remains
                // separate from the optional retained alias so both uniqueness branches run.
                let sentinels = (0..<max(count, 1)).map { Sentinel($0 % 3) }
                func fresh() -> [Sentinel] { (0..<count).map { sentinels[$0 % sentinels.count] } }
                var original = fresh()
                let alias: [Sentinel]? = shared ? original : nil
                var replica = fresh()
                withUnsafeMutablePointer(to: &original) { pointer in
                    _ = oracle_call_context(address(0x10008468c), UnsafeMutableRawPointer(pointer), 0)
                }
                OriginalStackFunctions.f_10008468c(&replica)
                let equal = original.count == replica.count && zip(original, replica).allSatisfy { $0 === $1 }
                    && (alias == nil || alias!.map(\.value) == fresh().map(\.value))
                record("Paste:0x10008468c", ["count": count, "shared_storage": shared, "duplicate_values": true],
                       original.map(\.value), replica.map(\.value), equal)
            }
        }
        let numberOfRows = unsafeBitCast(address(0x100085230), to: (@convention(c)(UnsafeRawPointer, UInt64, UnsafeRawPointer) -> Int).self)
        let shouldSelect = unsafeBitCast(address(0x100085670), to: (@convention(c)(UnsafeRawPointer, UInt64, UnsafeRawPointer, Int) -> UInt64).self)
        for count in [0, 1, 2, 9, 10, 11, 257] {
            for rowHeight: CGFloat in [1, 12.5, 44] {
                let table = NSTableView(frame: .init(x: 0, y: 0, width: 264, height: 100))
                table.rowHeight = rowHeight
                let scroll = NSScrollView(frame: table.frame)
                scroll.documentView = table
                let tablePointer = Unmanaged.passUnretained(table).toOpaque()
                let pointer = oracle_create_table_controller(tablePointer)!
                let original = Unmanaged<NSViewController>.fromOpaque(pointer).takeRetainedValue()
                let cls: AnyClass = type(of: original)
                let snippets = class_getInstanceVariable(cls, "snippets")!
                // This fixture is restricted to functions that read the Array's count.
                // No original function dereferences these stand-in snippet elements.
                pointer.advanced(by: ivar_getOffset(snippets)).assumingMemoryBound(to: [Sentinel].self).pointee = (0..<count).map { Sentinel($0) }
                let replica = OriginalStackTableController()
                replica.tableView.rowHeight = rowHeight
                replica.snippets = (0..<count).map { ClipboardItem(plainText: "row \($0)") }
                let input: [String: Any] = ["count": count, "row_height": rowHeight]
                let first = oracle_call_context(address(0x100082b90), pointer, 0)
                let second = oracle_call_context(address(0x100082b90), pointer, 0)
                let constraint = Unmanaged<NSLayoutConstraint>.fromOpaque(UnsafeRawPointer(bitPattern: UInt(first))!).takeUnretainedValue()
                let actualConstraint = replica.f_100082b90()
                let expectedLazy: [String: Any] = ["constant": constraint.constant, "active": constraint.isActive,
                    "reused": first == second, "scroll_anchor": constraint.firstItem === scroll]
                let actualLazy: [String: Any] = ["constant": actualConstraint.constant, "active": actualConstraint.isActive,
                    "reused": actualConstraint === replica.f_100082b90(), "scroll_anchor": actualConstraint.firstItem === replica.scrollView]
                record("Paste:0x100082b90", input, expectedLazy, actualLazy, NSDictionary(dictionary: expectedLazy).isEqual(to: actualLazy))
                let expectedCount = numberOfRows(UnsafeRawPointer(pointer), 0, UnsafeRawPointer(tablePointer))
                record("Paste:0x100085230", input, expectedCount, replica.f_100085230(), expectedCount == replica.f_100085230())
                for row in [Int.min, -1, 0, count, Int.max] {
                    let expected = shouldSelect(UnsafeRawPointer(pointer), 0, UnsafeRawPointer(tablePointer), row) != 0
                    let actual = replica.f_100085670(row: row)
                    record("Paste:0x100085670", input.merging(["row": row]) { a, _ in a }, expected, actual, expected == actual)
                }
                NSAnimationContext.runAnimationGroup { context in
                    context.duration = 0
                    _ = oracle_call_context(address(0x100083a20), pointer, 0)
                    replica.f_100083a20()
                }
                let beforeOriginal = constraint.constant, beforeReplica = actualConstraint.constant
                RunLoop.current.run(until: Date().addingTimeInterval(0.03))
                let expectedHeight: [String: Any] = ["immediate": beforeOriginal, "settled": constraint.constant, "active": constraint.isActive]
                let actualHeight: [String: Any] = ["immediate": beforeReplica, "settled": actualConstraint.constant, "active": actualConstraint.isActive]
                record("Paste:0x100083a20", input, expectedHeight, actualHeight, NSDictionary(dictionary: expectedHeight).isEqual(to: actualHeight))
                withExtendedLifetime(scroll) {}
            }
        }
        func image(width: Int, height: Int, text: String = "", type: String = UTType.png.identifier,
                   orientation: Int = 1) -> Data {
            let bitmap = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: width, pixelsHigh: height,
                bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
                colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
            NSGraphicsContext.saveGraphicsState()
            NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: bitmap)
            NSColor.white.setFill()
            NSRect(x: 0, y: 0, width: width, height: height).fill()
            (text as NSString).draw(with: NSRect(x: 40, y: 90, width: width - 80, height: 110),
                attributes: [.font: NSFont.boldSystemFont(ofSize: 70), .foregroundColor: NSColor.black])
            NSGraphicsContext.restoreGraphicsState()
            let data = NSMutableData()
            let destination = CGImageDestinationCreateWithData(data, type as CFString, 1, nil)!
            CGImageDestinationAddImage(destination, bitmap.cgImage!, [kCGImagePropertyOrientation: orientation] as CFDictionary)
            precondition(CGImageDestinationFinalize(destination))
            return data as Data
        }
        let phrases = ["PASTE REPLICA 8426", "PASTE, PASTE! 8426", "Hello...hello 中文 测试"]
        var fixtures: [(String, Data)] = [("empty", Data()), ("corrupt", Data([0, 1, 2, 3]))]
        for (width, height) in [(10, 11), (11, 10), (11, 11), (12, 48), (256, 1400)] {
            fixtures.append(("\(width)x\(height)", image(width: width, height: height)))
        }
        for (index, text) in phrases.enumerated() {
            fixtures.append(("text-\(index)", image(width: 1400, height: 260, text: text)))
        }
        for orientation in [3, 6, 8] {
            fixtures.append(("jpeg-orientation-\(orientation)", image(width: 1400, height: 260,
                text: phrases[0], type: UTType.jpeg.identifier, orientation: orientation)))
        }
        for (name, data) in fixtures {
            for maximum in [Int.min, -1, 0, 1, 10, 11, 128, 1400, Int.max] {
                let expected = prepare(maximum, data)
                let actual = ImageTextRecognizer.f_1002d4ba0(imageData: data, maximumDimension: maximum)
                record("Paste:0x1002d4ba0", ["fixture": name, "sha256": digest(data), "maximum": maximum],
                       dataResult(expected), dataResult(actual), expected == actual)
            }
            for function in ["Paste:0x1002d4738", "Paste:0x1002d4830"] {
                let input: [String: Any] = ["fixture": name, "sha256": digest(data), "maximum": Int.max]
                let expected: Result<[OracleWord], Error> = Result {
                    if function.hasSuffix("4738") { return try wrapper(data, Int.max) }
                    var data = data
                    var words: [OracleWord] = []
                    var error: Error?
                    let flag = withUnsafePointer(to: &data) { dataPointer in
                        withUnsafeMutablePointer(to: &words) { resultPointer in
                            withUnsafeMutablePointer(to: &error) { errorPointer in
                                oracle_call_request(address(0x1002d4830), dataPointer, Int64.max, resultPointer, errorPointer)
                            }
                        }
                    }
                    if flag != 0 { throw error! }
                    return words
                }
                let actual: Result<RecognizedTextDocument, Error> = Result {
                    if function.hasSuffix("4738") { return try ImageTextRecognizer.f_1002d4738(imageData: data, maximumDimension: Int.max) }
                    return try ImageTextRecognizer.f_1002d4830(imageData: data, maximumDimension: Int.max)
                }
                switch (expected, actual) {
                case (.success(let a), .success(let b)):
                    record(function, input, a.map { wordResult($0.text, $0.confidence, $0.boundingBox) },
                           b.words.map { wordResult($0.text, $0.confidence, $0.boundingBox) }, equalWords(a, b.words))
                case (.failure(let a), .failure(let b)):
                    let a = errorResult(a), b = errorResult(b)
                    record(function, input, a, b, NSDictionary(dictionary: a).isEqual(to: b))
                default: record(function, input, "different result branches", "different result branches", false)
                }
            }
        }
        var observationFixtures: [(String, [VNRecognizedTextObservation])] = [("empty", []), ("no-candidate", [VNRecognizedTextObservation()])]
        for (name, data) in fixtures where name.hasPrefix("text-") {
            let request = VNRecognizeTextRequest()
            request.automaticallyDetectsLanguage = true
            request.usesLanguageCorrection = true
            request.preferBackgroundProcessing = true
            try VNImageRequestHandler(data: data, options: [:]).perform([request])
            observationFixtures.append((name, request.results ?? []))
        }
        for (name, observations) in observationFixtures {
            let expected = mapper(observations)
            let actual = ImageTextRecognizer.f_1002d576c(observations: observations)
            record("Paste:0x1002d576c", ["fixture": name, "candidates": observations.map { $0.topCandidates(1).first?.string ?? "" }],
                   expected.map { wordResult($0.text, $0.confidence, $0.boundingBox) },
                   actual.map { wordResult($0.text, $0.confidence, $0.boundingBox) }, equalWords(expected, actual))
        }
        let report: [String: Any] = ["passed": true, "functions": results,
            "word_layout": ["size": MemoryLayout<OracleWord>.size, "stride": MemoryLayout<OracleWord>.stride],
            "macos": ProcessInfo.processInfo.operatingSystemVersionString]
        let output = try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
        try output.write(to: URL(fileURLWithPath: CommandLine.arguments[2]))
    }
}
