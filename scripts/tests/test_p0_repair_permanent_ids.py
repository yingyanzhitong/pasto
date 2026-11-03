from native_restore_only_scope_contract import pre_native_restore_only
"""Verify the original and current new-Item permanent-ID ordering statically."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body

class PermanentIDs(unittest.TestCase):
    def test_native_new_item_obtains_id_before_identifier_device_and_content(self):
        report=json.loads((ROOT/'.local/p0-repair/phase-4/permanent-id-readonly.json').read_text())
        for r in report['source_fragments']:
            self.assertEqual(source_fragments(ROOT/r['path'])[r['function_id'].split(':')[1]]['sha256'],r['sha256'])
        data=(ROOT/'.local/targets/Paste.arm64').read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),report['static_arm_evidence']['sha256'])
        def target(address):
            word=struct.unpack_from('<I',data,address-0x100000000)[0]
            self.assertEqual(word&0xfc000000,0x94000000)
            immediate=word&0x3ffffff
            return address+(immediate-(1<<26) if immediate&(1<<25) else immediate)*4
        self.assertEqual(target(0x100360eb8),0x100c075e0)
        self.assertEqual(target(0x100360ef4),0x100c0c0e0)
        self.assertEqual(target(0x100360f28),0x100c0b520)
        self.assertEqual(target(0x100360f40),0x100360ff8)
        stub=next(r for r in report['source_fragments'] if r['function_id']=='Paste:0x100c075e0')
        self.assertIn('"obtainPermanentIDsForObjects:error:"',(ROOT/stub['path']).read_text())

    def test_only_inserted_items_obtain_ids_before_any_field_application(self):
        persistence=(ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        update=body(persistence,'func update<T: Equatable>(_ values: [T], previous: [T], entity: String,')
        existing=body(update,'if let existing = objects[id]')
        self.assertNotIn('obtainPermanentIDs',existing)
        self.assertIn('if entity == "Item" { try context.obtainPermanentIDs(for: [object]) }',update)
        order=['NSEntityDescription.insertNewObject','try context.obtainPermanentIDs',
               'object.setValue(id, forKey: "key")','try apply(value, before[id], object)']
        self.assertEqual([update.index(t) for t in order],sorted(update.index(t) for t in order))
        self.assertEqual(update.count('obtainPermanentIDs'),1)
        self.assertNotIn('try? context.obtainPermanentIDs',update)

    def test_id_failure_throws_inside_transaction_without_returning_or_publishing_a_partial_item(self):
        persistence=(ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        commit=body(pre_native_restore_only(persistence),'func commit<T>(previous: StoreState?, deletingItemIDs: [UUID] = [],')
        self.assertLess(commit.index('try transaction.repository.update(state.items'),commit.index('try context.save()'))
        self.assertNotIn('catch',commit)
        self.assertIn('try context.performAndWait',commit)
        self.assertNotIn('rollback',commit)
        self.assertNotIn('try perform',commit)
        store=(ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        mutation=body(store,'private func mutateInTransaction<T>(historyAction: Bool = false,')
        self.assertLess(mutation.index('try persistence.commit('),mutation.index('publish(state)'))

if __name__=='__main__':unittest.main()
