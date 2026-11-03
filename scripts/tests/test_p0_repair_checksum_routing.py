import hashlib
import re
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
PASTEBOARD = ROOT / "replica/Sources/PastoCore/Pasteboard.swift"
CHECKSUMS = ROOT / "replica/Sources/PastoCore/OriginalPasteboardChecksums.swift"
STORE = ROOT / "replica/Sources/PastoCore/ClipboardStore.swift"
ORIGINAL = ROOT / "decompiled/Paste/part-0258.c"
RESULT = ROOT / ".local/p0-repair/phase-1/checksum-result.json"
EXPECTED_ORIGINAL_HASHES = {
    "1003214c8": "79fda1ac5cab85a2e23684ad440ba4d2e6bd3ba2a429b9bc7359041c2f511cd7",
    "1003216bc": "ba0fcc0a1800199881dd1af0f5adaa30b4fe5243fed61e1635490c061affe4e3",
    "100322ae4": "847a4714d2837febc019403a8a0d67c5d2bb1188864c82ce67640f6191eafd96",
}


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


def original_fragment(source: str, address: str) -> str:
    match = re.search(r"/\* Address: 0x" + re.escape(address) + r" \|.*?\*/", source)
    if not match:
        raise AssertionError(f"missing original address {address}")
    next_match = re.search(r"/\* Address: 0x", source[match.end():])
    end = match.end() + next_match.start() if next_match else len(source)
    return source[match.start():end].rstrip() + "\n"


class ChecksumRoutingSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pasteboard = PASTEBOARD.read_text()
        cls.checksums = CHECKSUMS.read_text()
        cls.store = STORE.read_text()
        cls.original = ORIGINAL.read_text()

    def test_original_function_hashes_are_bound(self):
        for address, expected in EXPECTED_ORIGINAL_HASHES.items():
            fragment = original_fragment(self.original, address)
            self.assertEqual(hashlib.sha256(fragment.encode()).hexdigest(), expected, address)

    def test_known_checksum_routes_every_decoded_kind_to_original_selector(self):
        body = method_body(self.pasteboard, "public nonisolated static func knownPasteboardChecksum(from payloads: [String: Data]) throws -> String?")
        self.assertIn("let items = try originalPasteboardItems(from: payloads)", body)
        self.assertIn("let kind = OriginalPasteboardClassification.f_10032362c(items)", body)
        self.assertIn("return OriginalPasteboardChecksums.f_1003216bc(items, kind: kind)", body)
        self.assertNotIn("kind != .unknown", body)
        self.assertNotIn("kind == .files", body)

    def test_archive_fallback_hashes_empty_data_on_archive_failure(self):
        body = method_body(self.checksums, "public static func f_100322ae4(_ items: [OriginalPasteboardItem]) -> String")
        self.assertIn("NSKeyedArchiver.archivedData(withRootObject: items as NSArray", body)
        self.assertIn("?? Data()", body)
        self.assertIn("return checksum(data)", body)
        selector = method_body(self.checksums, "public static func f_1003216bc(_ items: [OriginalPasteboardItem],")
        self.assertIn("case .unknown:\n            return f_100322ae4(items)", selector)
        self.assertIn("guard !paths.isEmpty else { return f_100322ae4(items) }", selector)

    def test_dedup_consumes_checksum_and_keeps_nil_fallback(self):
        body = method_body(self.store, "func addWithInsertionResult(_ item: ClipboardItem,")
        self.assertIn("checksum = try Self.knownPasteboardChecksum(from: item.payloads)", body)
        self.assertIn("checksum = try? Self.knownPasteboardChecksum(from: item.payloads)", body)
        self.assertIn("let previousChecksum = try? Self.knownPasteboardChecksum(from: previous.payloads)", body)
        self.assertIn("if let previousChecksum { return checksum == previousChecksum }", body)
        self.assertIn("return checksum == previousChecksum", body)
        self.assertIn("let explicitIdentity = Self.hasValidExplicitPasteboardRepresentations(previous.payloads)", body)
        self.assertIn("&& Self.hasSamePasteboardRepresentations(previous.payloads, item.payloads)", body)


if __name__ == "__main__":
    unittest.main()
