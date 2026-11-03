"""P1 card/Stack preview retains supplied object before optional ID retry; static only."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from supplied_preview_input_scope_contract import CHANGES,pre_supplied_preview_input
from native_preview_identity_scope_contract import pre_native_preview_identity
class SuppliedPreviewInputContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-135';cls.p=json.loads((cls.phase/'supplied-preview-input-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.s=pre_native_preview_identity((ROOT/cls.p['current_source']).read_text());cls.show=body(cls.s,'func showPreview(item: ClipboardItem, input:');cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
    def order(self,s,seq):
        i=0
        for t in seq:i=s.index(t,i)+len(t)
    def original(self,address):
        r=next(r for r in self.p['original_fragments']if r['address']==address);return original_fragment((ROOT/r['path']).read_text(),address[2:])
    def test_six_original_fragments_and_frozen_two_prior_evidences_bound(self):
        self.assertEqual(len(self.p['original_fragments']),6)
        for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.p['binary'],self.p['decoder']]+self.p['prior_evidence']:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_original_same_input_store_and_detach_field_words_still_bound(self):
        for r in self.p['ARM_words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
        field=self.p['item_ivar'];self.assertEqual(self.n['read'](int(field['address'],16),8).hex(),field['bytes']);self.assertEqual(field['offset'],0x48)
    def test_actual_collection_index_to_popover_calls_bound_as_distinct_producer(self):
        for r in self.p['ARM_calls']:
            pc=int(r['address'],16);raw=self.n['read'](pc,4);self.assertEqual(raw.hex(),r['bytes']);w=int.from_bytes(raw,'little');d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+4*d,int(r['target'],16))
    def test_original_show_and_detach_forward_same_entity_not_identifier_refetch(self):
        s=self.original('0x10002964c');self.order(s,['PreviewPopover::item) = param_5','FUN_10008747c()','FUN_1003c25dc(param_5'])
        d=self.original('0x100029a80');self.order(d,['PreviewPopover::item)','FUN_1003c25dc(lVar7'])
        for t in ['existingObjectWithID','FUN_10006bb3c','FUN_1001b9698']:self.assertNotIn(t,s)
    def test_current_supplied_input_short_circuits_collection_bridge_by_optional_pattern(self):
        self.assertIn('if case nil = input, showCollectionPreview(itemID: item.id) { return }',self.show)
        self.assertNotIn('if showCollectionPreview(itemID: item.id) { return }',self.show)
        self.assertEqual(self.show.count('showCollectionPreview('),1)
    def test_existing_content_constructor_uses_same_supplied_input_in_both_presentations(self):
        self.order(self.show,['let input = input ?? appliedRestoreItems(orderedIDs: [item.id]).first','?? state.stackRestoreItem(for: item.id) ?? ClipboardRestoreItem(item: item)','let anchor: NSView?','input: input,','contentView: makePreviewContent(for: input)','let content = makePreviewContent(for: input)'])
    def test_nil_input_index_resolution_retry_and_keyboard_producer_are_unchanged(self):
        selection=body(self.s,'private func previewSelection()');self.assertIn('showCollectionPreview(itemID: id)',selection)
        route=body(self.s,'private func showCollectionPreview(');self.order(route,['collection.appliedItems(for: state)','items.firstIndex(where: { $0.id == itemID })','collection.previewItem(at: index)'])
        host=(ROOT/'replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift').read_text();preview=body(host,'func previewItem(at index:');self.assertIn('self?.previewItem(at: index, present: present)',preview)
    def test_real_card_and_stack_menu_producers_supply_retained_input(self):
        card=(ROOT/'replica/Sources/Pasto/UI/PanelViews.swift').read_text();stack=(ROOT/'replica/Sources/Pasto/UI/AuxiliaryViews.swift').read_text()
        self.assertIn('showPreview(item: item, input: titleInput)',card);self.assertIn('showPreview(item: input.resolvedItem(), input: input)',stack)
        self.assertIn('state.controller?.copy(input: input, plainTextOnly: false)',stack)
    def test_single_line_change_leaves_entire_remaining_show_body_literal(self):
        old=body((self.phase/'before'/self.p['current_source']).read_text(),'func showPreview(item: ClipboardItem, input:');self.assertEqual(pre_supplied_preview_input(self.show),old)
        self.assertEqual(len(CHANGES),1);self.assertEqual(self.show.count('case nil = input'),1)
    def test_six_reused_methods_and_six_shared_sources_remain_current_unchanged(self):
        self.assertEqual(len(self.p['unchanged_methods']),6);self.assertEqual(len(self.p['unchanged_sources']),6)
        for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body(pre_native_preview_identity((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
        for p,h in self.p['unchanged_sources'].items():self.assertEqual(hashlib.sha256(pre_native_preview_identity((ROOT/p).read_text()).encode()if p.endswith('.swift')else(ROOT/p).read_bytes()).hexdigest(),h)
    def test_exact_inverse_preserves_all247_user_source_snapshots(self):
        diff=[]
        for p,h in self.base['production'].items():
            b=(ROOT/p).read_bytes();b=pre_native_preview_identity(b.decode()).encode()if p.endswith('.swift')else b
            if hashlib.sha256(b).hexdigest()!=h:diff.append(p)
            b=pre_supplied_preview_input(b.decode()).encode()if p.endswith('.swift')else b;self.assertEqual(hashlib.sha256(b).hexdigest(),h)
        self.assertEqual(diff,[self.p['current_source']]);self.assertEqual(hashlib.sha256(self.s.encode()).hexdigest(),self.p['current_source_sha256'])
    def test_full_registry_and_unknowns_not_silently_closed_by_guard(self):
        self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertEqual(len(self.p['remaining']),4);self.assertIn('UUID identity',self.p['remaining'][0]);self.assertIn('Two unknown',self.p['remaining'][3])
if __name__=='__main__':unittest.main()
