import AppKit
import Foundation
import ImageIO
import UniformTypeIdentifiers
import Vision

public struct RecognizedWord: Codable, Equatable, Sendable {
    public var text: String
    public var confidence: Float
    /// Vision coordinates: normalized to the image, origin at the lower left.
    public var boundingBox: CGRect?
}

public struct RecognizedTextDocument: Codable, Equatable, Sendable {
    public var text: String
    public var words: [RecognizedWord]
}

/// NSError bridging contract recovered by executing the original empty-input path.
public enum OCRError: Error, CustomNSError {
    case invalidImageData

    public static var errorDomain: String { "PasteRecognition.OCRError" }
    public var errorCode: Int { 0 }
    public var errorUserInfo: [String: Any] { [:] }
}

extension ClipboardItem {
    public var recognizedText: String? {
        payloads[ClipboardStore.recognizedTextPayloadKey].flatMap { String(data: $0, encoding: .utf8) }
    }

    public var recognizedTextDocument: RecognizedTextDocument? {
        payloads[ClipboardStore.recognizedDocumentPayloadKey].flatMap {
            try? JSONDecoder().decode(RecognizedTextDocument.self, from: $0)
        }
    }

    var imageData: Data? {
        for representation in ClipboardStore.normalizedPasteboardPayloads(payloads) {
            for key in [NSPasteboard.PasteboardType.png.rawValue, NSPasteboard.PasteboardType.tiff.rawValue,
                        "public.jpeg", "public.heic", "com.compuserve.gif"] {
                if let data = representation[key] { return data }
            }
        }
        return nil
    }
}

public enum ImageTextRecognizer {
    public static func recognize(imageData: Data) async throws -> String {
        try await recognizeDocument(imageData: imageData).text
    }

    public static func recognizeDocument(imageData: Data, maximumDimension: Int = .max) async throws -> RecognizedTextDocument {
        try await Task.detached(priority: .utility) {
            try f_1002d4738(imageData: imageData, maximumDimension: maximumDimension)
        }.value
    }

    /// REA 0x1002d4738: reject empty Data, execute recognition inside an autorelease pool.
    public static func f_1002d4738(imageData: Data, maximumDimension: Int) throws -> RecognizedTextDocument {
        guard !imageData.isEmpty else { throw OCRError.invalidImageData }
        return try autoreleasepool { try f_1002d4830(imageData: imageData, maximumDimension: maximumDimension) }
    }

    /// REA 0x1002d4ba0: reject missing/tiny dimensions; retain bytes below the supplied
    /// threshold, otherwise create an orientation-corrected thumbnail and encode PNG.
    public static func f_1002d4ba0(imageData: Data, maximumDimension: Int) -> Data? {
        guard let source = CGImageSourceCreateWithData(imageData as CFData, nil),
              let properties = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [CFString: Any],
              let width = properties[kCGImagePropertyPixelWidth] as? Int,
              let height = properties[kCGImagePropertyPixelHeight] as? Int,
              width > 10, height > 10 else { return nil }
        if max(width, height) <= maximumDimension { return imageData }
        // The original passes zero/negative values through to ImageIO; zero does
        // not mean failure. Direct original-function comparison covers this edge.
        guard let thumbnail = CGImageSourceCreateThumbnailAtIndex(source, 0, [
                kCGImageSourceCreateThumbnailFromImageAlways: true,
                kCGImageSourceCreateThumbnailWithTransform: true,
                kCGImageSourceThumbnailMaxPixelSize: maximumDimension
              ] as CFDictionary) else { return nil }
        let output = NSMutableData()
        guard let destination = CGImageDestinationCreateWithData(output, UTType.png.identifier as CFString, 1, nil) else { return nil }
        CGImageDestinationAddImage(destination, thumbnail, nil)
        guard CGImageDestinationFinalize(destination) else { return nil }
        return output as Data
    }

    /// REA 0x1002d4830: invalid prepared image returns an empty result; Vision errors throw.
    public static func f_1002d4830(imageData: Data, maximumDimension: Int) throws -> RecognizedTextDocument {
        guard let prepared = f_1002d4ba0(imageData: imageData, maximumDimension: maximumDimension) else {
            return RecognizedTextDocument(text: "", words: [])
        }
        let request = VNRecognizeTextRequest()
        request.automaticallyDetectsLanguage = true
        request.usesLanguageCorrection = true
        request.preferBackgroundProcessing = true
        let handler = VNImageRequestHandler(data: prepared, options: [:])
        try handler.perform([request])
        let observations = request.results ?? []
        return RecognizedTextDocument(text: observations.compactMap { $0.topCandidates(1).first?.string }.joined(separator: "\n"),
                                      words: f_1002d576c(observations: observations))
    }

    /// REA 0x1002d576c: first candidate, split on whitespace/newlines plus punctuation,
    /// omit empty components, retain per-token confidence and optional Vision rectangle.
    /// Forward ranges are also compared with the original machine code on synthetic observations.
    public static func f_1002d576c(observations: [VNRecognizedTextObservation]) -> [RecognizedWord] {
        let separators = CharacterSet.whitespacesAndNewlines.union(.punctuationCharacters)
        var words: [RecognizedWord] = []
        for observation in observations {
            guard let candidate = observation.topCandidates(1).first else { continue }
            let text = candidate.string
            var cursor = text.startIndex
            for word in text.components(separatedBy: separators).filter({ !$0.isEmpty }) {
                guard let range = text.range(of: word, options: [], range: cursor..<text.endIndex, locale: nil) else { break }
                let box = try? candidate.boundingBox(for: range)
                words.append(RecognizedWord(text: word, confidence: candidate.confidence, boundingBox: box?.boundingBox))
                cursor = range.upperBound
            }
        }
        return words
    }
}

extension ClipboardStore {
    nonisolated static let recognizedTextPayloadKey = "com.pastereplica.internal.recognized-text"
    nonisolated static let recognizedDocumentPayloadKey = "com.pastereplica.internal.recognized-document+json"
    nonisolated static let analysisPayloadKeys: Set<String> = [recognizedTextPayloadKey, recognizedDocumentPayloadKey]

    @discardableResult
    public func recognizeImageText(id: UUID) async throws -> String {
        try save()
        guard let item = items.first(where: { $0.id == id && !$0.isDeleted }) else { throw ClipboardStoreError.itemNotFound }
        if let recognized = item.recognizedText { return recognized }
        return try await recognizeImageDocument(id: id).text
    }

    public func recognizeImageDocument(id: UUID) async throws -> RecognizedTextDocument {
        try save()
        guard let item = items.first(where: { $0.id == id && !$0.isDeleted }) else { throw ClipboardStoreError.itemNotFound }
        if let document = item.recognizedTextDocument { return document }
        guard item.kind == .image, let data = item.imageData else { throw CocoaError(.fileReadUnsupportedScheme) }
        let document = try await ImageTextRecognizer.recognizeDocument(imageData: data)
        try saveRecognizedDocument(id: id, document: document, expectedImageData: data)
        return document
    }

    func startBackgroundTextRecognition(id: UUID) {
        guard let item = items.first(where: { $0.id == id }), item.recognizedTextDocument == nil else { return }
        Task { [weak self] in _ = try? await self?.recognizeImageText(id: id) }
    }
}
