import Foundation

public enum OriginalSearchInputContext {
    public struct Context: Equatable, Sendable {
        public let nodes: [OriginalSearchQueryNode]
        public let nodeIndex: Int
        public let text: String
        public let anchorRange: NSRange
    }

    public static func f_1002f78f8(_ nodes: [OriginalSearchQueryNode], caret: Int) -> Context? {
        var offset = 0
        for (index, node) in nodes.enumerated() {
            let text: String
            let length: Int
            switch node {
            case let .text(value):
                text = value
                length = (value as NSString).length
            case let .filter(tag, value):
                let prefix: String
                switch tag {
                case 0: prefix = "app"
                case 1: prefix = "type"
                case 2: prefix = "title"
                case 3: prefix = "date"
                case 4: prefix = "device"
                default: prefix = "pinboard"
                }
                text = prefix + ":" + value
                length = 1
            }
            let context = Context(nodes: nodes, nodeIndex: index, text: text,
                                  anchorRange: NSRange(location: offset, length: length))
            if caret >= offset, caret - offset < length { return context }
            offset += length
            if offset == caret { return context }
        }
        return nil
    }
}
