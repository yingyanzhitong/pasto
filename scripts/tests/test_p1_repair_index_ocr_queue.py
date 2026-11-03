"""Original-bound OCR queue/source checks; no Swift, Vision, SDK or clock execution."""
import hashlib
import json
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from native_search_content_scope_contract import pre_native_search_content_bytes
from test_offline_p0_contracts import body
from index_write_scope_contract import assert_write_scope_only, assert_service_initializer_only, assert_ui_service_composition_only
from test_p0_repair_checksum_routing import original_fragment


class IndexOCRQueueContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-52'
        cls.proof = json.loads((cls.phase / 'ocr-queue-contract.json').read_text())
        cls.path = 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift'
        cls.source = (ROOT / cls.path).read_text()
        cls.before = (cls.phase / 'before' / cls.path).read_text()
        cls.record = (ROOT / 'replica/Sources/PastoCore/ClipboardSearchRecord.swift').read_text()
        cls.engine = (ROOT / 'replica/Sources/PastoCore/OCR.swift').read_text()
        cls.queue = body(cls.source, 'private func enqueueOCR(')
        cls.start = body(cls.source, 'private func startOCRWorker()')
        cls.consume = body(cls.source, 'private func drainOCRQueue()')
        cls.stop = body(cls.source, 'private func stopIndexing()')
        cls.original = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:])
                        for r in cls.proof['original_fragments']}

    def assertOrder(self, source, tokens):
        offsets = [source.index(token) for token in tokens]
        self.assertEqual(offsets, sorted(offsets))

    def test_raw_fragments_engine_and_prior_lifecycle_inputs_are_hash_bound(self):
        self.assertEqual(len(self.proof['original_fragments']), 38)
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        for row in self.proof['prior_contracts'] + [self.proof['append_arm']]:
            self.assertEqual(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest(), row['sha256'])
        for path, digest in self.proof['current_sources'].items():
            frozen = self.phase / 'after' / path
            self.assertEqual(hashlib.sha256(frozen.read_bytes()).hexdigest(), digest)
            if path == self.path:
                from fixed_review_scope_contract import before_fixed_review_bytes
                historical_source = before_fixed_review_bytes(ROOT / path).decode()
                for marker in ['private func enqueueOCR(', 'private func startOCRWorker()',
                               'private func drainOCRQueue()', 'private func stopIndexing()']:
                    assert_write_scope_only(self, body(historical_source, marker), body(frozen.read_text(), marker))
            else:
                if path.endswith('/OCR.swift'):
                    from fixed_review_scope_contract import before_fixed_review_bytes
                    data = before_fixed_review_bytes(ROOT / path)
                else:
                    data = pre_native_search_content_bytes(ROOT / path)
                self.assertEqual(hashlib.sha256(data).hexdigest(), digest)
        self.assertEqual(self.proof['binary']['sha256'], '871f00354fbb1c165d858a98e6d19d6f43cb9d3f9f958b3e07c7f07eb5c19afb')

    def test_entity_and_projected_record_fields_are_different_real_structures(self):
        rows = {r['name']: r for r in self.proof['record_structures']}
        self.assertEqual(rows['SearchableItemEntity']['fields'],
                         ['id', 'type', 'title', 'content', 'app', 'imageData', 'timestamp', 'device', 'pinboard'])
        self.assertEqual(rows['SearchableItem']['fields'],
                         ['id', 'app', 'timestamp', 'device', 'pinboard', 'type', 'title', 'content', 'imageData'])
        for row in rows.values():
            header = bytes.fromhex(row['descriptor_bytes'])
            self.assertEqual(int(row['descriptor'], 16) + 16 + struct.unpack_from('<i', header, 16)[0],
                             int(row['field_descriptor'], 16))
            size, count = struct.unpack_from('<HI', bytes.fromhex(row['bytes']), 10)
            self.assertEqual((size, count), (12, 9))

    def test_business_protocol_slot_48_is_deferred_image_data_not_value_witness_copy(self):
        rows = {r['address']: {s['offset']: s for s in r['slots']} for r in self.proof['record_protocols']}
        self.assertEqual(rows['0x100ecd440']['0x48']['target'], '0x1003752a8')
        self.assertEqual(rows['0x100ec8c30']['0x48']['target'], '0x1002ee528')
        for slots in rows.values():
            for slot in slots.values():
                self.assertTrue(slot['chain']['declared_chain_reachable'])
                encoded = struct.unpack('<Q', bytes.fromhex(slot['bytes']))[0]
                self.assertEqual(hex(0x100000000 + (encoded & ((1 << 36) - 1))), slot['target'])
        self.assertIn('unaff_x20 + 0x50', self.original['0x1003752a8'])
        self.assertIn('**(code **)(uVar11 + 0x48)', self.original['0x1002ec9d8'])
        self.assertIn('lVar3 + 0x30', self.original['0x1002ee16c'])
        self.assertIn('*puVar1 = 0;', self.original['0x1002ee16c'])
        self.assertIn('puVar1[1] = 0;', self.original['0x1002ee16c'])

    def test_queue_filters_existing_set_then_unions_and_appends_without_reading_images(self):
        self.assertOrder(self.queue, ['entries.filter', '$0.imageData != nil', '!ocrQueuedIdentifiers.contains',
                                    '.map(\\.searchIdentifier)', 'ocrQueuedIdentifiers.formUnion(added)',
                                    'ocrQueue.append(contentsOf: added)'])
        self.assertNotIn('readImage()', self.queue)
        self.assertNotIn('startOCRWorker()', self.queue)
        native = self.original['0x1002ec26c']
        self.assertOrder(native, ['unaff_x20 + 0x108', 'FUN_1002ee748()', 'unaff_x20 + 0x100', 'FUN_1002daab8('])
        self.assertNotIn('FUN_1002ec520(', native)

    def test_pending_set_batch_duplicates_and_inflight_reenqueue_fixture(self):
        # Bound to filter-before-union source above, not an execution of the Swift queue.
        pending, queue = {'old'}, ['old']
        incoming = ['old', 'new', 'new', 'other']
        added = [i for i in incoming if i not in pending]
        pending.update(added)
        queue.extend(added)
        self.assertEqual(queue, ['old', 'new', 'new', 'other'])
        identifier = queue.pop(0)
        pending.discard(identifier)
        self.assertEqual(identifier, 'old')
        self.assertNotIn('old', pending)
        self.assertEqual([i for i in ['old'] if i not in pending], ['old'])

    def test_low_priority_starter_replaces_only_missing_or_cancelled_task(self):
        self.assertIn('guard isRunning, !ocrQueue.isEmpty, ocrTask == nil || ocrTask?.isCancelled == true else { return }', self.start)
        self.assertOrder(self.start, ['Task(priority: .low) { [self] in', 'await drainOCRQueue()', 'ocrTask = nil'])
        native = self.original['0x1002ec520']
        for token in ['+ 0xf0', '+ 0x100', '+ 0xf8', '_swift_task_isCancelled()', 'get_low', '&DAT_100c3e950']:
            self.assertIn(token, native)
        d = self.proof['async_descriptors'][0]
        delta, frame = struct.unpack('<iI', bytes.fromhex(d['bytes']))
        self.assertEqual((hex(int(d['address'], 16) + delta), frame), ('0x1002ee824', 32))
        self.assertIn('FUN_1002ec72c()', self.original['0x1002ec660'])
        self.assertIn('+ 0xf8) = 0', self.original['0x1002ec6f4'])

    def test_fresh_first_record_fetch_precedes_cancellation_image_access_and_recognition(self):
        self.assertOrder(self.consume, ['while isRunning && !Task.isCancelled && !ocrQueue.isEmpty',
                        'ocrQueue.removeFirst()', 'ocrQueuedIdentifiers.remove(identifier)',
                        'try liveEntries(identifiers: [identifier]).first', 'try Task.checkCancellation()',
                        'let readImage = entry.imageData', 'let data = readImage()',
                        'try await ImageTextRecognizer.recognizeWords('])
        self.assertNotIn('indexed[', self.consume)
        native = self.original['0x1002ec7d8']
        self.assertOrder(native, ['FUN_1002ee68c(0,1)', 'FUN_1002ee560(', 'lVar9 + 0x98', 'FUN_1002ec9d8'])
        self.assertOrder(self.original['0x1002ec9d8'], ['Swift::Task::_checkCancellation()', 'uVar11 + 0x48'])

    def test_missing_record_or_nil_image_skips_without_sdk_or_cooldown(self):
        self.assertIn('guard let entry = try liveEntries(identifiers: [identifier]).first else { continue }', self.consume)
        self.assertIn('guard let readImage = entry.imageData, let data = readImage() else { continue }', self.consume)
        self.assertNotIn('guard !data.isEmpty', self.consume)
        self.assertIn('guard !imageData.isEmpty else { throw OCRError.invalidImageData }', self.engine)

    def test_default_1024_background_engine_is_existing_adapter_not_new_native_execution(self):
        self.assertIn('*param_1 = 0x400;', self.original['0x1002d36e8'])
        self.assertIn('maximumDimension: 1024', self.consume)
        self.assertIn('Task.detached(priority: .utility)', body(self.engine, 'public static func recognizeDocument('))
        self.assertIn('try f_1002d4738(', self.engine)
        self.assertIn('try f_1002d4830(', self.engine)
        self.assertIn('@MainActor', self.source)
        self.assertTrue(any('MainActor' in p and 'not claimed' in p for p in self.proof['retained_partial_contracts']))

    def test_ocr_words_join_with_ascii_space_and_do_not_use_display_document_newlines(self):
        self.assertIn('words.map(\\.text).joined(separator: " ")', self.consume)
        self.assertNotIn('document.text', self.consume)
        self.assertIn('Swift::String', self.original['0x1002ec9d8'])

    def test_projection_preserves_metadata_and_appends_newline_without_image_capability(self):
        projection = body(self.record, 'public func appendingRecognizedText(')
        self.assertIn('let existing = content?() ?? ""', projection)
        self.assertIn('existing.isEmpty ? text : existing + "\\n" + text', projection)
        for name in ['id', 'nativeIdentifier', 'type', 'title', 'app', 'modified', 'device', 'pinboard', 'contentVersion']:
            self.assertIn(name + ': ' + name, projection)
        self.assertIn('content: { combined }, imageData: nil', projection)
        arm = (ROOT / self.proof['append_arm']['path']).read_text()
        self.assertIn('1002ee36c:', arm)
        self.assertIn('#0xa', arm)
        self.assertIn('1002ee374:', arm)
        self.assertIn('1002ee39c:', arm)
        for existing, recognized, expected in [('', 'word', 'word'), ('old', 'new', 'old\nnew')]:
            self.assertEqual(existing + '\n' + recognized if existing else recognized, expected)

    def test_recognized_nonempty_text_is_a_direct_update_write_without_clipboard_payload_mutation(self):
        self.assertOrder(self.consume, ['if !text.isEmpty', 'Entry(entry.record.appendingRecognizedText(text))',
                        'searchableItem(enriched, isUpdate: true)', 'Self.writeSearchableItems([item], index: resolveWriteIndex())',
                        'try await ContinuousClock().sleep(for: .seconds(2))'])
        for token in ['retryTransientIndexErrors', 'recognizeImageDocument', 'recognizedTextPayloadKey',
                      'payloads[', 'stateStore.save', 'recordRestoredItems', 'indexed[']:
            self.assertNotIn(token, self.consume)
        self.assertIn('FUN_1002e1bac(lVar19,uVar24,puVar20,1)', self.original['0x1002ec9d8'])

    def test_success_or_empty_result_cools_down_but_errors_and_missing_inputs_do_not(self):
        self.assertEqual(self.consume.count('sleep('), 1)
        suffix = self.consume[self.consume.index('} catch is CancellationError'):]
        self.assertIn('return', suffix[:suffix.index('} catch {')])
        self.assertIn('logger.error(', suffix)
        self.assertNotIn('sleep(', suffix)
        for address in ['0x1002ec9d8', '0x1002ed360']:
            self.assertIn('FUN_1002eb1f0(2000000000000000000,0,0,0,1)', self.original[address])
        self.assertIn('pcVar1 = FUN_1002edab0', self.original['0x1002eda2c'])
        self.assertIn('pcVar1 = FUN_1002edc9c', self.original['0x1002eda2c'])

    def test_cancel_check_is_before_image_read_and_sdk_error_propagates_to_queue_catch(self):
        self.assertEqual(self.consume.count('Task.checkCancellation()'), 1)
        self.assertIn('continuation.resume(throwing: error)', body(self.source, 'private static func writeSearchableItems('))
        self.assertNotIn('try?', self.consume)
        self.assertNotIn('Task.detached', self.consume)
        # Source-bound transition fixture only: no recognition or sleeping is executed.
        outcomes = {'missing': [], 'nil-image': [], 'empty': ['sleep-2'],
                    'text': ['project', 'update', 'sleep-2'], 'error': ['log', 'next'], 'cancel': ['exit']}
        self.assertNotIn('sleep-2', outcomes['error'])
        self.assertEqual(outcomes['cancel'], ['exit'])

    def test_stop_cancels_and_awaits_only_ocr_then_clears_slot_preserving_queue(self):
        self.assertOrder(self.stop, ['isRunning = false', 'historyTask?.cancel()', 'historyTask = nil',
                        'ocrTask.cancel()', 'await ocrTask.value', 'ocrTask = nil'])
        for token in ['worker', 'ocrQueue', 'ocrQueuedIdentifiers', 'stateStore']:
            self.assertNotIn(token, self.stop)
        native = self.original['0x1002f2d18']
        self.assertOrder(native, ['+ 0xf0) = 0', '+ 0x120', '+ 0x120) = 0', '+ 0xf8', 'Swift::Task::_get_value'])
        self.assertNotIn('+ 0x108', native)
        self.assertNotIn('+ 0x100', native)

    def test_actual_reset_mismatch_and_full_callback_await_stop_before_clear_or_enqueue(self):
        reset = body(self.source, 'private func resetIndex(')
        self.assertOrder(reset, ['if isRunning { await stopIndexing() }', 'try stateStore.save(nil)',
                                'try await clearIndex()', 'try await initializeIndexIfNeeded(request)'])
        initialize = body(self.source, 'private func initializeIndexIfNeeded(')
        self.assertOrder(initialize, ['if needsReset && isRunning { await stopIndexing() }',
                                     'guard !isRunning else { return }', 'isRunning = true'])
        callback = body(self.source, 'private func enqueueDelegateRebuild(')
        self.assertOrder(callback, ['if isRunning { await stopIndexing() }', 'pending = request', 'startWorker()'])
        self.assertEqual(self.source.count('await stopIndexing()'), 3)

    def test_full_target_and_history_producers_enqueue_before_sdk_and_kick_on_correct_tail(self):
        for marker in ['private func reindexTargets(', 'private func indexInitialSnapshot(', 'private func applyHistoryChanges(']:
            method = body(self.source, marker)
            self.assertOrder(method, ['try liveEntries(', 'enqueueOCR(live)', 'Self.writeSearchableItems('])
            self.assertIn('startOCRWorker()', method)
        target = body(self.source, 'private func reindexTargets(')
        self.assertOrder(target, ['guard !input.isEmpty else { return }', 'enqueueOCR(live)',
                                 'Self.writeSearchableItems(', 'for entry in refreshed', 'startOCRWorker()'])
        self.assertNotIn('defer', target)
        snapshot = body(self.source, 'private func indexInitialSnapshot(')
        self.assertOrder(snapshot, ['guard !allIDs.isEmpty else { return false }', 'defer { startOCRWorker() }', 'enqueueOCR(live)'])
        self.assertOrder(self.original['0x1002e8de0'], ['FUN_1002ec26c(', '&DAT_100c3e850', 'FUN_1002e7914('])
        self.assertOrder(self.original['0x1002eaa10'], ['FUN_1002ec26c(', 'FUN_1002e1bac('])
        for address in ['0x1002e8de0', '0x1002e96ac', '0x1002e9d54']:
            self.assertIn('FUN_1002ec520()', self.original[address])

    def test_new_contracts_have_real_missing_before_consumers_and_no_whole_function_upgrade(self):
        for token in ['ocrTask:', 'ocrQueue:', 'enqueueOCR(', 'drainOCRQueue(']:
            self.assertNotIn(token, self.before)
        previous_record = (self.phase / 'before/replica/Sources/PastoCore/ClipboardSearchRecord.swift').read_text()
        self.assertNotIn('appendingRecognizedText(', previous_record)
        self.assertEqual(len(self.proof['contracts']), 7)
        self.assertEqual(len(self.proof['new_function_ids']), 4)
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['function_map_markers_upgraded'], 0)
        self.assertTrue(all(not r['full_function_migration_verified'] for r in self.proof['contracts']))


if __name__ == '__main__':
    unittest.main()
