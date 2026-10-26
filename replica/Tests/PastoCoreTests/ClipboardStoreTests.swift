import AppKit
import Foundation
import Combine
import ImageIO
import PastoCore

final class ClipboardStoreTests {
    private func temporaryDirectory() throws -> URL {
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("PastoTests-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        return url
    }

    @MainActor
    private func privatePasteboard() -> NSPasteboard {
        NSPasteboard(name: .init("PastoTests-\(UUID().uuidString)"))
    }

    @MainActor
    private func textImageFixture(text: String = "PASTE REPLICA 8426") throws -> Data {
        let bitmap = try requireValue(NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: 1400, pixelsHigh: 260,
                                                       bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
                                                       isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0))
        let context = try requireValue(NSGraphicsContext(bitmapImageRep: bitmap))
        NSGraphicsContext.saveGraphicsState()
        NSGraphicsContext.current = context
        NSColor.white.setFill()
        NSRect(x: 0, y: 0, width: 1400, height: 260).fill()
        (text as NSString).draw(with: NSRect(x: 40, y: 90, width: 1320, height: 110), attributes: [
            .font: NSFont.boldSystemFont(ofSize: 86), .foregroundColor: NSColor.black
        ])
        NSGraphicsContext.restoreGraphicsState()
        return try requireValue(bitmap.representation(using: .png, properties: [:]))
    }

    func testUnicodeSearchDeduplicationAndIndependentRepresentations() async throws {
        let directory = try temporaryDirectory()
        defer { try? FileManager.default.removeItem(at: directory) }
        try await MainActor.run {
            let store = try ClipboardStore(directoryURL: directory)
            let text = "CAFÉ 👨‍👩‍👧‍👦 简体中文 e\u{301}"
            let original = ClipboardItem(title: "标题", plainText: text, sourceName: "测试来源", payloads: ["public.utf8-plain-text": Data(text.utf8)])
            let id = try store.add(original)
            var copy = original
            copy.id = UUID()
            copy.sourceName = "另一个来源"
            expectEqual(try store.add(copy), id)
            expectEqual(store.items.count, 1)
            expectEqual(store.items[0].sourceName, "另一个来源")
            expectEqual(store.search(query: "cafe 中文").map(\.id), [id])
            expectEqual(store.search(query: "é").count, 1)
            expectTrue(store.search(query: "不存在").isEmpty)
            copy.payloads["text/html"] = Data("<b>different formatting</b>".utf8)
            expectFalse(try store.add(copy) == id)
            expectEqual(store.items.count, 2, "Different raw representations must not disappear through text-only deduplication")
            let reopened = try ClipboardStore(directoryURL: directory)
            expectEqual(Set(reopened.items.map(\.id)), Set(store.items.map(\.id)))
            expectEqual(reopened.items.first { $0.id == id }?.plainText, text)
            let attributes = try FileManager.default.attributesOfItem(atPath: directory.appendingPathComponent("clipboard.json").path)
            expectEqual((attributes[.posixPermissions] as? NSNumber)?.intValue, 0o600)
        }
    }

    func testPinboardsEditingTrashRestoreAndPermanentDeletion() async throws {
        let directory = try temporaryDirectory()
        defer { try? FileManager.default.removeItem(at: directory) }
        try await MainActor.run {
            let store = try ClipboardStore(directoryURL: directory)
            let id = try store.add(ClipboardItem(title: "old", kind: .richText, plainText: "old", payloads: ["public.rtf": Data("old rich bytes".utf8)]))
            let a = try store.createPinboard(name: "工作", colorHex: "#FF0000")
            let b = try store.createPinboard(name: "私人", colorHex: "#00FF00")
            try store.assign(ids: [id], to: a.id)
            try store.assign(ids: [id], to: b.id)
            try store.unassign(ids: [id], from: a.id)
            expectEqual(store.items[0].pinboardIDs, [b.id])
            try store.renamePinboard(id: b.id, name: "收藏")
            expectEqual(store.search(query: "", pinboardID: b.id).count, 1)
            try store.updateItem(id: id, title: "新标题", text: "https://example.invalid/中文")
            expectEqual(store.items[0].kind, .link)
            expectNil(store.items[0].payloads["public.rtf"], "Editing text cannot leave stale rich-text bytes")
            try store.updateItem(id: id, text: "#FF8800")
            expectEqual(store.items[0].kind, .color)
            try store.delete(ids: [id])
            expectTrue(store.search(query: "").isEmpty)
            expectEqual(store.search(query: "新标题", includeDeleted: true).count, 1)
            try store.restore(ids: [id])
            try store.removePinboard(id: b.id)
            expectEqual(store.items[0].pinboardIDs, [])
            expectEqual(store.items[0].plainText, "#FF8800")
            try store.permanentlyDelete(ids: [id])
            try store.reload()
            expectTrue(store.items.isEmpty)
            expectThrows(try store.renamePinboard(id: a.id, name: " \n"))
            expectThrows(try store.assign(ids: [], to: UUID()))
        }
    }

    func testHistoryLimitPreservesPinnedContentOutsideHistory() async throws {
        let directory = try temporaryDirectory()
        defer { try? FileManager.default.removeItem(at: directory) }
        try await MainActor.run {
            let store = try ClipboardStore(directoryURL: directory)
            store.preferences.historyLimit = 2
            let board = try store.createPinboard(name: "长期保存", colorHex: "#123456")
            let start = Date(timeIntervalSince1970: 100)
            let pinned = try store.add(ClipboardItem(createdAt: start, plainText: "pinned", pinboardIDs: [board.id]))
            _ = try store.add(ClipboardItem(createdAt: start.addingTimeInterval(1), plainText: "evicted"))
            _ = try store.add(ClipboardItem(createdAt: start.addingTimeInterval(2), plainText: "recent"))
            _ = try store.add(ClipboardItem(createdAt: start.addingTimeInterval(3), plainText: "newest"))
            expectEqual(store.search(query: "").count, 2)
            expectEqual(store.search(query: "", pinboardID: board.id).map(\.id), [pinned])
            expectEqual(store.items.first { $0.id == pinned }?.isInHistory, false)
            expectFalse(store.items.contains { $0.plainText == "evicted" })
            expectEqual(store.search(query: "pinned").count, 1)
        }
    }

    func testStaleStoresMergeItemsPreferencesAndDisjointFields() async throws {
        let directory = try temporaryDirectory()
        defer { try? FileManager.default.removeItem(at: directory) }
        try await MainActor.run {
            let a = try ClipboardStore(directoryURL: directory)
            let b = try ClipboardStore(directoryURL: directory)
            let first = try a.add(ClipboardItem(plainText: "first"))
            _ = try b.add(ClipboardItem(plainText: "second"))
            a.preferences.appearance = "dark"
            a.preferences.pasteToActiveApp = false
            b.preferences.historyLimit = 25
            b.preferences.alwaysPastePlainText = true
            b.preferences.historyRetentionDays = 365
            try b.save()
            try a.save()
            expectEqual(a.items.count, 2)
            expectEqual(a.preferences.appearance, "dark")
            expectEqual(a.preferences.historyLimit, 25)
            expectFalse(a.preferences.pasteToActiveApp)
            expectTrue(a.preferences.alwaysPastePlainText)
            expectEqual(a.preferences.historyRetentionDays, 365)
            try b.reload()
            let board = try a.createPinboard(name: "shared", colorHex: "#00AAFF")
            try b.reload()
            if let i = a.items.firstIndex(where: { $0.id == first }) { a.items[i].title = "renamed" }
            try b.assign(ids: [first], to: board.id)
            try a.save()
            let item = try requireValue(a.items.first { $0.id == first })
            expectEqual(item.title, "renamed")
            expectTrue(item.pinboardIDs.contains(board.id))
            let same = try b.add(ClipboardItem(plainText: "first"))
            expectEqual(same, first)
            expectEqual(b.items.count, 2)
            try a.reload()
            if let i = a.items.firstIndex(where: { $0.id == first }) { a.items[i].title = "stale pending rename" }
            try b.permanentlyDelete(ids: [first])
            try a.save()
            expectFalse(a.items.contains { $0.id == first }, "A permanent deletion cannot be resurrected by stale edits")
        }
    }

    func testHistoryErasureAndQueuePreferencesSurviveReopenAndMerge() async throws {
        let directory = try temporaryDirectory()
        defer { try? FileManager.default.removeItem(at: directory) }
        try await MainActor.run {
            let store = try ClipboardStore(directoryURL: directory)
            let pinned = try store.add(ClipboardItem(plainText: "keep pinned"))
            let ordinary = try store.add(ClipboardItem(plainText: "erase ordinary"))
            let board = try store.createPinboard(name: "保留", colorHex: "#00AAFF")
            try store.assign(ids: [pinned], to: board.id)
            let concurrent = try ClipboardStore(directoryURL: directory)
            store.preferences.historyTitle = "本地剪贴板"
            store.preferences.stackItemIDs = [pinned, ordinary]
            store.preferences.stackReversed = true
            concurrent.preferences.ignoreTransientContent = false
            try concurrent.save()
            try store.save()
            let reopened = try ClipboardStore(directoryURL: directory)
            expectEqual(reopened.preferences.historyTitle, "本地剪贴板")
            expectEqual(reopened.preferences.stackItemIDs, [pinned, ordinary])
            expectTrue(reopened.preferences.stackReversed)
            expectFalse(reopened.preferences.ignoreTransientContent)
            try reopened.eraseHistory()
            let erased = try ClipboardStore(directoryURL: directory)
            expectFalse(erased.items.contains { $0.id == ordinary })
            let preserved = try requireValue(erased.items.first { $0.id == pinned })
            expectFalse(preserved.isInHistory)
            expectTrue(preserved.pinboardIDs.contains(board.id))
            concurrent.preferences.historyTitle = "并发改名"
            try concurrent.save()
            try erased.reload()
            expectEqual(erased.preferences.historyTitle, "并发改名")
            expectFalse(erased.items.contains { $0.id == ordinary }, "Stale preferences cannot restore erased history")
            expectFalse(try requireValue(erased.items.first { $0.id == pinned }).isInHistory)
            expectEqual(erased.preferences.stackItemIDs, [pinned, ordinary])
        }
    }

    func testArchiveRoundTripMergeAndCorruptionDoesNotDestroyData() async throws {
        let directory = try temporaryDirectory()
        defer { try? FileManager.default.removeItem(at: directory) }
        try await MainActor.run {
            let source = try ClipboardStore(directoryURL: directory.appendingPathComponent("source"))
            let board = try source.createPinboard(name: "存档", colorHex: "#F0F0F0")
            let id = try source.add(ClipboardItem(title: "二进制", kind: .unknown, payloads: ["application/custom": Data([0, 255, 128, 1])], pinboardIDs: [board.id]))
            try source.delete(ids: [id])
            source.preferences.excludedBundleIDs = ["invalid.synthetic"]
            let archive = directory.appendingPathComponent("archive.json")
            try source.exportArchive(to: archive)
            let destination = try ClipboardStore(directoryURL: directory.appendingPathComponent("destination"))
            let existing = try destination.add(ClipboardItem(plainText: "local data must survive import"))
            try destination.importArchive(from: archive)
            try destination.importArchive(from: archive)
            expectEqual(destination.items.count, 2)
            expectTrue(destination.items.contains { $0.id == existing })
            expectEqual(destination.items.first { $0.id == id }, source.items[0])
            expectEqual(destination.pinboards, source.pinboards)
            expectEqual(destination.preferences, source.preferences)
            let broken = directory.appendingPathComponent("broken.json")
            try Data("{truncated".utf8).write(to: broken)
            expectThrows(try destination.importArchive(from: broken))
            try destination.reload()
            expectEqual(destination.items.count, 2)
            let stateURL = destination.directoryURL.appendingPathComponent("clipboard.json")
            let original = try Data(contentsOf: stateURL)
            try Data("{corrupt disk state".utf8).write(to: stateURL)
            expectThrows(try ClipboardStore(directoryURL: destination.directoryURL))
            expectEqual(try Data(contentsOf: stateURL), Data("{corrupt disk state".utf8))
            try original.write(to: stateURL)
        }
    }

    func testRichTextRoundTripPlainTextModeAndWriteLoopPrevention() async throws {
        let directory = try temporaryDirectory()
        defer { try? FileManager.default.removeItem(at: directory) }
        try await MainActor.run {
            let store = try ClipboardStore(directoryURL: directory)
            let pasteboard = privatePasteboard()
            defer { pasteboard.releaseGlobally() }
            let monitor = ClipboardMonitor(store: store, pasteboard: pasteboard)
            let text = "格式化 👩🏽‍💻 中文\n第二行"
            let attributed = NSAttributedString(string: text, attributes: [.font: NSFont.boldSystemFont(ofSize: 18), .foregroundColor: NSColor.red])
            let rtf = try attributed.data(from: NSRange(location: 0, length: attributed.length), documentAttributes: [.documentType: NSAttributedString.DocumentType.rtf])
            let html = Data("<strong>格式化 👩🏽‍💻 中文</strong>".utf8)
            let object = NSPasteboardItem()
            object.setString(text, forType: .string)
            object.setData(rtf, forType: .rtf)
            object.setData(html, forType: .html)
            pasteboard.clearContents()
            expectTrue(pasteboard.writeObjects([object]))
            monitor.poll()
            expectNil(monitor.lastError)
            let item = try requireValue(store.items.first)
            expectEqual(item.kind, .richText)
            expectEqual(item.payloads[NSPasteboard.PasteboardType.rtf.rawValue], rtf)
            try store.writeToPasteboard(id: item.id, pasteboard: pasteboard, plainTextOnly: false)
            expectEqual(pasteboard.data(forType: .rtf), rtf)
            expectEqual(pasteboard.data(forType: .html), html)
            monitor.poll()
            expectEqual(store.items.count, 1)
            try store.writeToPasteboard(id: item.id, pasteboard: pasteboard, plainTextOnly: true)
            expectEqual(pasteboard.string(forType: .string), text)
            expectNil(pasteboard.data(forType: .rtf))
            expectNil(pasteboard.data(forType: .html))
            monitor.poll()
            expectEqual(store.items.count, 1)
            pasteboard.clearContents()
            pasteboard.setString("new external copy", forType: .string)
            monitor.poll()
            expectEqual(store.items.count, 2)
            monitor.stop()
        }
    }

    func testRichTextEditingPreservesFormattingAfterReopen() async throws {
        let directory = try temporaryDirectory()
        defer { try? FileManager.default.removeItem(at: directory) }
        try await MainActor.run {
            let store = try ClipboardStore(directoryURL: directory)
            let board = try store.createPinboard(name: "编辑收藏", colorHex: "#AABBCC")
            let id = try store.add(ClipboardItem(createdAt: Date(timeIntervalSince1970: 1000), title: "保留标题",
                                                 kind: .text, plainText: "old", sourceName: "原来源",
                                                 sourceBundleID: "invalid.original", payloads: ["public.html": Data("stale".utf8),
                                                 "com.pastereplica.internal.items+json": Data("stale items".utf8)], pinboardIDs: [board.id]))
            let text = "粗体 蓝色 中文 👩🏽‍💻\n第二段"
            let formatted = NSMutableAttributedString(string: text, attributes: [
                .font: NSFont.boldSystemFont(ofSize: 22),
                .foregroundColor: NSColor(calibratedRed: 0.2, green: 0.4, blue: 0.8, alpha: 1)
            ])
            formatted.addAttribute(.underlineStyle, value: NSUnderlineStyle.single.rawValue, range: NSRange(location: 0, length: 2))
            let paragraph = NSMutableParagraphStyle()
            paragraph.alignment = .center
            formatted.addAttribute(.paragraphStyle, value: paragraph, range: NSRange(location: 0, length: formatted.length))
            try store.updateRichTextItem(id: id, attributedString: formatted)
            let reopened = try ClipboardStore(directoryURL: directory)
            let item = try requireValue(reopened.items.first { $0.id == id })
            expectEqual(item.kind, .richText)
            expectEqual(item.title, "保留标题")
            expectEqual(item.plainText, text)
            expectEqual(item.createdAt, Date(timeIntervalSince1970: 1000))
            expectTrue(item.updatedAt > item.createdAt)
            expectEqual(item.pinboardIDs, [board.id])
            expectEqual(item.sourceName, "原来源")
            expectEqual(item.sourceBundleID, "invalid.original")
            expectEqual(Set(item.payloads.keys), [NSPasteboard.PasteboardType.rtf.rawValue, NSPasteboard.PasteboardType.string.rawValue])
            let rtf = try requireValue(item.payloads[NSPasteboard.PasteboardType.rtf.rawValue])
            let decoded = try NSAttributedString(data: rtf, options: [.documentType: NSAttributedString.DocumentType.rtf], documentAttributes: nil)
            expectEqual(decoded.string, text)
            let font = try requireValue(decoded.attribute(.font, at: 0, effectiveRange: nil) as? NSFont)
            expectTrue(NSFontManager.shared.traits(of: font).contains(.boldFontMask))
            expectTrue(abs(font.pointSize - 22) < 0.01)
            expectEqual((decoded.attribute(.underlineStyle, at: 0, effectiveRange: nil) as? NSNumber)?.intValue, NSUnderlineStyle.single.rawValue)
            let color = try requireValue((decoded.attribute(.foregroundColor, at: 0, effectiveRange: nil) as? NSColor)?.usingColorSpace(.sRGB))
            let expectedColor = try requireValue(NSColor(calibratedRed: 0.2, green: 0.4, blue: 0.8, alpha: 1).usingColorSpace(.sRGB))
            expectTrue(abs(color.blueComponent - expectedColor.blueComponent) < 0.02)
            let decodedParagraph = try requireValue(decoded.attribute(.paragraphStyle, at: 0, effectiveRange: nil) as? NSParagraphStyle)
            expectEqual(decodedParagraph.alignment, .center)
            let pasteboard = privatePasteboard()
            defer { pasteboard.releaseGlobally() }
            try reopened.writeToPasteboard(id: id, pasteboard: pasteboard, plainTextOnly: false)
            expectEqual(pasteboard.data(forType: .rtf), rtf)
            expectEqual(pasteboard.string(forType: .string), text)
            expectThrows(try store.updateRichTextItem(id: UUID(), attributedString: formatted))
        }
    }

    func testRTFOnlyCaptureExtractsTextAndRetainsOriginalBytes() async throws {
        let directory = try temporaryDirectory()
        defer { try? FileManager.default.removeItem(at: directory) }
        try await MainActor.run {
            let store = try ClipboardStore(directoryURL: directory)
            let pasteboard = privatePasteboard()
            defer { pasteboard.releaseGlobally() }
            let text = NSAttributedString(string: "Only RTF 中文 👨‍🚀")
            let data = try text.data(from: NSRange(location: 0, length: text.length), documentAttributes: [.documentType: NSAttributedString.DocumentType.rtf])
            pasteboard.clearContents()
            pasteboard.setData(data, forType: .rtf)
            let id = try requireValue(store.capture(pasteboard: pasteboard, sourceName: "Synthetic", sourceBundleID: nil))
            expectEqual(store.items.first { $0.id == id }?.plainText, text.string)
            expectEqual(store.items.first { $0.id == id }?.payloads[NSPasteboard.PasteboardType.rtf.rawValue], data)
        }
    }

    func testMultiFileURLPasteboardPreservesSeparateItemsAndUnicodePaths() async throws {
        let directory = try temporaryDirectory()
        defer { try? FileManager.default.removeItem(at: directory) }
        try await MainActor.run {
            let store = try ClipboardStore(directoryURL: directory.appendingPathComponent("store"))
            let pasteboard = privatePasteboard()
            defer { pasteboard.releaseGlobally() }
            let urls = [directory.appendingPathComponent("文件 👨‍🚀.txt"), directory.appendingPathComponent("second space.txt")]
            var original: [Data] = []
            let objects = urls.map { url -> NSPasteboardItem in
                let item = NSPasteboardItem()
                item.setString(url.absoluteString, forType: .fileURL)
                original.append(item.data(forType: .fileURL)!)
                return item
            }
            pasteboard.clearContents()
            expectTrue(pasteboard.writeObjects(objects))
            let id = try requireValue(store.capture(pasteboard: pasteboard, sourceName: "Synthetic Finder", sourceBundleID: "invalid.finder"))
            expectEqual(store.items[0].kind, .files)
            expectEqual(store.items[0].plainText, urls.map(\.path).joined(separator: "\n"))
            try store.reload()
            try store.writeToPasteboard(id: id, pasteboard: pasteboard, plainTextOnly: false)
            expectEqual(pasteboard.pasteboardItems?.count, 2)
            expectEqual(pasteboard.pasteboardItems?.compactMap { $0.data(forType: .fileURL) }, original)
        }
    }

    func testActualLargePNGAndUnknownBinaryPayloadSurvivePersistence() async throws {
        let directory = try temporaryDirectory()
        defer { try? FileManager.default.removeItem(at: directory) }
        try await MainActor.run {
            let store = try ClipboardStore(directoryURL: directory)
            let pasteboard = privatePasteboard()
            defer { pasteboard.releaseGlobally() }
            let bitmap = try requireValue(NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: 1024, pixelsHigh: 1024,
                                                      bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
                                                      isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0))
            let pixels = try requireValue(bitmap.bitmapData)
            var random: UInt32 = 0x12345678
            for i in 0..<(bitmap.bytesPerRow * bitmap.pixelsHigh) {
                random ^= random << 13; random ^= random >> 17; random ^= random << 5
                pixels[i] = UInt8(truncatingIfNeeded: random)
            }
            let png = try requireValue(bitmap.representation(using: .png, properties: [:]))
            expectGreaterThan(png.count, 3_000_000)
            let unknown = Data((0..<4096).map { UInt8(truncatingIfNeeded: $0) })
            let customType = NSPasteboard.PasteboardType("invalid.synthetic.binary")
            let object = NSPasteboardItem()
            object.setData(png, forType: .png)
            object.setData(unknown, forType: customType)
            pasteboard.clearContents()
            expectTrue(pasteboard.writeObjects([object]))
            let id = try requireValue(store.capture(pasteboard: pasteboard, sourceName: "Synthetic image", sourceBundleID: nil))
            let reopened = try ClipboardStore(directoryURL: directory)
            expectEqual(reopened.items[0].kind, .image)
            expectEqual(reopened.items[0].payloads[NSPasteboard.PasteboardType.png.rawValue], png)
            try reopened.writeToPasteboard(id: id, pasteboard: pasteboard, plainTextOnly: false)
            expectEqual(pasteboard.data(forType: .png), png)
            expectEqual(pasteboard.data(forType: customType), unknown)
            expectNotNil(NSImage(data: try requireValue(pasteboard.data(forType: .png))))
            expectThrows(try reopened.writeToPasteboard(id: id, pasteboard: pasteboard, plainTextOnly: true))
        }
    }

    func testCapturePrivacyPauseAndExcludedSourcePolicies() async throws {
        let directory = try temporaryDirectory()
        defer { try? FileManager.default.removeItem(at: directory) }
        try await MainActor.run {
            let store = try ClipboardStore(directoryURL: directory)
            let pasteboard = privatePasteboard()
            defer { pasteboard.releaseGlobally() }
            func setContent(_ marker: String? = nil) {
                let item = NSPasteboardItem()
                item.setString("synthetic sensitive sample", forType: .string)
                if let marker { item.setData(Data(), forType: .init(marker)) }
                pasteboard.clearContents()
                _ = pasteboard.writeObjects([item])
            }
            for type in ["org.nspasteboard.ConcealedType", "org.nspasteboard.TransientType", "org.nspasteboard.AutoGeneratedType"] {
                setContent(type)
                expectNil(try store.capture(pasteboard: pasteboard, sourceName: "Synthetic", sourceBundleID: nil))
            }
            setContent()
            store.preferences.excludedBundleIDs = ["invalid.excluded"]
            expectNil(try store.capture(pasteboard: pasteboard, sourceName: "Excluded", sourceBundleID: "invalid.excluded"))
            store.preferences.isMonitoringPaused = true
            expectNil(try store.capture(pasteboard: pasteboard, sourceName: "Synthetic", sourceBundleID: nil))
            store.preferences.pauseUntil = Date().addingTimeInterval(60)
            expectNil(try store.capture(pasteboard: pasteboard, sourceName: "Synthetic", sourceBundleID: nil))
            store.preferences.pauseUntil = Date().addingTimeInterval(-1)
            expectNotNil(try store.capture(pasteboard: pasteboard, sourceName: "Synthetic", sourceBundleID: nil))
            expectFalse(store.preferences.isMonitoringPaused)
            expectNil(store.preferences.pauseUntil)
            expectEqual(store.items.count, 1)
        }
    }

    func testHistoryRetentionPermanentExpiredPinnedAndFreshBoundaries() async throws {
        let directory = try temporaryDirectory()
        defer { try? FileManager.default.removeItem(at: directory) }
        try await MainActor.run {
            let defaults = try JSONDecoder().decode(AppPreferences.self, from: Data("{}".utf8))
            expectEqual(defaults.historyRetentionDays, 0)
            expectTrue(defaults.pasteToActiveApp)
            expectFalse(defaults.alwaysPastePlainText)
            let store = try ClipboardStore(directoryURL: directory)
            let now = Date()
            let old = now.addingTimeInterval(-2 * 86_400)
            let board = try store.createPinboard(name: "keep", colorHex: "#ABCDEF")
            let expired = try store.add(ClipboardItem(createdAt: old, plainText: "old unpinned"))
            let pinned = try store.add(ClipboardItem(createdAt: old, plainText: "old pinned", pinboardIDs: [board.id]))
            let fresh = try store.add(ClipboardItem(createdAt: now.addingTimeInterval(-86_400 + 60), plainText: "inside one-day boundary"))
            let future = try store.add(ClipboardItem(createdAt: now.addingTimeInterval(60), plainText: "future clock skew"))
            expectEqual(store.search(query: "").count, 4, "Default permanent retention must not age out old entries")
            store.preferences.historyRetentionDays = 1
            try store.save()
            expectFalse(store.items.contains { $0.id == expired })
            expectEqual(store.items.first { $0.id == pinned }?.isInHistory, false)
            expectEqual(store.search(query: "", pinboardID: board.id).map(\.id), [pinned])
            expectEqual(Set(store.search(query: "").map(\.id)), [fresh, future])
            store.preferences.historyRetentionDays = 0
            _ = try store.add(ClipboardItem(createdAt: old, plainText: "old after setting permanent"))
            expectTrue(store.items.contains { $0.plainText == "old after setting permanent" })
        }
    }

    func testMultiSelectionOrderRawRepresentationsAndAtomicFailure() async throws {
        let directory = try temporaryDirectory()
        defer { try? FileManager.default.removeItem(at: directory) }
        try await MainActor.run {
            let store = try ClipboardStore(directoryURL: directory)
            let pasteboard = privatePasteboard()
            defer { pasteboard.releaseGlobally() }
            let text = try store.add(ClipboardItem(plainText: "alpha 中文", payloads: [NSPasteboard.PasteboardType.string.rawValue: Data("alpha 中文".utf8)]))
            let rich = try store.add(ClipboardItem(title: "rich"))
            let attributed = NSAttributedString(string: "BOLD", attributes: [.font: NSFont.boldSystemFont(ofSize: 24)])
            try store.updateRichTextItem(id: rich, attributedString: attributed)
            let rtf = try requireValue(store.items.first { $0.id == rich }?.payloads[NSPasteboard.PasteboardType.rtf.rawValue])
            let fileURL = directory.appendingPathComponent("synthetic file.txt").absoluteString
            let file = try store.add(ClipboardItem(kind: .files, plainText: "synthetic file.txt", payloads: [NSPasteboard.PasteboardType.fileURL.rawValue: Data(fileURL.utf8)]))
            let png = try textImageFixture()
            let image = try store.add(ClipboardItem(kind: .image, payloads: [NSPasteboard.PasteboardType.png.rawValue: png]))
            try store.writeToPasteboard(ids: [file, rich, image, text], pasteboard: pasteboard, plainTextOnly: false)
            let objects = try requireValue(pasteboard.pasteboardItems)
            expectEqual(objects.count, 4)
            expectEqual(objects[0].data(forType: .fileURL), Data(fileURL.utf8))
            expectEqual(objects[1].data(forType: .rtf), rtf)
            expectEqual(objects[2].data(forType: .png), png)
            expectEqual(objects[3].string(forType: .string), "alpha 中文")
            try store.writeToPasteboard(ids: [rich, text, file], pasteboard: pasteboard, plainTextOnly: true)
            expectEqual(pasteboard.string(forType: .string), "BOLD\nalpha 中文\nsynthetic file.txt")
            expectEqual(pasteboard.pasteboardItems?.count, 1)
            expectNil(pasteboard.data(forType: .rtf))
            let previous = pasteboard.changeCount
            expectThrows(try store.writeToPasteboard(ids: [text, UUID()], pasteboard: pasteboard, plainTextOnly: false))
            expectEqual(pasteboard.changeCount, previous, "Invalid selections cannot partially replace the clipboard")
            expectThrows(try store.writeToPasteboard(ids: [text, image], pasteboard: pasteboard, plainTextOnly: true))
            expectEqual(pasteboard.changeCount, previous)
        }
    }

    func testPinboardReorderingDuplicationAndDeletingPinOnlyContent() async throws {
        let directory = try temporaryDirectory()
        defer { try? FileManager.default.removeItem(at: directory) }
        try await MainActor.run {
            let store = try ClipboardStore(directoryURL: directory)
            let a = try store.createPinboard(name: "a", colorHex: "#112233")
            let b = try store.createPinboard(name: "b", colorHex: "#445566")
            try store.updatePinboard(id: a.id, colorHex: "#ABCDEF")
            try store.reorderPinboards(ids: [b.id, a.id])
            expectEqual(store.pinboards.map(\.id), [b.id, a.id])
            expectEqual(store.pinboards.first { $0.id == a.id }?.colorHex, "#ABCDEF")
            expectThrows(try store.reorderPinboards(ids: [b.id, b.id]))
            let history = try store.add(ClipboardItem(plainText: "history", pinboardIDs: [a.id]))
            let onlyA = try store.add(ClipboardItem(plainText: "pin only a", pinboardIDs: [a.id], isInHistory: false))
            let both = try store.add(ClipboardItem(plainText: "pin both", pinboardIDs: [a.id, b.id], isInHistory: false))
            let duplicate = try store.duplicateItem(id: history)
            expectFalse(duplicate == history)
            expectEqual(store.items.first { $0.id == duplicate }?.plainText, "history")
            expectEqual(store.items.first { $0.id == duplicate }?.pinboardIDs, [a.id])
            try store.removePinboard(id: a.id)
            expectFalse(store.items.contains { $0.id == onlyA })
            expectTrue(store.items.contains { $0.id == history })
            expectTrue(store.items.contains { $0.id == duplicate })
            expectEqual(store.items.first { $0.id == both }?.pinboardIDs, [b.id])
            let reopened = try ClipboardStore(directoryURL: directory)
            expectEqual(reopened.pinboards.map(\.id), [b.id])
        }
    }

    func testLocalVisionOCRSearchPersistenceAndOriginalPayloadIsolation() async throws {
        let directory = try temporaryDirectory()
        defer { try? FileManager.default.removeItem(at: directory) }
        let fixture = try await MainActor.run { () -> (ClipboardStore, UUID, Data) in
            let store = try ClipboardStore(directoryURL: directory)
            let data = try textImageFixture()
            let id = try store.add(ClipboardItem(title: "OCR fixture", kind: .image, payloads: [NSPasteboard.PasteboardType.png.rawValue: data]))
            return (store, id, data)
        }
        let recognized = try await fixture.0.recognizeImageText(id: fixture.1)
        expectTrue(recognized.uppercased().contains("PASTE"), "Vision must recognize text from real rendered pixels")
        expectTrue(recognized.contains("8426"))
        try await MainActor.run {
            let store = fixture.0
            let item = try requireValue(store.items.first { $0.id == fixture.1 })
            expectEqual(item.kind, .image)
            expectNil(item.plainText, "OCR is an index, not a replacement of the original image representation")
            expectEqual(item.recognizedText, recognized)
            expectEqual(item.payloads[NSPasteboard.PasteboardType.png.rawValue], fixture.2)
            expectEqual(store.search(query: "replica 8426").map(\.id), [fixture.1])
            let reopened = try ClipboardStore(directoryURL: directory)
            expectEqual(reopened.items.first?.recognizedText, recognized)
            let duplicate = try reopened.add(ClipboardItem(kind: .image, payloads: [NSPasteboard.PasteboardType.png.rawValue: fixture.2]))
            expectEqual(duplicate, fixture.1, "Persisted OCR metadata must not defeat raw-content deduplication")
            let pasteboard = privatePasteboard()
            defer { pasteboard.releaseGlobally() }
            try reopened.writeToPasteboard(id: fixture.1, pasteboard: pasteboard, plainTextOnly: false)
            expectEqual(pasteboard.data(forType: .png), fixture.2)
            expectNil(pasteboard.data(forType: .init("com.pastereplica.internal.recognized-text")))
            try reopened.writeToPasteboard(id: fixture.1, pasteboard: pasteboard, plainTextOnly: true)
            expectEqual(pasteboard.string(forType: .string), recognized)
        }
        let invalid = try await ImageTextRecognizer.recognize(imageData: Data([0, 1, 2, 3]))
        expectEqual(invalid, "", "REA image preprocessing returns no results for nonempty undecodable image data")
        do { _ = try await ImageTextRecognizer.recognize(imageData: Data()); expectTrue(false, "Original public wrapper rejects empty input") }
        catch { }
    }

    func testAddressStackArrayAndWindowContracts() async throws {
        for original in [[], [1], [1, 2], [1, 2, 3], [1, 2, 2, 4]] {
            let alias = original
            var mutable = original
            OriginalStackFunctions.f_10008468c(&mutable)
            expectEqual(mutable, Array(original.reversed()))
            expectEqual(alias, original, "In-place reverse must preserve independent Array storage")
            OriginalStackFunctions.f_10008468c(&mutable)
            expectEqual(mutable, original)
        }
        await MainActor.run {
            expectFalse(OriginalStackFunctions.f_1000114fc())
            expectFalse(OriginalStackFunctions.f_1000114ec())
            expectFalse(OriginalStackFunctions.f_1000114f4())
            let window = NSWindow(contentRect: .init(x: 0, y: 0, width: 264, height: 76),
                                  styleMask: .borderless, backing: .buffered, defer: false)
            let controller = OriginalStackWindowController(window: window)
            controller.f_100011138()
            expectEqual(window.level.rawValue, 25)
            expectEqual(window.collectionBehavior.rawValue, 257)
            expectTrue(window.isMovableByWindowBackground)
            expectEqual(window.frameAutosaveName, "com.wiheads.paste.paste-stack-frame")
            expectFalse(window.isVisible)
            OriginalStackWindowController(window: nil).f_100011138()
        }
    }

    func testAddressStackTableContracts() async throws {
        let counts = [0, 1, 2, 9, 10, 11, 257]
        let controllers = await MainActor.run {
            counts.map { count -> OriginalStackTableController in
                let controller = OriginalStackTableController()
                controller.snippets = (0..<count).map { ClipboardItem(plainText: "row \($0)") }
                controller.tableView.reloadData()
                expectEqual(controller.f_100085230(), count)
                expectEqual(controller.tableView.numberOfRows, count)
                for row in [Int.min, -1, 0, count, Int.max] {
                    expectFalse(controller.f_100085670(row: row))
                    expectEqual(controller.tableView.delegate?.tableView?(controller.tableView, shouldSelectRow: row), false)
                }
                let constraint = controller.f_100082b90()
                expectTrue(constraint === controller.f_100082b90())
                expectTrue(constraint.firstItem === controller.scrollView)
                expectEqual(constraint.constant, 44)
                expectFalse(constraint.isActive)
                NSAnimationContext.runAnimationGroup { context in
                    context.duration = 0
                    controller.f_100083a20()
                }
                expectTrue(constraint.isActive)
                return controller
            }
        }
        try await Task.sleep(nanoseconds: 100_000_000)
        await MainActor.run {
            for (count, controller) in zip(counts, controllers) {
                expectEqual(controller.f_100082b90().constant, CGFloat(min(10, max(1, count))) * 44)
            }
        }
    }

    func testAddressOCRPreparationAndWordGeometry() async throws {
        let image = try await MainActor.run { try textImageFixture(text: "PASTE, PASTE! 8426") }
        expectEqual(ImageTextRecognizer.f_1002d4ba0(imageData: image, maximumDimension: 1400), image)
        let resized = try requireValue(ImageTextRecognizer.f_1002d4ba0(imageData: image, maximumDimension: 128))
        let source = try requireValue(CGImageSourceCreateWithData(resized as CFData, nil))
        let properties = try requireValue(CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [CFString: Any])
        expectEqual(properties[kCGImagePropertyPixelWidth] as? Int, 128)
        expectTrue((properties[kCGImagePropertyPixelHeight] as? Int ?? 0) <= 128)
        expectEqual(CGImageSourceGetType(source) as String?, "public.png")
        let zeroLimit = try requireValue(ImageTextRecognizer.f_1002d4ba0(imageData: image, maximumDimension: 0))
        let zeroSource = try requireValue(CGImageSourceCreateWithData(zeroLimit as CFData, nil))
        let zeroProperties = try requireValue(CGImageSourceCopyPropertiesAtIndex(zeroSource, 0, nil) as? [CFString: Any])
        expectEqual(zeroProperties[kCGImagePropertyPixelWidth] as? Int, 1400)
        expectNil(ImageTextRecognizer.f_1002d4ba0(imageData: Data([0, 1]), maximumDimension: 128))
        try await MainActor.run {
            for width in [10, 11] {
                let bitmap = try requireValue(NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: width, pixelsHigh: 20,
                    bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
                    colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0))
                let data = try requireValue(bitmap.representation(using: .png, properties: [:]))
                expectEqual(ImageTextRecognizer.f_1002d4ba0(imageData: data, maximumDimension: 20), width == 10 ? nil : data)
            }
        }
        let empty = try ImageTextRecognizer.f_1002d4830(imageData: Data([0, 1]), maximumDimension: 128)
        expectEqual(empty.words, [])
        expectEqual(empty.text, "")
        do {
            _ = try ImageTextRecognizer.f_1002d4738(imageData: Data(), maximumDimension: 128)
            expectTrue(false)
        } catch {
            expectEqual((error as NSError).domain, "PasteRecognition.OCRError")
            expectEqual((error as NSError).code, 0)
            expectTrue((error as NSError).userInfo.isEmpty)
            expectTrue(error is OCRError)
        }
        let document = try await ImageTextRecognizer.recognizeDocument(imageData: image)
        let repeated = document.words.filter { $0.text.uppercased() == "PASTE" }
        expectEqual(repeated.count, 2)
        expectTrue(document.words.contains { $0.text == "8426" })
        for word in document.words {
            expectTrue(word.confidence >= 0 && word.confidence <= 1)
            let box = try requireValue(word.boundingBox)
            expectTrue(box.minX >= 0 && box.minY >= 0 && box.maxX <= 1.001 && box.maxY <= 1.001)
            expectTrue(box.width > 0 && box.height > 0)
        }
        if repeated.count == 2 {
            expectGreaterThan(try requireValue(repeated[1].boundingBox).minX,
                              try requireValue(repeated[0].boundingBox).minX)
        }
        let directory = try temporaryDirectory()
        defer { try? FileManager.default.removeItem(at: directory) }
        let store = try await MainActor.run { try ClipboardStore(directoryURL: directory) }
        let id = try await MainActor.run { try store.add(ClipboardItem(kind: .image, payloads: ["public.png": image])) }
        let stored = try await store.recognizeImageDocument(id: id)
        try await MainActor.run {
            let reopened = try ClipboardStore(directoryURL: directory)
            expectEqual(reopened.items.first?.recognizedTextDocument, stored)
            let board = privatePasteboard()
            defer { board.releaseGlobally() }
            try reopened.writeToPasteboard(id: id, pasteboard: board)
            expectNil(board.data(forType: .init("com.pastereplica.internal.recognized-document+json")))
            expectEqual(board.data(forType: .png), image)
        }
    }

    func testTransientOptOutStillRejectsReplicaWriteBack() async throws {
        let directory = try temporaryDirectory()
        defer { try? FileManager.default.removeItem(at: directory) }
        try await MainActor.run {
            let store = try ClipboardStore(directoryURL: directory)
            store.preferences.ignoreTransientContent = false
            let pasteboard = privatePasteboard()
            defer { pasteboard.releaseGlobally() }
            let object = NSPasteboardItem()
            object.setString("external transient", forType: .string)
            object.setData(Data(), forType: .init("org.nspasteboard.TransientType"))
            pasteboard.clearContents()
            expectTrue(pasteboard.writeObjects([object]))
            let id = try requireValue(store.capture(pasteboard: pasteboard, sourceName: "Synthetic", sourceBundleID: nil))
            try store.writeToPasteboard(id: id, pasteboard: pasteboard, plainTextOnly: false)
            expectNil(try store.capture(pasteboard: pasteboard, sourceName: "Replica", sourceBundleID: nil))
            expectEqual(store.items.count, 1)
        }
    }

    func testRefreshPreservesPendingEditsWithoutNoOpWrites() async throws {
        let directory = try temporaryDirectory()
        defer { try? FileManager.default.removeItem(at: directory) }
        try await MainActor.run {
            let a = try ClipboardStore(directoryURL: directory)
            let id = try a.add(ClipboardItem(title: "original", kind: .image,
                                             payloads: ["public.png": Data(repeating: 123, count: 1_048_576)]))
            let b = try ClipboardStore(directoryURL: directory)
            let url = directory.appendingPathComponent("clipboard.json")
            let before = try FileManager.default.attributesOfItem(atPath: url.path)
            var updates = 0
            let subscription = a.objectWillChange.sink { updates += 1 }
            for _ in 0..<5 { try a.reload(); try a.save() }
            let after = try FileManager.default.attributesOfItem(atPath: url.path)
            expectEqual(before[.systemFileNumber] as? NSNumber, after[.systemFileNumber] as? NSNumber)
            expectEqual(before[.modificationDate] as? Date, after[.modificationDate] as? Date)
            expectEqual(updates, 0, "No-op polling must not publish or rewrite image history")
            a.preferences.appearance = "dark"
            if let i = a.items.firstIndex(where: { $0.id == id }) { a.items[i].title = "pending edit" }
            b.preferences.historyLimit = 42
            try b.save()
            try a.reload()
            expectEqual(a.preferences.appearance, "dark")
            expectEqual(a.preferences.historyLimit, 42)
            expectEqual(a.items.first { $0.id == id }?.title, "pending edit")
            let beforeSave = try ClipboardStore(directoryURL: directory)
            expectEqual(beforeSave.preferences.appearance, "system", "Reload preserves pending edits without secretly saving them")
            try a.save()
            let reopened = try ClipboardStore(directoryURL: directory)
            expectEqual(reopened.preferences.appearance, "dark")
            expectEqual(reopened.preferences.historyLimit, 42)
            expectEqual(reopened.items.first { $0.id == id }?.title, "pending edit")
            subscription.cancel()
        }
    }

    func runWorker(directory: URL, prefix: String) async throws {
        try await MainActor.run {
            let store = try ClipboardStore(directoryURL: directory)
            for i in 0..<30 { _ = try store.add(ClipboardItem(plainText: "\(prefix)-\(i)")) }
        }
    }

    func testTwoRealProcessesDoNotLoseConcurrentWrites() async throws {
        let directory = try temporaryDirectory()
        defer { try? FileManager.default.removeItem(at: directory) }
        var processes: [Process] = []
        var outputs: [Pipe] = []
        for prefix in ["process-a", "process-b"] {
            let process = Process()
            process.executableURL = URL(fileURLWithPath: CommandLine.arguments[0])
            process.arguments = ["--worker", directory.path, prefix]
            let output = Pipe()
            process.standardOutput = output
            process.standardError = output
            try process.run()
            processes.append(process)
            outputs.append(output)
        }
        for (process, output) in zip(processes, outputs) {
            process.waitUntilExit()
            let log = String(data: output.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
            expectEqual(process.terminationStatus, 0, log)
        }
        try await MainActor.run {
            let store = try ClipboardStore(directoryURL: directory)
            expectEqual(store.items.count, 60)
            for prefix in ["process-a", "process-b"] {
                for i in 0..<30 { expectTrue(store.items.contains { $0.plainText == "\(prefix)-\(i)" }) }
            }
        }
    }
}
