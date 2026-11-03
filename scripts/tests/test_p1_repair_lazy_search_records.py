from item_order_scope_contract import without_order_model
"""Original-bound source contracts only; no Swift, Core Data, OCR or Spotlight execution."""
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from snapshot_read_scope_contract import body, commit_business_body, projection_spelling
from test_p0_repair_checksum_routing import original_fragment


class LazySearchRecordContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-43'
        cls.proof = json.loads((cls.phase / 'lazy-record-contract.json').read_text())
        cls.record = (ROOT / 'replica/Sources/PastoCore/ClipboardSearchRecord.swift').read_text()
        cls.persistence = (ROOT / 'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        cls.store = (ROOT / 'replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        cls.index = (ROOT / 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        cls.make = body(cls.persistence, 'func searchIndexRecords(')
        cls.original = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:])
                        for r in cls.proof['original_fragments']}

    def before(self, path):
        return (self.phase / 'before' / path).read_text()

    def test_original_fragments_and_native_selector_evidence_are_bound(self):
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        selector, = self.proof['native_selector_bindings']
        self.assertEqual(selector['selector'], 'existingObjectWithID:error:')
        self.assertTrue(selector['chain']['declared_chain_reachable'])
        self.assertEqual(selector['chain']['pointer_format'], 6)

    def test_original_raw_one_means_private_context_not_main_context(self):
        sdk = self.proof['sdk']
        raw = Path(sdk['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), sdk['sha256'])
        self.assertRegex(raw, rb'NSPrivateQueueConcurrencyType\s*= 0x01')
        for address in ['0x100372440', '0x100371f2c']:
            text = self.original[address]
            self.assertIn('initWithConcurrencyType_((ID)self,1)', text)
            self.assertIn('setPersistentStoreCoordinator_(self_00,param_1)', text)
            self.assertIn('NSManagedObjectContext::_performAndWait()', text)

    def test_original_constructor_branches_image_and_content_without_evaluation(self):
        text = self.original['0x100371998']
        self.assertIn('param_1[3].str = (char *)0x0', text)
        self.assertIn('pcVar14 = FUN_100375458', text)
        self.assertIn('param_1[3].str = (char *)FUN_1003753f8', text)
        self.assertIn('*(ID *)(puVar13 + 0x18) = IVar5', text)
        self.assertIn('puVar13[0x30] = uVar16', text)
        self.assertNotIn('FUN_1003724f0(', text)

    def test_native_constructor_uses_actual_relation_metadata_and_timestamp(self):
        for token in ['object.value(forKey: "sourceApplication") as? NSManagedObject',
                      'object.value(forKey: "device") as? NSManagedObject',
                      'modified: object.value(forKey: "timestamp") as? Date',
                      'app: application?.value(forKey: "name") as? String',
                      'device: device?.value(forKey: "name") as? String']:
            self.assertIn(token, self.make)
        for forbidden in ['value.sourceName', 'value.sourceDevice', 'sourceApplications', 'applicationNames(for:']:
            self.assertNotIn(forbidden, self.make)

    def test_single_pinboard_requires_exact_native_raw_type_two(self):
        self.assertIn('(list?.value(forKey: "rawType") as? NSNumber)?.int64Value == 2', self.make)
        self.assertIn('? list?.value(forKey: "identifier") as? String : nil', self.make)
        self.assertNotIn('?? 2', self.make)
        self.assertNotIn('pinboardIDs', self.make)
        self.assertIn('FUN_1003250f0()', self.original['0x100371998'])

    def test_native_factory_captures_coordinator_object_id_and_kind_in_deferred_closures(self):
        self.assertIn('ClipboardSearchRecordReader(coordinator: coordinator, objectID: object.objectID, kind: kind)', self.make)
        self.assertIn('content: kind == .image ? nil : { reader.content() }', self.make)
        self.assertIn('imageData: kind == .image ? { reader.imageData() } : nil', self.make)
        for forbidden in ['rawPasteboardItems', 'f_10031aeec(', 'f_10037c9a8(', '.plainText', '.prefix(5000)']:
            self.assertNotIn(forbidden, self.make)

    def test_reader_retains_no_materialized_item_or_owner_context(self):
        reader = body(self.record, 'final class ClipboardSearchRecordReader')
        fields = re.findall(r'private let (\w+): ([^\n]+)', reader)
        self.assertEqual(fields, [('coordinator', 'NSPersistentStoreCoordinator'),
                                  ('objectID', 'NSManagedObjectID'), ('kind', 'OriginalPasteboardContentKind')])
        self.assertNotIn('private var ', reader)
        self.assertNotIn('weak ', reader)
        self.assertNotIn('unowned ', reader)

    def test_each_callback_allocates_context_and_resolves_current_object_before_decoding(self):
        read = body(self.record, 'private func read<T>(')
        order = ['NSManagedObjectContext(concurrencyType: .privateQueueConcurrencyType)',
                 'context.persistentStoreCoordinator = coordinator', 'try context.performAndWait',
                 'try OriginalObjCExceptionBridge.withResult', 'try context.existingObject(with: objectID)',
                 'object.value(forKey: "data")', 'data.value(forKey: "rawPasteboardItems")',
                 'OriginalPasteboardDataCodec.f_10031aeec(raw)']
        offsets = [read.index(t) for t in order]
        self.assertEqual(offsets, sorted(offsets))
        self.assertIn('object.entity.name == "Item", !object.isDeleted', read)
        self.assertIn('return nil', body(read, 'catch'))
        for forbidden in ['context.save()', 'context.rollback()', 'context.reset()', 'insertNewObject', 'UserDefaults']:
            self.assertNotIn(forbidden, read)

    def test_record_to_entry_to_sdk_copies_callbacks_without_running_them(self):
        live = body(self.index, 'private func liveEntries(')
        self.assertIn('store.searchIndexRecords(identifiers: identifiers).map { Entry($0) }', live)
        entry = body(self.index, 'private struct Entry: Equatable')
        self.assertIn('let record: ClipboardSearchRecord', entry)
        self.assertIn('init(_ record: ClipboardSearchRecord) { self.record = record }', entry)
        self.assertIn('var content: (() -> String?)? { record.content }', entry)
        self.assertIn('var imageData: (() -> Data?)? { record.imageData }', entry)
        self.assertNotIn('record.content()', entry)
        self.assertNotIn('record.imageData()', entry)
        self.assertIn('FUN_1002fc0ec(param_1,puVar5)', self.original['0x1002faafc'])
        self.assertIn('lVar9 = param_2[6]', self.original['0x10037582c'])
        self.assertIn('lVar9 = param_2[10]', self.original['0x10037582c'])

    def test_all_actual_store_sdk_paths_use_native_records_including_snapshot_fallback(self):
        store = body(self.store, 'public func searchIndexRecords(')
        self.assertIn('try persistence.searchIndexRecords(identifiers: identifiers)', store)
        self.assertIn('if try await indexInitialSnapshot(currentEntries, resuming: resumeState)', self.index)
        initial = body(self.index, 'private func indexInitialSnapshot(')
        self.assertIn('try store?.searchIndexIdentifiers(before: before)', initial)
        self.assertIn('try liveEntries(identifiers: Array(input[lowerBound..<upperBound]))', initial)
        self.assertIn('let live = try liveEntries(identifiers: identifiers)', self.index)
        self.assertIn('try liveEntries(identifiers: Array(input[lowerBound..<upperBound]))', self.index)
        live = body(self.index, 'private func liveEntries(')
        self.assertNotIn('applicationNames', live)

    def test_normal_text_getter_matches_original_all_item_space_join(self):
        original = self.original['0x1003724f0']
        self.assertIn('if (param_6 == 5) goto LAB_100373188', original)
        loop = original.split('LAB_100373188:', 1)[1].split('if ((param_6 == 1)', 1)[0]
        self.assertIn('while (puVar56 != puVar45)', loop)
        self.assertIn('FUN_10037c9a8()', loop)
        self.assertIn('separator.str = (char *)0x20', loop)
        method = body(self.record, 'static func text(')
        plain = method.split('case .unknown, .text:', 1)[1].split('case .image:', 1)[0]
        expected = 'items.compactMap { $0.f_10037c9a8() }.joined(separator: " ")'
        self.assertIn(expected, plain)
        self.assertNotIn('.first', plain)
        self.assertNotIn('Set(', plain)
        before = self.before('replica/Sources/Pasto/UI/ReplicaSearchIndex.swift')
        self.assertIn('(item.plainText ?? "")', before)
        # ASCII source-bound cases; this is a Python semantic fixture, not execution of Swift.
        cases = [(['pasto alpha', 'pasto beta'], 'pasto alpha pasto beta'),
                 (['alpha', None, 'beta'], 'alpha beta'), (['alpha', '', 'beta'], 'alpha  beta'),
                 (['same', 'same'], 'same same')]
        for inputs, wanted in cases:
            actual = ' '.join(value for value in inputs if value is not None)
            self.assertEqual(actual, wanted)
        self.assertNotEqual(cases[0][0][0], cases[0][1])

    def test_color_reads_first_optional_string_and_images_have_no_content(self):
        text = body(self.record, 'static func text(')
        self.assertIn('case .image: return nil', text)
        self.assertIn('case .color: return items.first?.f_10037c9a8()', text)
        self.assertNotIn('recognizedText', self.record)
        self.assertNotIn('recognizedText', self.index)
        self.assertNotIn('ImageTextRecognizer', self.record)

    def test_image_reader_retains_independent_all_items_first_non_nil_capability(self):
        method = body(self.record, 'func imageData()')
        self.assertIn('read { _, items in items.compactMap { $0.f_10037d5c4() }.first }', method)
        original = self.original['0x100371fd4']
        self.assertIn('FUN_10037d5c4()', original)
        self.assertIn('if (*(long *)(local_120 + 0x10) == 0)', original)
        self.assertIn('*param_1 = *(undefined8 *)(local_120 + 0x20)', original)
        self.assertNotIn('NSImage(', method)

    def test_sdk_invokes_optional_content_before_5000_limit_and_preserves_nil(self):
        builder = body(self.index, 'private func searchableItem(')
        order = ['let content = entry.content?()', 'let text = content.map { String($0.prefix(5000)) }',
                 'attributes.textContent = text', 'attributes.contentDescription = text']
        offsets = [builder.index(t) for t in order]
        self.assertEqual(offsets, sorted(offsets))
        self.assertNotIn('?? ""', builder[:builder.index('attributes.contentModificationDate')])
        self.assertNotIn('prefix(5000)', self.record)
        self.assertIn('FUN_1002e3a8c(5000,pcVar9,lVar15)', self.original['0x1002e3ce8'])

    def test_optional_device_bridges_nil_and_single_board_bridges_empty_string(self):
        builder = body(self.index, 'private func searchableItem(')
        self.assertIn('attributes.setValue(entry.device.map { $0 as NSString }, forCustomKey: deviceKey)', builder)
        self.assertIn('attributes.setValue((entry.pinboard ?? "") as NSString, forCustomKey: pinboardKey)', builder)
        self.assertNotIn('NSArray', builder)
        self.assertIn('public let device: String?', self.record)
        self.assertIn('public let pinboard: String?', self.record)
        self.assertIn('lVar15 = -0x2000000000000000', self.original['0x1002e3ce8'])

    def test_pinboard_custom_attribute_is_single_valued_per_original_factory(self):
        key = next(line for line in self.index.splitlines() if 'keyName: "pastePinboard"' in line)
        self.assertIn('multiValued: false', key)
        self.assertIn('((ID)self,pNVar2,1,1,0,0)', self.original['0x1002e1948'])

    def test_metadata_preserves_explicit_empty_title_and_original_kind_names(self):
        make = body(self.record, 'static func make(')
        self.assertIn('title: value.originalTitle ?? name', make)
        self.assertNotIn('title.isEmpty', make)
        for kind, title in [('unknown', 'Unknown'), ('image', 'Image'), ('color', 'Color'),
                            ('files', 'File'), ('link', 'Link'), ('text', 'Text')]:
            self.assertIn(f'case .{kind}: name = "{title}"', make)
        self.assertIn('type: name,', make)
        self.assertNotIn('lowercased()', make)

    def test_file_content_joins_all_decoded_url_paths_with_spaces(self):
        method = body(self.record, 'static func text(')
        files = method.split('case .files:', 1)[1].split('case .link:', 1)[0]
        self.assertIn('items.compactMap { $0.f_10037cc6c()?.path }.joined(separator: " ")', files)
        self.assertNotIn('\\n', files)
        original = self.original['0x1003724f0']
        self.assertIn('UniformTypeIdentifiers::UTType::get_fileURL', original)
        self.assertIn('Foundation::URL::get_path', original)
        self.assertIn('separator_00.str = (char *)0x20', original)

    def test_link_content_appends_optional_preview_name_to_first_absolute_url(self):
        method = body(self.record, 'static func text(')
        link = method.split('case .link:', 1)[1]
        self.assertIn('let url = items.first?.f_10037ce0c()', link)
        self.assertIn('var values = url.map { [$0.absoluteString] } ?? []', link)
        self.assertIn('OriginalImagePreviewMetadataCodec.decodeLink(preview)?.name', link)
        self.assertIn('values.append(name)', link)
        self.assertIn('values.joined(separator: " ")', link)
        original = self.original['0x1003724f0']
        link_original = original.split('if (param_6 == 4)', 1)[1].split('LAB_100373784:', 1)[0]
        self.assertIn('FUN_10037ce0c(', link_original)
        self.assertIn('Foundation::URL::get_absoluteString', link_original)
        self.assertIn('if (lVar41 != 0)', link_original)
        self.assertIn('plVar44[uVar42 * 2 + 5] = lVar41', link_original)

    def test_cache_equality_does_not_run_readers_and_version_is_explicit_adapter(self):
        equal = body(self.record, 'public static func ==')
        for field in ['id', 'nativeIdentifier', 'type', 'title', 'app', 'modified', 'device', 'pinboard', 'contentVersion']:
            self.assertIn(f'lhs.{field} == rhs.{field}', equal)
        self.assertNotIn('content?', equal)
        self.assertNotIn('imageData?', equal)
        self.assertIn('contentVersion: object.value(forKey: "updatedAt") as? Date ?? value.updatedAt', self.make)

    def test_new_record_reads_do_not_alter_old_schemas_transactions_or_capture(self):
        path = 'replica/Sources/PastoCore/ClipboardPersistence.swift'
        previous = self.before(path)
        self.assertEqual(commit_business_body(self.persistence), commit_business_body(previous))
        # New typed Item class is selected only for the destination/current model.
        model = body(self.persistence, 'private static func makeModel(')
        old_model = body(previous, 'private static func makeModel(')
        typed = body(model, 'if includeTypedItem')
        self.assertIn('NSStringFromClass(PastoItemEntity.self)', typed)
        self.assertEqual(without_order_model(model).replace('        if includeTypedItem ' + typed + '\n', '', 1), old_model)
        migration = body(self.persistence, 'private static func migrateLegacyStoreIfNeeded(')
        old_migration = body(previous, 'private static func migrateLegacyStoreIfNeeded(')
        tail = '        // The older history-retention variants'
        self.assertEqual(migration[migration.index(tail):], old_migration[old_migration.index(tail):])
        current_read = body(self.persistence, 'func searchNativeItems(')
        old_read = body(previous, 'func searchNativeItems(')
        old_head, _, old_tail = old_read.partition('let request = NSFetchRequest<NSManagedObject>(entityName: "Item")')
        new_head, _, new_tail = current_read.partition('let request = PastoItemEntity.defaultFetchRequest()')
        self.assertIn('PastoItemEntity.defaultFetchRequest()', current_read)
        self.assertEqual(tuple(map(projection_spelling, (new_head, new_tail))), tuple(map(projection_spelling, (old_head, old_tail))))
        self.assertNotIn('context.save()', self.make)
        self.assertNotIn('context.setValue', self.make)
        self.assertNotIn('insertNewObject', self.make)

    def test_normal_domain_closures_are_limited_and_preview_branches_stay_explicitly_open(self):
        self.assertEqual(len(self.proof['contracts']), 8)
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['function_map_markers_upgraded'], 0)
        text = body(self.record, 'static func text(')
        self.assertIn('case .files:', text)
        self.assertIn('case .link:', text)
        self.assertIn('return value.isEmpty ? legacyPreviewFallback() : value', text)
        row, = [r for r in self.proof['contracts'] if r['function_id'] == 'Paste:0x1003724f0']
        self.assertIn('normal nonempty', row['scope'])
        self.assertFalse(row['full_function_migration_verified'])


if __name__ == '__main__':
    unittest.main()
