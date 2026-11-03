"""Frozen group-menu input contracts; static source/Mach-O checks only."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from group_menu_input_scope_contract import CHANGES, pre_group_menu_input
from optional_selection_scope_contract import pre_optional_selection, pre_optional_selection_bytes

class GroupMenuInputContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-84'
        cls.proof=json.loads((cls.phase/'group-menu-input-contract.json').read_text())
        cls.base=json.loads((cls.phase/'baseline.json').read_text())
        cls.paths=dict(ui='replica/Sources/Pasto/UI/ReplicaUIController.swift',panel='replica/Sources/Pasto/UI/PanelViews.swift')
        cls.source={k:pre_optional_selection((ROOT/p).read_text())for k,p in cls.paths.items()}

    def before(self,key):return (self.phase/'before'/self.paths[key]).read_text()
    def original(self,address):
        r=next(r for r in self.proof['original_fragments']if r['address']==address)
        return original_fragment((ROOT/r['path']).read_text(),address[2:])

    def test_original_fragments_and_reused_real_repository_protocol_bound(self):
        self.assertEqual(len(self.proof['original_fragments']),18)
        for r in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        r=self.proof['reused_repository_protocol'];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
        prior=json.loads((ROOT/r['path']).read_text())
        self.assertTrue(prior['pointers']);self.assertTrue(prior['conformances'])

    def test_binary_twelve_real_branches_and_eight_array_handoff_words_bound(self):
        r=self.proof['binary'];raw=(ROOT/r['path']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),r['sha256'])
        self.assertEqual(len(self.proof['ARM_calls']),12)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);b=raw[pc-0x100000000:pc-0x100000000+4];self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little')
            self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+d*4,int(r['target'],16))
            self.assertEqual(r['kind'],'BL'if w&0x80000000 else'B')
        self.assertEqual(len(self.proof['ARM_words']),8)
        for r in self.proof['ARM_words']:
            pc=int(r['address'],16);b=raw[pc-0x100000000:pc-0x100000000+4]
            self.assertEqual(b.hex(),r['bytes']);self.assertEqual(int.from_bytes(b,'little'),int(r['word'],16))

    def test_original_menu_input_getter_uses_applier_before_menu_construction(self):
        caller=self.original('0x100075460')
        self.assertIn('ItemCollectionView::applier',caller)
        self.assertIn('FUN_100076128',caller)
        self.assertIn('FUN_10006e1f8()',self.original('0x100076128'))
        selection=self.original('0x10006e1f8')
        self.assertIn('ItemCollectionView::applier',selection)
        self.assertIn('FUN_1001b9698(&local_70,uVar19',selection)
        menu=self.original('0x10006f41c')
        self.assertIn('local_1e0 = param_3',menu)
        self.assertLess(menu.index('(*local_1e0)(&local_178'),menu.index('FUN_100075284(local_178'))

    def test_original_group_builder_and_callback_capture_same_array(self):
        builder=self.original('0x100075284')
        self.assertIn('local_58 = param_1',builder)
        self.assertIn('*(undefined **)(puVar5 + 0x20) = puVar3',builder)
        self.assertIn('*(code **)(puVar5 + 0x28) = FUN_100076320',builder)
        self.assertIn('*(code **)(puVar5 + 0x38) = FUN_100076328',builder)
        callback=self.original('0x10009e8a8')
        self.assertIn('local_80 = param_4',callback)
        self.assertIn('*(undefined **)(puVar9 + 0x20) = local_80',callback)
        self.assertIn('FUN_10009f240',callback)
        self.assertIn('*(undefined **)(puVar27 + 0x20) = local_80',callback)
        self.assertIn('FUN_10009f250',callback)

    def test_original_existing_group_delivers_frozen_array_and_target(self):
        route=self.original('0x10009f240')
        self.assertIn('unaff_x20 + 0x20',route);self.assertIn('unaff_x20 + 0x28',route)
        source=self.original('0x10009ee9c')
        self.assertIn('local_68[0] = param_3',source)
        self.assertIn('_swift_bridgeObjectRetain(param_3)',source)
        self.assertIn('(*param_1)(local_68,param_4)',source)
        self.assertIn('FUN_10009e5a4()',self.original('0x100076320'))
        self.assertIn('FUN_1003b9a78()',self.original('0x10009e5a4'))

    def test_original_create_group_delivers_same_frozen_array(self):
        self.assertIn('unaff_x20 + 0x20',self.original('0x10009f250'))
        source=self.original('0x10009ef40')
        self.assertIn('local_68[0] = param_3',source)
        self.assertIn('(*param_1)(local_68)',source)
        self.assertIn('FUN_10009e5fc()',self.original('0x100076328'))
        self.assertIn('FUN_1000538b4',self.original('0x10009e5fc'))
        create=self.original('0x1000538b4')
        self.assertLess(create.index('FUN_1003bb08c('),create.index('FUN_1003b9a78('))

    def test_actual_menu_captures_once_and_both_buttons_use_same_handles(self):
        source=body(self.source['panel'],'Menu("添加到 Pasto")')
        self.assertEqual(source.count('contextMenuRestoreItems()'),1)
        self.assertLess(source.index('let groupItems'),source.index('ForEach('))
        self.assertIn('state.assignItems(groupItems, to: board.id)',source)
        self.assertIn('createPinboard(assignSelection: true, selectionItems: groupItems)',source)
        for forbidden in ['assignSelection(to:', 'visibleItems','state.selection','selectedItems']:
            self.assertNotIn(forbidden,source)

    def test_current_snapshot_helper_reuses_exact_applied_owner_path_without_payload_decode(self):
        source=body(self.source['ui'],'func contextMenuRestoreItems()')
        self.assertEqual(source.strip(),'{\n        appliedRestoreItems()\n    }')
        for forbidden in ['visibleItems','store.items','resolvedItem()','requiredItem()']:self.assertNotIn(forbidden,source)
        signature='private func appliedRestoreItems(orderedIDs:'
        self.assertEqual(body(self.source['ui'],signature),body(self.before('ui'),signature))
        shared=pre_optional_selection((ROOT/'replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift').read_text())
        source=body(shared,'func appliedRestoreItems(for state: ReplicaUIState, orderedIDs:')
        self.assertIn('self.state === state, state.collectionOwner === self',source)
        self.assertIn('return orderedIDs.compactMap',source)
        self.assertIn('items[index].requiredRestoreItem()',source)

    def test_existing_group_holds_inputs_through_ordered_repository_call(self):
        source=body(self.source['ui'],'func assignItems(_ items:')
        self.assertIn('try withExtendedLifetime(items)',source)
        self.assertIn('store.assign(orderedIDs: items.map(\\.id), to: id)',source)
        for forbidden in ['visibleItems','selection','Set(','resolvedItem()']:self.assertNotIn(forbidden,source)
        self.assertEqual(body(self.source['ui'],'func assignSelection(to id:'),body(self.before('ui'),'func assignSelection(to id:'))

    def test_create_keeps_explicit_empty_input_distinct_from_legacy_nil_default(self):
        source=self.source['ui']
        self.assertIn('func createPinboard(assignSelection: Bool = false, selectionItems: [ClipboardRestoreItem]? = nil)',source)
        create=body(source,'func createPinboard(')
        self.assertIn('selectionItems?.map(\\.id) ?? state.visibleItems',create)
        self.assertNotIn('selectionItems?.isEmpty',create)
        self.assertLess(create.index('store.createPinboard(name: name)'),create.index('store.assign(orderedIDs: ids'))
        self.assertIn('try withExtendedLifetime(selectionItems)',create)
        old=body(self.before('ui'),'func createPinboard(')
        self.assertEqual(create[create.index('            // 0x100039618'):],old[old.index('            // 0x100039618'):])

    def test_six_exact_deltas_only_two_production_files_and_shared_core_unchanged(self):
        self.assertEqual(len(CHANGES),6)
        for k in self.paths:self.assertEqual(pre_group_menu_input(self.source[k]),self.before(k))
        sha=lambda p:hashlib.sha256(pre_optional_selection_bytes(ROOT/p)).hexdigest()
        self.assertEqual({p for p,h in self.base['production'].items()if sha(p)!=h},set(self.paths.values()))
        for group in ['current_sources','shared_sources']:
            for p,h in self.proof[group].items():self.assertEqual(sha(p),h)
        for p,h in self.proof['shared_sources'].items():self.assertEqual(h,self.base['production'][p])
        for p in ['replica/Package.swift','package.json']:self.assertEqual(sha(p),self.base['other'][p])

    def test_finite_handoff_does_not_claim_complete_original_selection_order_or_di(self):
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertFalse(self.proof['performance_measured'])
        self.assertTrue(any('0x108 getter order' in r for r in self.proof['remaining']))
        self.assertTrue(any('UUID adaptation' in r for r in self.proof['remaining']))
        self.assertTrue(any('SwiftUI dynamic menu' in r for r in self.proof['remaining']))
