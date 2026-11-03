from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "replica/Sources/PastoCore/OriginalPasteboard.swift"


def method_body(source: str, signature: str) -> str:
    start = source.index(signature)
    opening = source.index("{", start)
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[opening + 1:index]
    raise AssertionError(f"unterminated method: {signature}")


class ArchiveKeySourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text()

    def test_secure_archive_encoder_uses_original_keys(self):
        body = method_body(self.source, "public func f_10037f520(with coder: NSCoder)")
        self.assertRegex(body, r'coder\.encode\(orderedTypes as NSArray,\s*forKey: "types"\)')
        self.assertRegex(body, r'coder\.encode\(dataByType as NSDictionary,\s*forKey: "data"\)')
        self.assertNotIn('forKey: "dataByType"', body)

    def test_decoder_falls_back_only_when_original_data_key_is_absent(self):
        body = method_body(self.source, "public required init?(coder: NSCoder)")
        self.assertIn('if coder.containsValue(forKey: "data")', body)
        data_branch = body.split('if coder.containsValue(forKey: "data")', 1)[1].split("} else {", 1)[0]
        legacy_branch = body.split("} else {", 1)[1]
        self.assertIn('forKey: "data"', data_branch)
        self.assertNotIn('forKey: "dataByType"', data_branch)
        self.assertIn('forKey: "dataByType"', legacy_branch)

    def test_codable_property_list_and_json_keys_are_unchanged(self):
        self.assertIn("private enum CodingKeys: String, CodingKey { case types, dataByType }", self.source)
        encode_body = method_body(self.source, "public func f_10037df78(to encoder: Encoder)")
        self.assertRegex(encode_body, r'container\.encode\(orderedTypes,\s*forKey: \.types\)')
        self.assertRegex(encode_body, r'container\.encode\(dataByType,\s*forKey: \.dataByType\)')
        decode_body = method_body(self.source, "public required init(from decoder: Decoder)")
        self.assertIn("forKey: .types", decode_body)
        self.assertIn("forKey: .dataByType", decode_body)

    def test_archive_decode_remains_connected_to_item_import(self):
        archive = (ROOT / "replica/Sources/PastoCore/OriginalPasteboardArchive.swift").read_text()
        pasteboard = (ROOT / "replica/Sources/PastoCore/Pasteboard.swift").read_text()
        self.assertIn("decoder.setClass(OriginalPasteboardItem.self, forClassName: \"PasteCore.PasteboardItem\")", archive)
        self.assertIn("decoder.setClass(OriginalPasteboardItem.self, forClassName: \"_TtC9PasteCore14PasteboardItem\")", archive)
        self.assertIn("let snapshot = try OriginalPasteboardArchive.decodeItems(data)", pasteboard)


if __name__ == "__main__":
    unittest.main()
