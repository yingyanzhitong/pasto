from native_title_scope_contract import pre_native_title
import hashlib
import re
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
ORIGINALS = {
    "100360d9c": (ROOT / "decompiled/Paste/part-0275.c", "ad0fc43d41bfc0f6ae5dedf2732a5b6fcf1894285cc88e8c651b6cb53dfdda88"),
    "1003611b0": (ROOT / "decompiled/Paste/part-0275.c", "b90d0c344d03be5287711e30be2411b4617b18909e0b31f4e937d0b6a60a676e"),
    "10036fa2c": (ROOT / "decompiled/Paste/part-0279.c", "e201ab914f62ce9a76997d5cd8cc54a20c84d0d355efc6807d624894b8a445c5"),
    "10037063c": (ROOT / "decompiled/Paste/part-0279.c", "c2a4e13499be2d15e88f799556453cb2d9afe3ed3267f52e9b90dae4e62d3223"),
}
MODELS = ROOT / "replica/Sources/PastoCore/Models.swift"
STORE = ROOT / "replica/Sources/PastoCore/ClipboardStore.swift"
PERSISTENCE = ROOT / "replica/Sources/PastoCore/ClipboardPersistence.swift"
HISTORY = ROOT / "replica/Sources/PastoCore/OriginalSearchHistory.swift"
INDEX = ROOT / "replica/Sources/Pasto/UI/ReplicaSearchIndex.swift"
MIGRATION = ROOT / "replica/Sources/PastoCore/PasteGroupMigration.swift"
LEGACY_SHIPPED = ROOT / ".local/phase2/legacy-shipped-persistence.swift"


def source_fragment(path: Path, address: str) -> str:
    source = path.read_text()
    match = re.search(r"/\* Address: 0x" + re.escape(address) + r" \|.*?\*/", source)
    if not match:
        raise AssertionError(f"missing original function {address}")
    following = re.search(r"/\* Address: 0x", source[match.end():])
    end = match.end() + following.start() if following else len(source)
    return source[match.start():end].rstrip() + "\n"


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


class NativeIdentitySourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.models = MODELS.read_text()
        cls.store = pre_native_title(STORE.read_text())
        cls.persistence = pre_native_title(PERSISTENCE.read_text())
        cls.history = HISTORY.read_text()
        cls.index = INDEX.read_text()
        cls.migration = MIGRATION.read_text()

    def test_original_creation_history_and_identifier_fragments_are_bound(self):
        for address, (path, expected) in ORIGINALS.items():
            actual = hashlib.sha256(source_fragment(path, address).encode()).hexdigest()
            self.assertEqual(actual, expected, address)

    def test_model_keeps_local_uuid_and_adds_optional_native_strings(self):
        item = method_body(self.models, "public struct ClipboardItem: Identifiable, Codable, Equatable, Sendable")
        self.assertIn("public var id: UUID", item)
        self.assertIn("public var nativeIdentifier: String?", item)
        self.assertIn("public var nativeChecksum: String?", item)
        self.assertIn("public var sourceIdentifier: String?", item)
        self.assertIn("id: UUID = UUID(), nativeIdentifier: String? = nil, nativeChecksum: String? = nil,", item)
        self.assertIn("sourceIdentifier: String? = nil,", item)
        self.assertNotIn("init(from decoder: Decoder)", item)

    def test_capture_defaults_identifier_to_checksum_and_reuses_local_id_on_hit(self):
        body = method_body(self.store, "func addWithInsertionResult(_ item: ClipboardItem,")
        self.assertIn("if recordCapture", body)
        self.assertIn("checksum = try Self.knownPasteboardChecksum(from: item.payloads)", body)
        self.assertIn("guard item.nativeIdentifier != nil || checksum != nil", body)
        self.assertIn("throw OriginalPasteboardItemCreationError.unsupportedContent", body)
        self.assertIn("if item.nativeIdentifier == nil { item.nativeIdentifier = checksum }", body)
        self.assertIn("item.nativeChecksum = checksum", body)
        self.assertIn("let previousChecksum = try? Self.knownPasteboardChecksum(from: previous.payloads)", body)
        lookup = method_body(body, 'if let i = state.items.firstIndex(where:')
        capture = method_body(lookup, 'if recordCapture')
        self.assertIn('guard let checksum else { return false }', capture)
        self.assertIn('return previous.nativeChecksum == checksum', capture)
        self.assertNotIn('knownPasteboardChecksum', capture)
        self.assertNotIn("previous.nativeIdentifier == checksum", body)
        self.assertNotIn("previous.nativeIdentifier == identifier", body)
        self.assertIn("if state.items[i].nativeIdentifier == nil { state.items[i].nativeIdentifier = state.items[i].id.uuidString }", body)
        self.assertIn("return (state.items[result.index].id, result.isNew)", body)

    def test_imported_identity_metadata_does_not_override_payload_dedup(self):
        body = method_body(self.store, "func addWithInsertionResult(_ item: ClipboardItem,")
        self.assertIn("checksum = try? Self.knownPasteboardChecksum(from: item.payloads)", body)
        self.assertNotIn("} else if let stored = item.nativeChecksum {", body)
        intent = method_body(self.store, "public func createIntentText(_ content: String, destination: IntentTextDestination)")
        self.assertIn("let previousChecksum = try? Self.knownPasteboardChecksum(from: previous.payloads)", intent)
        self.assertNotIn("previous.nativeChecksum", intent)
        self.assertNotIn("previous.nativeIdentifier == checksum", intent)

    def test_duplicate_and_content_edits_keep_identity_consistent(self):
        duplicate = method_body(self.store, "public func duplicateItem(id: UUID) throws -> UUID")
        self.assertIn("item.id = UUID()", duplicate)
        self.assertIn("item.nativeIdentifier = item.id.uuidString", duplicate)
        self.assertNotIn("nativeChecksum = nil", duplicate)
        self.assertIn("private static func refreshNativeChecksum(_ item: inout ClipboardItem)", self.store)
        for signature in [
            "public func updateItem(id: UUID, title: String? = nil, text: String? = nil)",
            "public func updateTextPreviewItem(id: UUID, attributedString: NSAttributedString)",
            "public func updateRichTextItem(id: UUID, attributedString: NSAttributedString)",
            "private func updateImageItem(id: UUID, payloads: [String: Data], allowingEmptyRepresentation: Bool)",
            "public func updateLinkItem(id: UUID, url: URL)",
            "public func updateColorItem(id: UUID, text: String)",
        ]:
            self.assertIn("refreshNativeChecksum", method_body(self.store, signature), signature)

    def test_core_data_migrates_optional_native_fields_without_replacing_uuid_key(self):
        self.assertIn('attribute("nativeIdentifier", .stringAttributeType, optional: true)', self.persistence)
        self.assertIn('attribute("nativeChecksum", .stringAttributeType, optional: true)', self.persistence)
        self.assertIn('attributes.first(where: { $0.name == "nativeIdentifier" })?.preservesValueInHistoryOnDeletion = true', self.persistence)
        commit = method_body(self.persistence, "func commit<T>(previous: StoreState?, deletingItemIDs: [UUID] = [],")
        self.assertIn('key: { $0.id.uuidString }', commit)
        self.assertIn('object.setValue(item.nativeIdentifier, forKey: "nativeIdentifier")', commit)
        self.assertIn('object.setValue(item.nativeChecksum, forKey: "nativeChecksum")', commit)
        self.assertIn('deletingKeys: deletingItemIDs.map(\\.uuidString)', commit)
        self.assertIn('NSMigratePersistentStoresAutomaticallyOption: true', self.persistence)
        self.assertIn('NSInferMappingModelAutomaticallyOption: true', self.persistence)

    def test_legacy_store_migration_is_explicit_and_source_preserving(self):
        init = method_body(self.persistence, "init(directoryURL: URL) throws")
        self.assertLess(init.index("migrateLegacyStoreIfNeeded"), init.index("addPersistentStore"))
        factory = method_body(self.persistence, "private static func makeModel(includeNativeIdentity: Bool,")
        self.assertIn('attribute("timestamp", .dateAttributeType, optional: includeOptionalTimestamp)', factory)
        self.assertIn('attribute("localCreatedAt", .dateAttributeType, optional: true)', factory)
        self.assertIn("if includeNativeIdentity", factory)
        self.assertIn('attribute("nativeIdentifier", .stringAttributeType, optional: true)', factory)
        self.assertIn('attribute("nativeChecksum", .stringAttributeType, optional: true)', factory)
        self.assertIn("itemAttributes.append(contentsOf: [attribute(\"updatedAt\", .dateAttributeType), attribute(\"inHistory\", .booleanAttributeType)])", factory)
        self.assertIn('entity("Pinboard", [attribute("content", .binaryDataAttributeType)])', factory)
        migration = method_body(self.persistence, "private static func migrateLegacyStoreIfNeeded(at storeURL: URL,")
        self.assertIn("metadataForPersistentStore", migration)
        self.assertIn("destinationModel.isConfiguration(nil, compatibleWithStoreMetadata: metadata)", migration)
        self.assertIn("makeModel(includeNativeIdentity: false, preserveItemKeyInHistory: true, includeLists: false, includeOptionalTimestamp: false, includeNativeItemData: false, includeNativeSources: false, includeTypedItem: false, includeItemOrder: false)", migration)
        self.assertIn("$0.isConfiguration(nil, compatibleWithStoreMetadata: metadata)", migration)
        self.assertIn("inferredMappingModel", migration)
        self.assertIn("defer { try? FileManager.default.removeItem(at: temporaryDirectory) }", migration)
        self.assertLess(migration.index("try manager.migrateStore"), migration.index("try coordinator.replacePersistentStore"))
        self.assertIn("metadataForPersistentStore(\n            type: .sqlite", migration)
        self.assertIn("let mapping = try NSMappingModel.inferredMappingModel(", migration)
        self.assertNotIn("guard let mapping", migration)
        self.assertIn("migrateStore(from: storeURL, type: .sqlite", migration)
        self.assertIn("withPersistentStoreFrom: migratedURL, sourceOptions: storeOptions, type: .sqlite", migration)
        self.assertNotIn("removeItem(at: storeURL)", migration)
        self.assertNotIn("destroyPersistentStore(at: storeURL", migration)

    def test_both_exact_legacy_model_variants_are_candidates(self):
        factory = method_body(self.persistence, "private static func makeModel(includeNativeIdentity: Bool,")
        self.assertIn("preserveItemKeyInHistory: Bool", self.persistence)
        self.assertIn("if name == \"Item\", preserveItemKeyInHistory", factory)
        migration = method_body(self.persistence, "private static func migrateLegacyStoreIfNeeded(at storeURL: URL,")
        self.assertIn("makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, includeLists: true, includeOptionalTimestamp: false, includeNativeItemData: false, includeNativeSources: false, includeTypedItem: false, includeItemOrder: false)", migration)
        self.assertIn("makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, includeLists: false, includeOptionalTimestamp: false, includeNativeItemData: false, includeNativeSources: false, includeTypedItem: false, includeItemOrder: false)", migration)
        self.assertIn("makeModel(includeNativeIdentity: false, preserveItemKeyInHistory: true, includeLists: false, includeOptionalTimestamp: false, includeNativeItemData: false, includeNativeSources: false, includeTypedItem: false, includeItemOrder: false)", migration)
        self.assertIn("makeModel(includeNativeIdentity: false, preserveItemKeyInHistory: false, includeLists: false, includeOptionalTimestamp: false, includeNativeItemData: false, includeNativeSources: false, includeTypedItem: false, includeItemOrder: false)", migration)
        self.assertIn("let sourceModel = legacyCandidates.first", migration)
        self.assertIn("guard let sourceModel else", migration)
        self.assertNotIn("compatibleSourceModels.count == 1", migration)
        shipped = LEGACY_SHIPPED.read_text()
        self.assertIn('entity("Item", [content(), attribute("timestamp", .dateAttributeType),', shipped)
        self.assertNotIn('attribute("nativeIdentifier"', shipped)
        self.assertNotIn('attribute("nativeChecksum"', shipped)
        self.assertNotIn("preservesValueInHistoryOnDeletion", shipped)

    def test_public_search_stays_local_and_native_search_has_legacy_uuid_fallback(self):
        body = method_body(self.persistence, "func searchItems(identifiers: [String]?) throws -> [ClipboardItem]")
        self.assertIn('key IN %@', body)
        self.assertNotIn("nativeIdentifier", body)
        self.assertIn("guard let identifiers else { return try fetch(\"Item\").map(ClipboardPersistence.item) }", body)
        self.assertIn("guard !identifiers.isEmpty else { return [] }", body)
        native = method_body(self.persistence, "func searchNativeItems(identifiers: [String]?) throws -> [ClipboardItem]")
        self.assertIn("nativeIdentifier IN %@ OR (nativeIdentifier == nil AND key IN %@)", native)

    def test_history_reads_native_identifier_and_tombstone_preserving_empty_string(self):
        body = method_body(self.history, "private func changes(in transactions: [NSPersistentHistoryTransaction]) -> [OriginalSearchHistoryChange]")
        self.assertIn('identifier = reader.searchIdentifier(for: change.changedObjectID)', body)
        reader = (ROOT / 'replica/Sources/PastoCore/ClipboardSnapshotReader.swift').read_text()
        producer = method_body(reader, 'func searchIdentifier(for objectID:')
        self.assertIn('if let nativeIdentifier = object.value(forKey: "nativeIdentifier") as? String', producer)
        self.assertIn('return nativeIdentifier', producer)
        self.assertIn('if let nativeIdentifier = change.tombstone?["nativeIdentifier"] as? String', body)
        self.assertIn('identifier = nativeIdentifier', body)
        self.assertIn('change.tombstone?["key"] as? String', body)

    def test_search_sdk_keeps_string_ids_and_maps_hits_to_local_uuid(self):
        entry = method_body(self.index, "private struct Entry: Equatable")
        self.assertIn("let record: ClipboardSearchRecord", entry)
        record = (ROOT / "replica/Sources/PastoCore/ClipboardSearchRecord.swift").read_text()
        self.assertIn("public let id: UUID", record)
        self.assertIn("public let nativeIdentifier: String?", record)
        self.assertIn("public var searchIdentifier: String { nativeIdentifier ?? id.uuidString }", record)
        self.assertIn("var searchIdentifier: String { record.searchIdentifier }", entry)
        query = method_body(self.index, "nonisolated private static func matchingIdentifiers(predicate: String, limit: Int) async throws -> [String]")
        self.assertIn("found.append(result.item.uniqueIdentifier)", query)
        self.assertNotIn("UUID(uuidString:", query)
        replace = method_body(self.index, "private func replaceQuery(with nodes: [OriginalSearchQueryNode])")
        self.assertIn("installResultSource(store.makeSearchCollection(identifiers: found))", replace)
        searchable = method_body(self.index, "private func searchableItem(_ entry: Entry, isUpdate: Bool) -> CSSearchableItem")
        self.assertIn('uniqueIdentifier: entry.searchIdentifier,', searchable)
        self.assertNotIn('domain + ":"', searchable)
        rebuild = method_body(self.index, "nonisolated private func rebuild(identifiers: [String]?, _ acknowledge: @escaping () -> Void)")
        self.assertNotIn("localIdentifier.isEmpty", rebuild)
        reindex = method_body(self.index, "private func reindexTargets(_ identifiers: [String]) async throws")
        self.assertIn("let input = identifiers.filter { !$0.isEmpty }", reindex)
        self.assertNotIn("UUID(uuidString:", reindex)
        self.assertNotIn("Array(Set(", reindex)
        self.assertIn("store.searchIndexRecords(identifiers: identifiers)", self.index)

    def test_migration_preserves_source_string_and_stable_local_uuid(self):
        source_id = method_body(self.migration, "private static func sourceIdentifier(_ object: NSManagedObject, kind: String) throws -> String")
        self.assertIn("return source", source_id)
        snapshot = method_body(self.migration, "private static func snapshot(in context: NSManagedObjectContext) throws -> Snapshot")
        self.assertIn('let sourceIdentifier = try sourceIdentifier(object, kind: "item")', snapshot)
        self.assertIn('let id = identifier(sourceIdentifier, kind: "item")', snapshot)
        self.assertIn("nativeIdentifier: id.uuidString", snapshot)
        self.assertIn("sourceIdentifier: sourceIdentifier", snapshot)
        self.assertIn('object.value(forKey: "checksum") as? String', snapshot)

    def test_legacy_hit_retains_effective_id_and_checksum_always_tracks_current_content(self):
        add = method_body(self.store, "func addWithInsertionResult(_ item: ClipboardItem,")
        self.assertIn("state.items[i].nativeChecksum = checksum", add)
        self.assertNotIn("nativeChecksum = item.nativeChecksum ??", add)
        self.assertIn("if state.items[i].nativeIdentifier == nil { state.items[i].nativeIdentifier = state.items[i].id.uuidString }", add)
        duplicate = method_body(self.store, "public func duplicateItem(id: UUID) throws -> UUID")
        self.assertLess(duplicate.index("item.nativeIdentifier = item.id.uuidString"), duplicate.index("Self.refreshNativeChecksum(&item)"))

    def test_legacy_import_does_not_erase_existing_native_fields(self):
        body = method_body(self.store, "public func importArchive(from url: URL) throws")
        self.assertIn("if item.nativeIdentifier == nil { item.nativeIdentifier = existing.nativeIdentifier }", body)
        self.assertIn("if item.nativeChecksum == nil { item.nativeChecksum = existing.nativeChecksum }", body)
        self.assertIn("if item.sourceIdentifier == nil { item.sourceIdentifier = existing.sourceIdentifier }", body)


if __name__ == "__main__":
    unittest.main()
