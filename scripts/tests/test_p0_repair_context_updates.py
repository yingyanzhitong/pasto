"""Static checks for Core Data changed-item ID publication; no Core Data runtime."""
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from macho_imports import _chained_bindings
from test_offline_p0_contracts import body

SOURCE = "replica/Sources/PastoCore/ClipboardPersistence.swift"
RESULT = ".local/p0-repair/phase-6/context-updates-result.json"
PROOF = ".local/p0-repair/phase-6/changed-id-observer-proof.json"
BINARY = ".local/paste-arm64-static.bin"


def original_fragment(path: Path, address: str) -> str:
    source = path.read_text()
    headers = list(re.finditer(r"^/\* Address: (0x[0-9a-f]+) \| .*? \*/$", source, re.M))
    for index, match in enumerate(headers):
        if match.group(1) == address:
            end = headers[index + 1].start() if index + 1 < len(headers) else len(source)
            return source[match.start():end].rstrip() + "\n"
    raise AssertionError(f"Original function not found: {path} {address}")


def chained_bindings(data: bytes):
    cursor = 32
    segments, dylibs, chained = [], [], None
    command_count = struct.unpack_from("<I", data, 16)[0]
    for _ in range(command_count):
        command, size = struct.unpack_from("<II", data, cursor)
        if command == 0x19:
            address, memory_size, offset, file_size = struct.unpack_from("<QQQQ", data, cursor + 24)
            segments.append(dict(address=address, memory_size=memory_size, offset=offset, file_size=file_size))
        elif command in (0xC, 0x80000018, 0x8000001F, 0x20, 0x80000023):
            name_offset = struct.unpack_from("<I", data, cursor + 8)[0]
            end = data.index(b"\0", cursor + name_offset, cursor + size)
            dylibs.append(dict(install_name=data[cursor + name_offset:end].decode()))
        elif command == 0x80000034:
            chained = struct.unpack_from("<II", data, cursor + 8)
        cursor += size
    return _chained_bindings(data, chained, segments, dylibs)[0]


class ContextUpdatesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_path = ROOT / SOURCE
        cls.source = cls.source_path.read_text()
        cls.result = json.loads((ROOT / RESULT).read_text())
        cls.proof = json.loads((ROOT / PROOF).read_text())

    def test_original_fragment_hash_and_key_slots_are_bound_to_real_imports(self):
        for ref in self.result["original_evidence"]["supporting_original_fragments"]:
            fragment = original_fragment(ROOT / ref["path"], ref["address"])
            self.assertEqual(hashlib.sha256(fragment.encode()).hexdigest(), ref["sha256"])

        data = (ROOT / BINARY).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), self.proof["original_binary"]["sha256_arm64"])
        bindings = chained_bindings(data)
        for address, symbol in ((0x100EA9A38, "_NSUpdatedObjectsKey"),
                                (0x100EA9A30, "_NSRefreshedObjectsKey")):
            self.assertEqual(bindings[address]["symbol"], symbol)
        self.assertEqual(self.proof["notification_userinfo_keys"]["count"], 2)

    def test_publisher_is_context_scoped_and_reads_only_confirmed_keys(self):
        self.assertIn("import Combine", self.source)
        self.assertIn("private let itemUpdatesSubject = PassthroughSubject<Set<UUID>, Never>()", self.source)
        self.assertIn("private var contextChangesObservation: AnyCancellable?", self.source)
        self.assertIn("var collectionItemUpdates: AnyPublisher<Set<UUID>, Never>", self.source)
        self.assertIn(".publisher(for: .NSManagedObjectContextObjectsDidChange, object: managedContext)", self.source)
        self.assertIn(".sink { [weak self] notification in", self.source)
        self.assertIn("MainActor.assumeIsolated {", self.source)
        self.assertIn("notification.userInfo?[NSUpdatedObjectsKey]", self.source)
        self.assertIn("notification.userInfo?[NSRefreshedObjectsKey]", self.source)
        for forbidden in ("NSInsertedObjectsKey", "NSDeletedObjectsKey", "NSInvalidatedObjectsKey"):
            self.assertNotIn(forbidden, self.source)
        self.assertEqual(self.source.count(".publisher(for: .NSManagedObjectContextObjectsDidChange"), 1)

    def test_only_item_uuid_keys_are_sent_and_empty_sets_are_suppressed(self):
        self.assertIn('guard object.entity.name == "Item",', self.source)
        self.assertIn('let key = object.value(forKey: "key") as? String else { return nil }', self.source)
        self.assertIn("return UUID(uuidString: key)", self.source)
        self.assertIn("guard !identifiers.isEmpty else { return }", self.source)
        self.assertIn("itemUpdatesSubject.send(identifiers)", self.source)
        start = self.source.index("private func publishChangedItemIDs")
        end = self.source.index("\n    }", start) + len("\n    }")
        self.assertNotIn("nativeIdentifier", self.source[start:end])
        self.assertNotIn("deinit", self.source)

    def test_frozen_result_hashes_and_unchanged_live_observer_document_scope(self):
        before = ROOT / ".local/p0-repair/phase-12/before"
        self.assertEqual(hashlib.sha256((before / SOURCE).read_bytes()).hexdigest(),
                         self.result["current_source"]["sha256"])
        signature = "private func publishChangedItemIDs(from notification: Notification)"
        self.assertEqual(body(self.source, signature), body((before / SOURCE).read_text(), signature))
        for ref in self.result["current_source"]["current_references"]:
            self.assertEqual(ref["path"], SOURCE)
            self.assertIn(ref["symbol"], self.source)
        test_path = before / "scripts/tests/test_p0_repair_context_updates.py"
        self.assertEqual(hashlib.sha256(test_path.read_bytes()).hexdigest(),
                         self.result["static_test"]["sha256"])
        self.assertFalse(self.result["scope"]["swift_compiled"])
        self.assertFalse(self.result["scope"]["coredata_runtime_executed"])


if __name__ == "__main__":
    unittest.main()
