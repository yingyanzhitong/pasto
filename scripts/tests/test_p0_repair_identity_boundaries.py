import hashlib
import plistlib
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
STORE = ROOT / "replica/Sources/PastoCore/ClipboardStore.swift"
PERSISTENCE = ROOT / "replica/Sources/PastoCore/ClipboardPersistence.swift"
INDEX = ROOT / "replica/Sources/Pasto/UI/ReplicaSearchIndex.swift"
ORIGINAL_MODEL = Path(
    "/Applications/Paste.app/Contents/Resources/PastePackages_PasteCore.bundle/Contents/Resources/"
    "v5Paste.momd/v10.mom"
)
ORIGINAL_MODEL_SHA256 = "25ee25cb8d2e5745c2d258e278ea5a64c72e1f1124f07392dcfdc21e39febc95"


def method_body(source: str, signature: str) -> str:
    if 'private let snapshotReader:' in source and signature.startswith(('func searchItems(', 'func searchNativeItems(')):
        from snapshot_read_scope_contract import body
        return body(source, signature)[1:-1]

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


class IdentityBoundarySourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = STORE.read_text()
        cls.persistence = PERSISTENCE.read_text()
        cls.index = INDEX.read_text()

    def test_original_v10_model_hash_binds_item_identifier_uniqueness(self):
        data = ORIGINAL_MODEL.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), ORIGINAL_MODEL_SHA256)
        objects = plistlib.loads(data)["$objects"]
        item_entity = objects[37]
        self.assertEqual(objects[item_entity["NSEntityName"].data], "ItemEntity")
        unique_tuple_container = objects[item_entity["NSUniqueTuples"].data]
        tuple_ref = unique_tuple_container["NS.objects"][0]
        identifier_ref = objects[tuple_ref.data]["NS.objects"][0]
        self.assertEqual(objects[identifier_ref.data], "identifier")

    def test_validate_uniquifies_effective_sdk_ids_but_allows_one_empty_string(self):
        body = method_body(self.store, "private func validate(_ state: StoreState) throws")
        self.assertIn("let effectiveItemIdentifiers = state.items.map { $0.nativeIdentifier ?? $0.id.uuidString }", body)
        self.assertIn("Set(effectiveItemIdentifiers).count == effectiveItemIdentifiers.count", body)
        self.assertIn("throw ClipboardStoreError.duplicateIdentifiers", body)
        # Empty remains a legal single native value; a second one collides in this same set.
        self.assertNotIn("nativeIdentifier?.isEmpty", body)

    def test_local_key_and_native_identity_lookups_are_separate(self):
        local = method_body(self.persistence, "func searchItems(identifiers: [String]?) throws -> [ClipboardItem]")
        self.assertIn('NSPredicate(format: "key IN %@", identifiers)', local)
        self.assertNotIn("nativeIdentifier", local)
        native = method_body(self.persistence, "func searchNativeItems(identifiers: [String]?) throws -> [ClipboardItem]")
        self.assertIn(
            'nativeIdentifier IN %@ OR (nativeIdentifier == nil AND key IN %@)',
            native,
        )
        self.assertIn("identifiers, identifiers", native)
        self.assertIn("func searchNativeItems(identifiers: [String]?) throws -> [ClipboardItem]", self.store)
        store_native = method_body(self.store, "public func searchNativeItems(identifiers: [String]?) throws -> [ClipboardItem]")
        self.assertIn("persistence.searchNativeItems(identifiers: identifiers)", store_native)

    def test_sdk_query_and_history_reindex_use_native_namespace_facade(self):
        query = method_body(self.index, "private func replaceQuery(with nodes: [OriginalSearchQueryNode])")
        self.assertIn("installResultSource(store.makeSearchCollection(identifiers: found))", query)
        live = method_body(self.index, "private func liveEntries(identifiers: [String]?) throws -> [Entry]")
        self.assertIn("store.searchIndexRecords(identifiers: identifiers)", live)
        self.assertNotIn("store.searchItems(identifiers:", self.index)

    def test_targeted_reindex_deletes_replaced_sdk_alias_before_indexing(self):
        body = method_body(self.index, "private func reindexTargets(_ identifiers: [String]) async throws")
        get_previous = body.index("indexed[entry.id]")
        delete = body.index("deleteIdentifiers(replacedIdentifiers)")
        write = body.index("Self.writeSearchableItems(changed, index: resolveWriteIndex())")
        cache = body.index("for entry in refreshed { indexed[entry.id] = entry }")
        self.assertLess(get_previous, delete)
        self.assertLess(delete, write)
        self.assertLess(write, cache)
        self.assertIn("previous.searchIdentifier != entry.searchIdentifier", body)
        self.assertIn("return previous.searchIdentifier", body)

    def test_ordered_delete_reads_dynamic_context_inside_mutation(self):
        facade = method_body(self.store, "public func delete(orderedIDs: [UUID], contextPinboardID: UUID?) throws")
        self.assertIn("delete(orderedIDs: orderedIDs, currentPinboardID: { contextPinboardID })", facade)
        body = method_body(self.store, "public func delete(orderedIDs: [UUID], currentPinboardID: () -> UUID?) throws")
        mutate = body.index("try mutate(deletingItemIDs: orderedIDs, refreshHistoryAfterChange: { refreshHistory }) { state in")
        read_context = body.index("let contextPinboardID = currentPinboardID()")
        self.assertLess(mutate, read_context)
        self.assertIn("let ids = Set(orderedIDs)", body)
        self.assertIn("ids.contains(state.items[i].id)", body)
        self.assertIn("deletingItemIDs: orderedIDs", body)


if __name__ == "__main__":
    unittest.main()
