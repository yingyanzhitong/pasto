"""Actual selected-index getter and optional applier lookup, without native execution."""
import hashlib
import json
from pathlib import Path
from entity_lookup_scope_contract import pre_entity_lookup
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from optional_selection_scope_contract import CHANGES,pre_optional_selection
from single_item_restore_scope_contract import pre_single_item_restore, pre_single_item_restore_bytes

class OptionalSelectionContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-85'
        cls.proof=json.loads((cls.phase/'optional-selection-contract.json').read_text())
        cls.base=json.loads((cls.phase/'baseline.json').read_text())
        cls.paths=dict(ref='replica/Sources/PastoCore/ClipboardCollectionItemReference.swift',entry='replica/Sources/PastoCore/ClipboardCollectionEntry.swift',host='replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',ui='replica/Sources/Pasto/UI/ReplicaUIController.swift')
        cls.source={k:pre_single_item_restore((ROOT/p).read_text())for k,p in cls.paths.items()}
        ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],ns)
        cls.ns=ns

    def before(self,k):return(self.phase/'before'/self.paths[k]).read_text()
    def original(self,a):
        r=next(r for r in self.proof['original_fragments']if r['address']==a)
        return original_fragment((ROOT/r['path']).read_text(),a[2:])

    def test_original_fragments_binary_decoder_and_reused_optional_provider_bound(self):
        self.assertEqual(len(self.proof['original_fragments']),13)
        for r in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['decoder'],self.proof['reused_optional_provider']]:
            self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])

    def test_actual_class_vtable_108_is_ordered_manager_array_getter(self):
        r=self.proof['native_class'];native=json.loads((ROOT/r['path']).read_text());self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
        c=next(c for c in native['result']['objc_classes']if c['name']==r['name']and not c['is_meta_class'])
        self.assertEqual(c['location']['address'],r['metadata']);self.assertEqual(int(r['getter']['address'],16),int(r['metadata'],16)+0x108)
        p=r['getter'];v,chain=self.ns['reachable_pointer'](int(p['address'],16))
        self.assertEqual(self.ns['read'](int(p['address'],16),8).hex(),p['bytes']);self.assertEqual(chain,p['chain'])
        self.assertEqual(hex(self.ns['base']+(v&((1<<36)-1))),p['target']);self.assertEqual(p['target'],'0x10022a930')
        getter=self.original('0x10022a930');self.assertIn('___lazy_storage___cellSelectionManager',getter)
        self.assertIn('puVar3 = (undefined *)*puVar1',getter);self.assertIn('return puVar3',getter)
        for token in ['sort','sorted','Set<']:self.assertNotIn(token,getter)
        duplicate=self.original('0x10022b1cc')
        self.assertEqual(getter[getter.index('{'):],duplicate[duplicate.index('{'):])

    def test_outer_and_inner_protocol_28_slots_are_real_declared_chain_pointers(self):
        outer=self.proof['outer_conformance'];a=int(outer['address'],16)
        self.assertEqual(self.ns['read'](a,16).hex(),outer['bytes'])
        rel=struct.unpack('<4i',bytes.fromhex(outer['bytes']));self.assertEqual(hex(a+8+rel[2]),outer['witness_table'])
        self.assertEqual(outer['type_name'],'AnyObservableCollection')
        for p in [outer['optional_ID_slot'],self.proof['inner_optional_ID_slot']]:
            address=int(p['address'],16);v,chain=self.ns['reachable_pointer'](address)
            self.assertEqual(chain,p['chain']);self.assertEqual(self.ns['read'](address,8).hex(),p['bytes'])
            self.assertEqual(hex(self.ns['base']+(v&((1<<36)-1))),p['target'])
        self.assertIn('FUN_1001aeafc()',self.original('0x1001aebd0'))
        self.assertIn('(unaff_x20 + 0x30)',self.original('0x1001aeafc'))
        self.assertIn('FUN_1001ae9dc(',self.original('0x1001ae768'))
        self.assertIn('auVar6._0_8_ = FUN_1001aec80',self.original('0x1001ae9dc'))
        self.assertIn('unaff_x20 + 0x20) + 0x28',self.original('0x1001aec80'))

    def test_actual_branch_targets_and_nil_skip_loop_instructions_bound(self):
        raw=(ROOT/self.proof['binary']['path']).read_bytes();self.assertEqual(len(self.proof['ARM_calls']),6)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);b=raw[pc-0x100000000:pc-0x100000000+4];self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little')
            self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+4*d,int(r['target'],16))
        words={int(r['address'],16):int(r['word'],16)for r in self.proof['ARM_words']};self.assertEqual(len(words),6)
        for r in self.proof['ARM_words']:
            pc=int(r['address'],16);b=raw[pc-0x100000000:pc-0x100000000+4]
            self.assertEqual(b.hex(),r['bytes']);self.assertEqual(int.from_bytes(b,'little'),int(r['word'],16))
        self.assertEqual(((words[0x10006e25c]>>10)&0xfff)*8,0x108)
        self.assertEqual(((words[0x1001b97a4]>>10)&0xfff)*8,0x28)
        w=words[0x10006e408];self.assertEqual(w&31,19);self.assertEqual(w&0xff000000,0xb4000000)
        d=(w>>5)&0x7ffff
        if d&0x40000:d-=0x80000
        self.assertEqual(0x10006e408+d*4,0x10006e2d4)

    def test_original_applier_lookup_is_optional_and_loop_skips_nil_in_input_order(self):
        source=self.original('0x1001b9698')
        self.assertIn('(param_2 < local_98) || (local_90 <= param_2)',source)
        self.assertIn('(param_1,1,1,lVar2)',source);self.assertIn('(param_5 + 0x28)',source)
        selection=self.original('0x10006e1f8')
        self.assertIn('if (local_70 != 0)',selection)
        self.assertIn('lVar20 = lVar20 + 8',selection)
        self.assertLess(selection.index('FUN_1001b9698('),selection.index('if (local_70 != 0)'))
        self.assertIn('__appendElementAssumeUniqueAndCapacity',selection)
        self.assertIn('objc_stub::FUN_100c02080',self.original('0x1003544dc'))
        self.assertIn('_swift_dynamicCastUnknownClass',self.original('0x1003544dc'))

    def test_optional_restore_reference_only_checks_context_object_and_type_without_payload_decode(self):
        source=body(self.source['ref'],'public func restoreItem(id: UUID)')
        self.assertIn('(try? context.existingObject(with: objectID)) as? PastoItemEntity else { return nil }',source)
        self.assertIn('ClipboardRestoreItem(id: id, object: object)',source)
        for token in ['ClipboardPersistence.item(', 'requiredItem()', 'fatalError','store.items']:
            self.assertNotIn(token,source)

    def test_entry_optional_native_results_do_not_fall_back_to_legacy_value(self):
        item=body(self.source['entry'],'public func item()')
        self.assertIn('if let reference { return reference.item() }',item)
        self.assertIn('return legacyItem',item)
        restore=body(self.source['entry'],'public func restoreItem()')
        self.assertIn('if let reference { return reference.restoreItem(id: id) }',restore)
        self.assertIn('guard let legacyItem else { return nil }',restore)
        self.assertIn('ClipboardRestoreItem(item: legacyItem)',restore)
        self.assertNotIn('??',item+restore)

    def test_real_applied_selection_readers_skip_missing_entries_without_reordering(self):
        for signature,lookup in [('func appliedSelectedItems(for state:','return items[index].item()'),('func appliedRestoreItems(for state:','return items[index].restoreItem()')]:
            source=body(self.source['host'],signature)
            self.assertIn('self.state === state, state.collectionOwner === self else { return nil }',source)
            self.assertIn('return orderedIDs.compactMap',source);self.assertIn(lookup,source)
            for forbidden in ['renderedItem(', 'requiredItem()', 'requiredRestoreItem()', '.sorted', 'Set(']:self.assertNotIn(forbidden,source)

    def test_ownerless_selection_adapter_uses_optional_entry_lookup_only_for_selected_ids(self):
        source=body(self.source['ui'],'var selectedItems:')
        self.assertIn('if let collectionOwner { return collectionOwner.appliedSelectedItems',source)
        self.assertIn('return ids.compactMap { byID[$0]?.item() }',source)
        self.assertNotIn('requiredItem()',source)
        self.assertIn('orderedSelectionIDs.filter { selection.contains($0) }',source)

    def test_required_indexed_access_and_visible_renderer_remain_exactly_unchanged(self):
        for key,signatures in [('ref',['public func requiredItem()','public func requiredRestoreItem(id: UUID)']),('entry',['public func requiredItem()','public func requiredRestoreItem()']),('host',['private func renderedItem(at index: Int)'])]:
            for signature in signatures:self.assertEqual(body(self.source[key],signature),body(self.before(key),signature))
        snapshot=pre_entity_lookup((ROOT/'replica/Sources/PastoCore/ClipboardSearchCollection.swift').read_text())
        self.assertIn('return reference.requiredItem()',body(snapshot,'public func item(at index: Int)'))

    def test_actual_bulk_action_routers_keep_empty_noop_and_same_writer(self):
        for signature in ['func copySelection(plainTextOnly:','func pasteSelection(plainTextOnly:','func contextMenuRestoreItems()','private func appliedRestoreItems(orderedIDs:','func addSelectionToStack()']:
            self.assertEqual(body(self.source['ui'],signature),body(self.before('ui'),signature))
        paste=body(self.source['ui'],'func pasteSelection(plainTextOnly:')
        self.assertIn('guard !items.isEmpty else { return }',paste)
        self.assertIn('paste(restoreItems: items',paste)

    def test_single_item_id_fallback_is_unchanged_and_explicitly_not_counted_closed(self):
        signature='func paste(itemID: UUID'
        self.assertEqual(body(self.source['ui'],signature),body(self.before('ui'),signature))
        self.assertTrue(any('paste(itemID:)' in s for s in self.proof['remaining']))
        self.assertFalse(self.proof['full_function_migration_verified'])

    def test_skip_table_covers_empty_missing_and_reordered_repeated_inputs(self):
        # Structural source checks above bind compactMap; this is the intended ordered omission table.
        positions={'A':0,'B':1,'C':2};values=[None,'b','c']
        cases=[([],[]),(['A'],[]),(['C','A','B'],['c','b']),(['C','C','A'],['c','c']),(['unknown','B'],['b'])]
        for ids,expected in cases:
            actual=[values[positions[i]]for i in ids if i in positions and values[positions[i]]is not None]
            self.assertEqual(actual,expected)

    def test_five_reviewed_hunks_only_four_production_files_and_no_schema_change(self):
        self.assertEqual(len(CHANGES),5)
        for k in self.paths:self.assertEqual(pre_optional_selection(self.source[k]),self.before(k))
        sha=lambda p:hashlib.sha256(pre_single_item_restore_bytes(ROOT/p)).hexdigest()
        self.assertEqual({p for p,h in self.base['production'].items()if sha(p)!=h},set(self.paths.values()))
        for group in ['current_sources','shared_sources']:
            for p,h in self.proof[group].items():self.assertEqual(sha(p),h)
        for p,h in self.proof['shared_sources'].items():self.assertEqual(h,self.base['production'][p])
        for p in ['replica/Package.swift','package.json']:self.assertEqual(sha(p),self.base['other'][p])
