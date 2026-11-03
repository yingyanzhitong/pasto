"""Real native single-item paste routes; source/Mach-O checks, no framework execution."""
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
from single_item_restore_scope_contract import CHANGES,pre_single_item_restore
from native_title_scope_contract import pre_native_title, pre_native_title_bytes

class SingleItemRestoreContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-86'
        cls.proof=json.loads((cls.phase/'single-item-restore-contract.json').read_text())
        cls.base=json.loads((cls.phase/'baseline.json').read_text())
        cls.path='replica/Sources/Pasto/UI/ReplicaUIController.swift'
        cls.ui=pre_native_title((ROOT/cls.path).read_text());cls.before=(cls.phase/'before'/cls.path).read_text()

    def original(self,a):
        r=next(r for r in self.proof['original_fragments']if r['address']==a)
        return original_fragment((ROOT/r['path']).read_text(),a[2:])

    def test_six_original_fragments_and_reused_optional_chain_bound(self):
        self.assertEqual(len(self.proof['original_fragments']),6)
        for r in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['reused_optional_provider'],self.proof['free_app_adapter']]:
            self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])

    def test_seven_actual_machine_code_call_targets_bound(self):
        raw=(ROOT/self.proof['binary']['path']).read_bytes();self.assertEqual(len(self.proof['ARM_calls']),7)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);b=raw[pc-0x100000000:pc-0x100000000+4];self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little')
            self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+d*4,int(r['target'],16))

    def test_original_double_click_has_one_optional_applier_lookup_and_no_id_retry(self):
        source=self.original('0x100075a6c')
        self.assertIn('if (1 < (long)IVar4)',source)
        self.assertEqual(source.count('FUN_1001b9698('),1)
        self.assertIn('FUN_1001b9698(&local_a0,param_1',source)
        self.assertIn('if (local_a0 != 0)',source)
        self.assertIn('FUN_100066068(puVar10,uVar14,0)',source)
        self.assertNotIn('objc_stub::identifier(',source)
        self.assertLess(source.index('FUN_1001b9698('),source.index('FUN_100066068('))

    def test_original_quick_paste_keeps_first_selection_after_optional_lookup(self):
        source=self.original('0x10006c60c')
        self.assertEqual(source.count('FUN_1001b9698('),1)
        self.assertIn('if (local_b0 != 0)',source)
        self.assertLess(source.index('FUN_1001b9698('),source.index('FUN_100066068('))
        self.assertLess(source.index('FUN_100066068('),source.index('FUN_100228c78(0,0,1)'))
        self.assertIn('uVar14 = 1',source)

    def test_original_empty_sequence_paid_branch_is_excluded_not_called_equivalent(self):
        source=self.original('0x100066068')
        self.assertIn('FUN_10031c4c4(',source)
        self.assertIn('FUN_100064afc(1,0,0)',source)
        self.assertIn('Swift::Sequence::_allSatisfy()',self.original('0x10031c4c4'))
        note=(ROOT/self.proof['free_app_adapter']['path']).read_text()
        self.assertIn('License',note);self.assertIn('Pasto 根据用户要求提供免费独立软件',note)
        native=body(self.ui,'func paste(itemID: UUID')
        self.assertIn('else { return false }',native)
        for token in ['Paywall','License','NSApp.activate','hidePanel()']:self.assertNotIn(token,native)

    def test_native_single_item_entry_is_strictly_applied_and_has_no_id_writer_retry(self):
        source=body(self.ui,'func paste(itemID: UUID')
        self.assertIn('guard let input = appliedRestoreItems(orderedIDs: [itemID]).first else { return false }',source)
        self.assertIn('return paste(restoreItems: [input], plainTextOnly: plainTextOnly)',source)
        self.assertNotIn('paste(ids:',source)
        self.assertNotIn('store.items',source)
        self.assertNotIn('ClipboardRestoreItem(item:',source)

    def test_value_based_legacy_entry_preserves_the_previous_lookup_fallback_body(self):
        legacy=body(self.ui,'func paste(item: ClipboardItem')
        old=body(self.before,'func paste(itemID: UUID').replace('itemID','item.id')
        legacy=legacy.replace('        // Value-based legacy views retain their ID writer compatibility path.\n','',1)
        self.assertEqual(legacy,old)
        self.assertIn('return paste(ids: [item.id], plainTextOnly: plainTextOnly)',legacy)

    def test_native_mouse_and_numeric_actual_producers_still_call_strict_id_entry(self):
        host=(ROOT/'replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift').read_text()
        mouse=body(host,'override func mouseDown(with event: NSEvent)')
        self.assertIn('paste(itemID: current[index].id, plainTextOnly:',mouse)
        quick=body(self.ui,'func performQuickPaste(_ action:')
        self.assertIn('paste(itemID: items[action.index].id, plainTextOnly:',quick)
        self.assertIn('state.selectFirstAppliedItem(items: appliedItems)',quick)
        self.assertEqual(quick,body(self.before,'func performQuickPaste(_ action:'))
        # These are the only production callers of the strict entry.
        callers=[]
        for p in (ROOT/'replica/Sources').rglob('*.swift'):
            for line in p.read_text().splitlines():
                if 'paste(itemID:' in line and not line.lstrip().startswith('func paste('):callers.append(str(p.relative_to(ROOT)))
        self.assertCountEqual(callers,['replica/Sources/Pasto/UI/ReplicaUIController.swift','replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift'])

    def test_value_card_fallback_still_uses_legacy_entry(self):
        panel=(ROOT/'replica/Sources/Pasto/UI/PanelViews.swift').read_text()
        self.assertIn('state.controller?.paste(item: item, plainTextOnly:',panel)
        self.assertIn('ReplicaCardTapHandlers(enabled: !nativeInteractions',panel)

    def test_owner_window_check_and_actual_restore_service_are_unchanged(self):
        for signature in ['private func appliedRestoreItems(orderedIDs:','private func paste(restoreItems:','func paste(ids: [UUID]']:
            self.assertEqual(body(self.ui,signature),body(self.before,signature))
        app=(ROOT/'replica/Sources/Pasto/AppMain.swift').read_text()
        self.assertIn('ui.pasteRestoreItemsHandler =',app)
        self.assertIn('forceDirect: forceDirect, restoreItems: items)',app)

    def test_bulk_stack_and_context_menu_actions_are_not_rewritten(self):
        for signature in ['func pasteSelection(plainTextOnly:','func pasteStackItem(id:','func contextMenuRestoreItems()','func addSelectionToStack()']:
            self.assertEqual(body(self.ui,signature),body(self.before,signature))

    def test_one_reviewed_hunk_only_one_production_file_and_six_shared_files_unchanged(self):
        self.assertEqual(len(CHANGES),1);self.assertEqual(pre_single_item_restore(self.ui),self.before)
        sha=lambda p:hashlib.sha256(pre_native_title_bytes(ROOT/p)).hexdigest()
        self.assertEqual({p for p,h in self.base['production'].items()if sha(p)!=h},{self.path})
        self.assertEqual(len(self.proof['shared_sources']),6)
        for group in ['current_sources','shared_sources']:
            for p,h in self.proof[group].items():self.assertEqual(sha(p),h)
        for p,h in self.proof['shared_sources'].items():self.assertEqual(h,self.base['production'][p])
        for p in ['replica/Package.swift','package.json']:self.assertEqual(sha(p),self.base['other'][p])

    def test_no_extra_function_count_or_whole_native_lifecycle_claim(self):
        self.assertEqual(self.proof['new_difference_records'],0)
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertFalse(self.proof['runtime_executed'])
        self.assertTrue(any('value-based paste(item:)' in r for r in self.proof['remaining']))
        self.assertTrue(any('mutation input identity' in r for r in self.proof['remaining']))
