"""Static source checks for the ordered Core Data deletion channel."""
import hashlib
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
ORIGINAL_PATH = ROOT / "decompiled/Paste/part-0275.c"
ORIGINAL_SHA256 = "6e2c2ddea2e00763d43bd1614935a0eafc96b10527c579e86f22d9e1b3988da0"
STORE = ROOT / "replica/Sources/PastoCore/ClipboardStore.swift"
PERSISTENCE = ROOT / "replica/Sources/PastoCore/ClipboardPersistence.swift"


def swift_body(source: str, signature: str) -> str:
    if source.count(signature) != 1:
        raise AssertionError(f"Expected one declaration: {signature}")
    start = source.index("{", source.index(signature) + len(signature))
    token = r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*[\s\S]*?\*/'
    masked = re.sub(token, lambda match: " " * len(match.group()), source)
    depth = 0
    for index in range(start, len(masked)):
        depth += (masked[index] == "{") - (masked[index] == "}")
        if depth == 0:
            return source[start:index + 1]
    raise AssertionError(f"Unclosed Swift body: {signature}")


def original_fragment(path: Path, address: str) -> str:
    source = path.read_text()
    headers = list(re.finditer(r"^/\* Address: (0x[0-9a-f]+) \| .*? \*/$", source, re.M))
    for index, match in enumerate(headers):
        if match.group(1) == address:
            end = headers[index + 1].start() if index + 1 < len(headers) else len(source)
            return source[match.start():end].rstrip() + "\n"
    raise AssertionError(f"Original function not found: {path} {address}")


class OrderedDeleteCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = STORE.read_text()
        cls.persistence = PERSISTENCE.read_text()

    def test_original_per_object_delete_fragment_is_bound(self):
        fragment = original_fragment(ORIGINAL_PATH, "0x1003646ec")
        self.assertEqual(hashlib.sha256(fragment.encode()).hexdigest(), ORIGINAL_SHA256)
        self.assertIn("managedObjectContext", fragment)
        self.assertIn("delete", fragment)

    def test_ordered_store_api_preserves_array_and_defers_context_read(self):
        facade = swift_body(self.store, "public func delete(orderedIDs: [UUID], contextPinboardID: UUID?) throws")
        self.assertIn("delete(orderedIDs: orderedIDs, currentPinboardID: { contextPinboardID })", facade)
        body = swift_body(self.store, "public func delete(orderedIDs: [UUID], currentPinboardID: () -> UUID?) throws")
        mutation = body.index("try mutate(deletingItemIDs: orderedIDs, refreshHistoryAfterChange: { refreshHistory }) { state in")
        read = body.index("let contextPinboardID = currentPinboardID()")
        membership = body.index("let ids = Set(orderedIDs)")
        self.assertLess(mutation, read)
        self.assertLess(membership, mutation)
        self.assertIn("ids.contains(state.items[i].id)", body)
        self.assertIn("state.items.removeAll", body)

    def test_context_delete_forwards_full_order_without_item_snapshot_filter(self):
        body = swift_body(self.store, "public func delete(orderedIDs: [UUID], currentPinboardID: () -> UUID?) throws")
        self.assertIn("mutate(deletingItemIDs: orderedIDs, refreshHistoryAfterChange: { refreshHistory })", body)
        self.assertNotIn("items.filter", body)
        self.assertNotIn("Set(orderedIDs).sorted", body)

    def test_set_wrappers_remain_available_and_forward_deterministically(self):
        wrapper = swift_body(self.store, "public func delete(ids: Set<UUID>, contextPinboardID: UUID?) throws")
        self.assertIn("ids.sorted { $0.uuidString < $1.uuidString }", wrapper)
        self.assertIn("delete(orderedIDs:", wrapper)
        permanent = swift_body(self.store, "public func permanentlyDelete(ids: Set<UUID>) throws")
        self.assertIn("orderedIDs: ids.sorted { $0.uuidString < $1.uuidString }", permanent)

    def test_commit_maps_ordered_ids_to_ordered_core_data_keys(self):
        commit = swift_body(self.persistence, "func commit<T>(previous: StoreState?, deletingItemIDs: [UUID] = [],")
        self.assertIn("deletingKeys: deletingItemIDs.map(\\.uuidString)", commit)
        update_call = commit.index('entity: "Item"')
        key_map = commit.index("deletingKeys: deletingItemIDs.map(\\.uuidString)")
        self.assertLess(update_call, key_map)

    def test_persistence_preserves_explicit_order_and_duplicates_then_deletes_each_object(self):
        update = swift_body(self.persistence, "func update<T: Equatable>(_ values: [T], previous: [T], entity: String,")
        self.assertIn("var orderedRemoved = deletingKeys.filter { removed.contains($0) }", update)
        self.assertIn("let scheduled = Set(orderedRemoved)", update)
        self.assertIn("orderedRemoved += previous.map(key).filter { removed.contains($0) && !scheduled.contains($0) }", update)
        self.assertLess(update.index("fetchObjects(entity, keys: keys)"), update.index("for id in orderedRemoved"))
        loop = update.index("for id in orderedRemoved")
        deletion = update.index("object.managedObjectContext?.delete(object)")
        apply = update.index("for value in changed")
        self.assertLess(loop, deletion)
        self.assertLess(deletion, apply)

    def test_missing_objects_nil_context_and_empty_update_are_noops(self):
        update = swift_body(self.persistence, "func update<T: Equatable>(_ values: [T], previous: [T], entity: String,")
        self.assertIn("guard !keys.isEmpty else { return }", update)
        self.assertIn("if let object = objects[id]", update)
        self.assertIn("object.managedObjectContext?.delete(object)", update)
        self.assertIn("let removed = Set(before.keys).subtracting(after.keys)", update)
        self.assertIn("deletingKeys.filter { removed.contains($0) }", update)


if __name__ == "__main__":
    unittest.main()
