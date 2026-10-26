import AppKit
import CoreFoundation
import Darwin
import Foundation
import PastoCore

private struct RPCFailure: Error {
    let code: Int
    let message: String
}

private func invalid(_ message: String) -> RPCFailure { RPCFailure(code: -32602, message: message) }

private struct ToolDefinition {
    let name: String
    let description: String
    let properties: [String: Any]
    var required: [String] = []
    var readOnly = false
    var destructive = false

    var json: [String: Any] {
        ["name": name, "description": description,
         "inputSchema": ["type": "object", "properties": properties, "required": required,
                         "additionalProperties": false],
         "annotations": ["readOnlyHint": readOnly, "destructiveHint": destructive,
                         "openWorldHint": false]]
    }
}

@MainActor
private final class Server {
    private let store: ClipboardStore
    private var initialized = false
    private let maxResponseBytes = 2 * 1024 * 1024
    private let definitions: [ToolDefinition]

    init(directory: URL) throws {
        store = try ClipboardStore(directoryURL: directory)
        let string: [String: Any] = ["type": "string"]
        let identifier: [String: Any] = ["type": "string", "format": "uuid"]
        let boolean: [String: Any] = ["type": "boolean"]
        definitions = [
            ToolDefinition(name: "search", description: "搜索历史和 Pinboard；无参数返回最近项目。兼容原版已证实的输入字段。", properties: [
                "query": string, "type": ["type": "string", "enum": ["text", "image", "file", "color", "link"]],
                "app": string, "device": string, "title": string, "pinboard_id": identifier,
                "date_from": string, "date_to": string,
                "limit": ["type": "integer", "default": 20, "description": "默认 20，实际值限制在 1 到 100。"]
            ], readOnly: true),
            ToolDefinition(name: "read_item", description: "按 search 返回的 id 读取完整内容；支持文本和 PNG 图像。", properties: ["id": identifier], required: ["id"], readOnly: true),
            ToolDefinition(name: "create_item", description: "保存文本，自动识别 text/color/link；不写系统剪贴板。list_id 指向私有 Pinboard；新建仅置顶项无历史时间。", properties: ["content": string, "list_id": identifier], required: ["content"]),
            ToolDefinition(name: "update_item", description: "更新 title/content，至少传入一项；图片和文件只能改标题。", properties: ["id": identifier, "title": string, "content": string], required: ["id"]),
            ToolDefinition(name: "delete_item", description: "不可逆删除。confirm 缺省或 false 仅预览，true 才实际删除。", properties: ["id": identifier, "confirm": boolean], required: ["id"], destructive: true),
            ToolDefinition(name: "list_pinboards", description: "列出 Pinboard 的 id、name、itemCount。", properties: [:], readOnly: true),
            ToolDefinition(name: "create_pinboard", description: "创建私有 Pinboard，名称去除首尾空白。", properties: ["name": string], required: ["name"]),
            ToolDefinition(name: "rename_pinboard", description: "重命名 Pinboard，名称去除首尾空白。", properties: ["id": identifier, "name": string], required: ["id", "name"]),
            ToolDefinition(name: "delete_pinboard", description: "confirm 缺省或 false 仅预览；true 删除 Pinboard，保留历史项目。", properties: ["id": identifier, "confirm": boolean], required: ["id"], destructive: true),
            ToolDefinition(name: "add_item_to_pinboard", description: "将已保存项目加入 Pinboard；重复调用保持幂等。", properties: ["item_id": identifier, "pinboard_id": identifier], required: ["item_id", "pinboard_id"]),
            ToolDefinition(name: "remove_item_from_pinboard", description: "仅移除指定 Pinboard 的归属，保留历史和其他 Pinboard。", properties: ["item_id": identifier, "pinboard_id": identifier], required: ["item_id", "pinboard_id"]),
            ToolDefinition(name: "replica_restore_item", description: "复刻扩展，非原版已证工具：恢复 UI 软删除项目；无法恢复 delete_item 永久删除。", properties: ["item_id": identifier], required: ["item_id"]),
            ToolDefinition(name: "replica_copy_item", description: "复刻扩展，非原版已证工具。显式写入具名私有剪贴板；只有 allow_system_clipboard=true 才可写 general，具有剪贴板副作用。", properties: ["item_id": identifier, "pasteboard_name": string, "plain_text_only": boolean, "allow_system_clipboard": boolean], required: ["item_id", "pasteboard_name"])
        ]
    }

    func sendError(id: Any = NSNull(), code: Int, message: String) {
        send(["jsonrpc": "2.0", "id": id, "error": ["code": code, "message": message]])
    }

    private func send(_ object: [String: Any]) {
        guard var data = try? JSONSerialization.data(withJSONObject: object, options: [.sortedKeys, .fragmentsAllowed]) else { return }
        if data.count > maxResponseBytes {
            data = try! JSONSerialization.data(withJSONObject: ["jsonrpc": "2.0", "id": object["id"] ?? NSNull(),
                    "error": ["code": -32001, "message": "Response exceeds 2 MiB; narrow the search or content."]])
        }
        data.append(0x0A)
        FileHandle.standardOutput.write(data)
    }

    func receive(_ frame: Data) {
        let object: Any
        do { object = try JSONSerialization.jsonObject(with: frame, options: [.fragmentsAllowed]) }
        catch { sendError(code: -32700, message: "Parse error: invalid JSON or UTF-8"); return }
        guard let request = object as? [String: Any], request["jsonrpc"] as? String == "2.0",
              let method = request["method"] as? String else {
            sendError(code: -32600, message: "Invalid JSON-RPC 2.0 request"); return
        }
        let id = request["id"] ?? NSNull()
        if let number = id as? NSNumber, CFGetTypeID(number) == CFBooleanGetTypeID() {
            sendError(code: -32600, message: "Request id must be a string, number, or null"); return
        }
        guard id is NSNull || id is String || id is NSNumber else {
            sendError(code: -32600, message: "Request id must be a string, number, or null"); return
        }
        // 通知绝不执行有副作用的工具，也绝不输出响应。
        guard request.keys.contains("id") else { return }
        do {
            let params: [String: Any]
            if let value = request["params"] {
                guard let dictionary = value as? [String: Any] else { throw invalid("params must be an object") }
                params = dictionary
            } else { params = [:] }
            let result: [String: Any]
            switch method {
            case "initialize":
                guard !initialized else { throw invalid("Already initialized") }
                guard let requestedVersion = params["protocolVersion"] as? String,
                      params["capabilities"] is [String: Any], let client = params["clientInfo"] as? [String: Any],
                      client["name"] is String, client["version"] is String else {
                    throw invalid("initialize requires protocolVersion, capabilities and clientInfo")
                }
                let supported = ["2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25"]
                result = ["protocolVersion": supported.contains(requestedVersion) ? requestedVersion : "2024-11-05",
                          "capabilities": ["tools": ["listChanged": false]],
                          "serverInfo": ["name": "pasto", "version": "0.1.0"],
                          "instructions": "独立本地复刻。工具字段根据安装包静态证据重建，未宣称与原版完整 schema 或语义等价。replica_* 为明确扩展。create_item 不写剪贴板。"]
                initialized = true
            case "ping": result = [:]
            case "tools/list":
                try requireInitialized()
                if let cursor = params["cursor"], !(cursor is NSNull) { throw invalid("No cursor is supported") }
                result = ["tools": definitions.map(\.json)]
            case "tools/call":
                try requireInitialized()
                guard let name = params["name"] as? String,
                      let definition = definitions.first(where: { $0.name == name }) else { throw invalid("Unknown tool") }
                let arguments: [String: Any]
                if let supplied = params["arguments"] {
                    guard let dictionary = supplied as? [String: Any] else { throw invalid("arguments must be an object") }
                    arguments = dictionary
                } else { arguments = [:] }
                try validate(arguments, against: definition)
                try store.reload()
                do { result = try call(name, arguments) }
                catch let failure as RPCFailure { throw failure }
                catch {
                    result = ["isError": true, "content": [["type": "text", "text": "操作失败：\(error.localizedDescription)"]]]
                }
            default: throw RPCFailure(code: -32601, message: "Method not found")
            }
            send(["jsonrpc": "2.0", "id": id, "result": result])
        } catch let failure as RPCFailure {
            sendError(id: id, code: failure.code, message: failure.message)
        } catch { sendError(id: id, code: -32603, message: "Local storage operation failed") }
    }

    private func requireInitialized() throws {
        if !initialized { throw RPCFailure(code: -32002, message: "Server not initialized") }
    }

    private func validate(_ args: [String: Any], against tool: ToolDefinition) throws {
        guard Set(args.keys).isSubset(of: Set(tool.properties.keys)) else { throw invalid("Unknown argument") }
        for key in tool.required where args[key] == nil { throw invalid("Missing argument: \(key)") }
        for (key, value) in args {
            let schema = tool.properties[key] as! [String: Any]
            switch schema["type"] as? String {
            case "string":
                guard let text = value as? String else { throw invalid("\(key) must be a string") }
                if text.utf8.count > 512 * 1024 { throw invalid("\(key) exceeds 512 KiB") }
                if schema["format"] as? String == "uuid", UUID(uuidString: text) == nil { throw invalid("\(key) must be a UUID") }
                if let allowed = schema["enum"] as? [String], !allowed.contains(text) { throw invalid("Invalid \(key)") }
            case "boolean":
                guard let number = value as? NSNumber, CFGetTypeID(number) == CFBooleanGetTypeID() else { throw invalid("\(key) must be a boolean") }
            case "integer":
                guard let number = value as? NSNumber, CFGetTypeID(number) != CFBooleanGetTypeID(),
                      number.doubleValue.isFinite, abs(number.doubleValue) <= Double(Int.max),
                      number.doubleValue.rounded() == number.doubleValue,
                      number.intValue >= (schema["minimum"] as? Int ?? Int.min),
                      number.intValue <= (schema["maximum"] as? Int ?? Int.max) else { throw invalid("Invalid integer: \(key)") }
            default: break
            }
        }
    }

    private func uuid(_ args: [String: Any], _ key: String) throws -> UUID {
        guard let value = args[key] as? String, let id = UUID(uuidString: value) else { throw invalid("Invalid \(key)") }
        return id
    }

    private func item(_ id: UUID, includeDeleted: Bool = false) throws -> ClipboardItem {
        guard let item = store.items.first(where: { $0.id == id && (includeDeleted || !$0.isDeleted) }) else {
            throw invalid("No saved item with this id")
        }
        return item
    }

    private func pinboard(_ id: UUID) throws -> Pinboard {
        guard let board = store.pinboards.first(where: { $0.id == id }) else { throw invalid("No pinboard with this id") }
        return board
    }

    private func typeName(_ kind: ClipboardKind) -> String {
        switch kind { case .files: return "file"; case .richText, .unknown: return "text"; default: return kind.rawValue }
    }

    private func summary(_ item: ClipboardItem) -> [String: Any] {
        var value: [String: Any] = ["id": item.id.uuidString, "type": typeName(item.kind),
                                  "preview": String((item.plainText ?? item.title).prefix(300)),
                                  "app": item.sourceName, "device": item.sourceDevice]
        if item.isInHistory { value["timestamp"] = ISO8601DateFormatter().string(from: item.createdAt) }
        return value
    }

    private func boardSummary(_ board: Pinboard) -> [String: Any] {
        ["id": board.id.uuidString, "name": board.name,
         "itemCount": store.items.filter { !$0.isDeleted && $0.pinboardIDs.contains(board.id) }.count]
    }

    private func result(_ value: [String: Any]) throws -> [String: Any] {
        let text = String(data: try JSONSerialization.data(withJSONObject: value, options: [.sortedKeys]), encoding: .utf8)!
        return ["content": [["type": "text", "text": text]], "structuredContent": value, "isError": false]
    }

    private func detectKind(_ text: String) -> ClipboardKind {
        if text.range(of: "^#?[0-9a-fA-F]{6}$", options: .regularExpression) != nil { return .color }
        if !text.contains(where: \.isWhitespace), let url = URL(string: text),
           let scheme = url.scheme?.lowercased(), ["http", "https", "ftp", "mailto"].contains(scheme),
           scheme == "mailto" || url.host != nil { return .link }
        return .text
    }

    private func nonempty(_ value: String?, name: String, trim: Bool) throws -> String {
        guard let value, !value.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { throw invalid("\(name) cannot be empty") }
        return trim ? value.trimmingCharacters(in: .whitespacesAndNewlines) : value
    }

    private func date(_ text: String?, upper: Bool) throws -> Date? {
        guard let text else { return nil }
        if text.range(of: "^\\d{4}-\\d{2}-\\d{2}$", options: .regularExpression) != nil {
            let formatter = DateFormatter()
            formatter.locale = Locale(identifier: "en_US_POSIX"); formatter.timeZone = .current
            formatter.dateFormat = "yyyy-MM-dd"; formatter.isLenient = false
            guard let parsed = formatter.date(from: text), formatter.string(from: parsed) == text else { throw invalid("Invalid ISO-8601 date") }
            return upper ? Calendar.current.date(byAdding: .day, value: 1, to: parsed) : parsed
        }
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let parsed = formatter.date(from: text) { return parsed }
        formatter.formatOptions = [.withInternetDateTime]
        guard let parsed = formatter.date(from: text) else { throw invalid("Invalid ISO-8601 timestamp") }
        return parsed
    }

    private func call(_ name: String, _ args: [String: Any]) throws -> [String: Any] {
        switch name {
        case "search":
            let boardID = try (args["pinboard_id"] as? String).map { _ in try uuid(args, "pinboard_id") }
            if let boardID { _ = try pinboard(boardID) }
            let lower = try date(args["date_from"] as? String, upper: false)
            let upper = try date(args["date_to"] as? String, upper: true)
            if let lower, let upper, lower >= upper { throw invalid("date_from must precede date_to") }
            let query = args["query"] as? String ?? ""
            let terms = query.split(whereSeparator: \.isWhitespace).map(String.init)
            var items = store.items.filter { value in
                !value.isDeleted && (value.isInHistory || !value.pinboardIDs.isEmpty)
                && (boardID == nil || value.pinboardIDs.contains(boardID!))
                && terms.allSatisfy { ([value.title, value.plainText ?? ""].joined(separator: "\n")).localizedCaseInsensitiveContains($0) }
            }.sorted { $0.createdAt > $1.createdAt }
            if let type = args["type"] as? String { items = items.filter { typeName($0.kind) == type } }
            if let app = args["app"] as? String { items = items.filter { $0.sourceName.localizedCaseInsensitiveContains(app) } }
            if let device = args["device"] as? String { items = items.filter { $0.sourceDevice.localizedCaseInsensitiveContains(device) } }
            if let title = args["title"] as? String { items = items.filter { $0.title.localizedCaseInsensitiveContains(title) } }
            if let lower { items = items.filter { $0.isInHistory && $0.createdAt >= lower } }
            if let upper { items = items.filter { $0.isInHistory && $0.createdAt < upper } }
            let limit = min(100, max(1, args["limit"] as? Int ?? 20))
            return try result(["items": items.prefix(limit).map(summary), "hasMore": items.count > limit])
        case "read_item":
            let value = try item(uuid(args, "id"))
            if value.kind == .image {
                guard let source = value.payloads[NSPasteboard.PasteboardType.png.rawValue] ?? value.payloads[NSPasteboard.PasteboardType.tiff.rawValue],
                      let bitmap = NSBitmapImageRep(data: source), let original = bitmap.cgImage else { throw invalid("Image representation unavailable") }
                var scale = min(1.0, 1024.0 / Double(max(original.width, original.height)))
                var png = Data()
                while true {
                    let width = max(1, Int(Double(original.width) * scale))
                    let height = max(1, Int(Double(original.height) * scale))
                    guard let context = CGContext(data: nil, width: width, height: height, bitsPerComponent: 8,
                                                  bytesPerRow: 0, space: CGColorSpaceCreateDeviceRGB(),
                                                  bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else { throw invalid("Cannot resize image") }
                    context.interpolationQuality = .high
                    context.draw(original, in: CGRect(x: 0, y: 0, width: width, height: height))
                    guard let image = context.makeImage(), let encoded = NSBitmapImageRep(cgImage: image).representation(using: .png, properties: [:]) else { throw invalid("Cannot encode PNG") }
                    png = encoded
                    if png.count <= 1024 * 1024 { break }
                    if width == 1 && height == 1 { throw invalid("Image exceeds response limit") }
                    scale *= 0.5
                }
                return ["content": [["type": "image", "data": png.base64EncodedString(), "mimeType": "image/png"]], "isError": false]
            }
            var text = value.plainText ?? value.title
            if value.kind == .color, text.range(of: "^#?[0-9a-fA-F]{6}$", options: .regularExpression) != nil {
                text = "#" + text.replacingOccurrences(of: "#", with: "").uppercased()
            }
            return ["content": [["type": "text", "text": text]], "isError": false]
        case "create_item":
            let content = try nonempty(args["content"] as? String, name: "content", trim: false)
            let boardID = try (args["list_id"] as? String).map { _ in try uuid(args, "list_id") }
            if let boardID { _ = try pinboard(boardID) }
            let existing = store.items.first { !$0.isDeleted && $0.plainText == content }
            let id: UUID
            if var existing {
                if boardID == nil && !existing.isInHistory {
                    existing.isInHistory = true
                    existing.createdAt = Date()
                    id = try store.add(existing)
                } else { id = existing.id }
            }
            else {
                let value = ClipboardItem(title: String(content.prefix(80)), kind: detectKind(content), plainText: content,
                                          sourceName: "Pasto MCP", pinboardIDs: boardID.map { [$0] } ?? [],
                                          sourceDevice: "此Mac", isInHistory: boardID == nil)
                id = try store.add(value)
            }
            if let boardID { try store.assign(ids: [id], to: boardID) }
            return try result(summary(item(id)))
        case "update_item":
            let id = try uuid(args, "id"), value = try item(id)
            guard args["title"] != nil || args["content"] != nil else { throw invalid("Pass title or content") }
            if let content = args["content"] as? String {
                guard value.kind != .image && value.kind != .files else { throw invalid("Image/file content cannot be edited") }
                _ = try nonempty(content, name: "content", trim: false)
            }
            try store.updateItem(id: id, title: args["title"] as? String, text: args["content"] as? String)
            return try result(summary(item(id)))
        case "delete_item":
            let id = try uuid(args, "id"), value = try item(id), confirmed = args["confirm"] as? Bool ?? false
            if confirmed { try store.permanentlyDelete(ids: [id]) }
            return try result(["deleted": confirmed, "item": summary(value), "message": confirmed ? "项目已永久删除。" : "预览：confirm=true 后永久删除项目及其 Pinboard 归属。"])
        case "list_pinboards":
            return try result(["pinboards": store.pinboards.sorted { $0.sortOrder < $1.sortOrder }.map(boardSummary)])
        case "create_pinboard":
            let name = try nonempty(args["name"] as? String, name: "name", trim: true)
            return try result(boardSummary(store.createPinboard(name: name, colorHex: "#F4B84A")))
        case "rename_pinboard":
            let id = try uuid(args, "id"); _ = try pinboard(id)
            try store.renamePinboard(id: id, name: nonempty(args["name"] as? String, name: "name", trim: true))
            return try result(boardSummary(pinboard(id)))
        case "delete_pinboard":
            let id = try uuid(args, "id"), value = try pinboard(id), confirmed = args["confirm"] as? Bool ?? false
            let before = boardSummary(value)
            if confirmed { try store.removePinboard(id: id) }
            return try result(["deleted": confirmed, "pinboard": before, "message": confirmed ? "Pinboard 已删除，历史项目保留。" : "预览：confirm=true 后删除 Pinboard。"])
        case "add_item_to_pinboard", "remove_item_from_pinboard":
            let id = try uuid(args, "item_id"), boardID = try uuid(args, "pinboard_id")
            _ = try item(id); _ = try pinboard(boardID)
            if name == "add_item_to_pinboard" { try store.assign(ids: [id], to: boardID) }
            else { try store.unassign(ids: [id], from: boardID) }
            return try result(boardSummary(pinboard(boardID)))
        case "replica_restore_item":
            let id = try uuid(args, "item_id"); _ = try item(id, includeDeleted: true)
            try store.restore(ids: [id]); return try result(summary(item(id)))
        case "replica_copy_item":
            let id = try uuid(args, "item_id"); _ = try item(id)
            let name = try nonempty(args["pasteboard_name"] as? String, name: "pasteboard_name", trim: true)
            let isGeneral = name == "general" || name == NSPasteboard.Name.general.rawValue
            guard !isGeneral || args["allow_system_clipboard"] as? Bool == true else { throw invalid("General clipboard requires allow_system_clipboard=true") }
            let pasteboard = isGeneral ? NSPasteboard.general : NSPasteboard(name: NSPasteboard.Name(name))
            try store.writeToPasteboard(id: id, pasteboard: pasteboard, plainTextOnly: args["plain_text_only"] as? Bool ?? false)
            return try result(["copied": true, "pasteboard": name, "system_clipboard_changed": isGeneral])
        default: throw invalid("Unknown tool")
        }
    }
}

@main
private struct PastoMCP {
    @MainActor
    static func main() {
        signal(SIGPIPE, SIG_IGN)
        do {
            let args = Array(CommandLine.arguments.dropFirst())
            if args == ["--help"] {
                FileHandle.standardError.write(Data("pasto-mcp [--data-dir PATH]\n隔离 stdio MCP；不监控系统剪贴板。\n".utf8))
                return
            }
            let directory: URL
            if args.isEmpty { directory = ClipboardStore.defaultDirectoryURL }
            else if args.count == 2 && args[0] == "--data-dir" { directory = URL(fileURLWithPath: args[1], isDirectory: true) }
            else { throw invalid("Usage: pasto-mcp [--data-dir PATH]") }
            let server = try Server(directory: directory)
            var buffer = Data(), droppingOversizedFrame = false
            let maximum = 1024 * 1024
            var chunk = [UInt8](repeating: 0, count: 65536)
            while true {
                let count = Darwin.read(STDIN_FILENO, &chunk, chunk.count)
                if count == 0 { break }
                if count < 0 {
                    if errno == EINTR { continue }
                    throw POSIXError(POSIXErrorCode(rawValue: errno) ?? .EIO)
                }
                for byte in chunk.prefix(count) {
                    if byte == 0x0A {
                        if droppingOversizedFrame { server.sendError(code: -32600, message: "Request exceeds 1 MiB") }
                        else { server.receive(buffer) }
                        buffer.removeAll(keepingCapacity: true); droppingOversizedFrame = false
                    } else if !droppingOversizedFrame {
                        buffer.append(byte)
                        if buffer.count > maximum { buffer.removeAll(keepingCapacity: true); droppingOversizedFrame = true }
                    }
                }
            }
            if droppingOversizedFrame { server.sendError(code: -32600, message: "Request exceeds 1 MiB") }
            else if !buffer.isEmpty { server.receive(buffer) }
        } catch {
            FileHandle.standardError.write(Data("pasto-mcp: \(error.localizedDescription)\n".utf8))
            exit(1)
        }
    }
}
