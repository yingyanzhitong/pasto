"""Live native List menu producer; Python source/Mach-O only."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from preview_group_menu_scope_contract import pre_preview_group_menu,pre_preview_group_menu_bytes
from test_offline_p0_contracts import body
from pinboard_collection_scope_contract import CHANGES,pre_pinboard_collection,pre_pinboard_collection_bytes

class PinboardCollectionContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-107';cls.proof=json.loads((cls.phase/'pinboard-collection-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.src={Path(p).stem:pre_preview_group_menu((ROOT/p).read_text())for p in cls.proof['current_sources']};s=cls.src['ClipboardSearchCollection'];cls.native=s[s.index('public final class ClipboardPinboardCollection'):s.index('/// 354800/354f90')];cls.search=s[s.index('public final class ClipboardSearchCollection'):s.index('/// The group menu')];ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],ns);cls.ns=ns
    def order(self,s,tokens):
        cursor=0
        for t in tokens:cursor=s.index(t,cursor)+len(t)
    def test_twenty_five_original_fragments_binary_and_prior_native_inputs_bound(self):
        self.assertEqual(len(self.proof['original_fragments']),25)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['decoder']]+self.proof['reused_evidence']:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_eighteen_actual_branches_bind_menu_to_List_factory_and_FRC(self):
        self.assertEqual(len(self.proof['ARM_calls']),18)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);b=self.ns['read'](pc,4);self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+d*4,int(r['target'],16))
    def test_real_List_repository_reading_slot_is_plus18_not_Item_request(self):
        self.assertEqual([(r['address'],r['target'])for r in self.proof['pointers']],[('0x100eccd70','0x100c42f30'),('0x100eccd88','0x10036805c')])
        for r in self.proof['pointers']:
            a=int(r['address'],16);v,chain=self.ns['reachable_pointer'](a);self.assertEqual(chain,r['chain']);self.assertEqual(self.ns['read'](a,8).hex(),r['bytes']);self.assertEqual(self.ns['base']+(v&((1<<36)-1)),int(r['target'],16))
    def test_witness_group_type_and_ascending_real_instructions_bound(self):
        self.assertEqual(len(self.proof['ARM_words']),4)
        for r in self.proof['ARM_words']:self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes']);self.assertEqual(int.from_bytes(bytes.fromhex(r['bytes']),'little'),int(r['word'],16))
    def test_sort_key_and_predicate_decode_from_real_MOV_immediates(self):
        self.assertEqual([r['value']for r in self.proof['decoded_strings']],['metadata.index','rawType = %i'])
        for r in self.proof['decoded_strings']:
            regs={}
            for row in r['ARM_words']:
                b=self.ns['read'](int(row['address'],16),4);self.assertEqual(b.hex(),row['bytes']);w=int.from_bytes(b,'little');reg=w&31;shift=((w>>21)&3)*16;imm=(w>>5)&0xffff
                if w&0xff800000==0xd2800000:regs[reg]=imm<<shift
                else:self.assertEqual(w&0xff800000,0xf2800000);regs[reg]=(regs[reg]&~(0xffff<<shift))|(imm<<shift)
            self.assertEqual(hex(regs[0]),r['first_word']);self.assertEqual(hex(regs[1]),r['second_word']);self.assertEqual((struct.pack('<Q',regs[0])+struct.pack('<Q',regs[1]))[:(regs[1]>>56)&15].decode(),r['value'])
    def test_native_List_request_uses_original_group_defaults(self):
        s=body(self.src['ClipboardListPersistence'],'func pinboardRequest(');self.order(s,['NSFetchRequest<NSManagedObject>(entityName: "ListEntity")','NSSortDescriptor(key: "metadata.index", ascending: true)','NSPredicate(format: "rawType == %d", 2)','request.fetchBatchSize = 20','return request'])
        for t in ['Item"','displayOrderInPinboard','fetchLimit','fetchOffset','UUID','isDeleted']:self.assertNotIn(t,s)
    def test_persistence_constructs_live_collection_on_same_context(self):
        s=body(self.src['ClipboardPersistence'],'func makePinboardCollection(');self.order(s,['context.performAndWait','ClipboardPinboardCollection(context: context, request: lists.pinboardRequest())'])
        for t in ['context.reset','lists.list(identifier','state.pinboards','try?']:self.assertNotIn(t,s)
    def test_store_facade_passes_collection_not_value_pinboards(self):
        s=body(self.src['ClipboardStore'],'public func makePinboardCollection(');self.assertIn('persistence.makePinboardCollection()',s);self.assertNotIn('pinboards',s.lower())
    def test_UI_owns_source_lazily_and_reads_current_snapshot_on_demand(self):
        s=self.src['ReplicaUIController'];self.assertIn('private lazy var pinboardMenuCollection = store.makePinboardCollection()',s);self.assertEqual(body(s,'func pinboardMenuTargets()').strip(),'{\n        pinboardMenuCollection.value\n    }');self.assertEqual(s.count('store.makePinboardCollection()'),1)
    def test_group_menu_no_longer_reconstructs_native_targets_from_UUID_values(self):
        s=body(self.src['PanelViews'],'@ViewBuilder private var contextMenu:');self.order(s,['let groupItems = state.controller?.contextMenuRestoreItems()','ForEach(state.pinboardMenuTargets(), id: \\.id)','Button(target.name) { state.assignItems(groupItems, to: target) }','createPinboard(assignSelection: true, selectionItems: groupItems)'])
        for t in ['state.store.pinboards','pinboardAssignmentTarget','to: board.id']:self.assertNotIn(t,s)
    def test_menu_target_name_reads_current_native_List(self):
        s=self.src['ClipboardListPersistence'];self.assertIn('public var name: String { nativeObject.value(forKey: "name") as? String ?? "" }',s)
    def test_obsolete_single_UUID_target_factories_removed(self):
        for key in ['ClipboardPersistence','ClipboardStore','PanelViews']:self.assertNotIn('pinboardAssignmentTarget(',self.src[key])
    def test_FRC_is_typed_for_List_objects_and_shared_delegate_is_per_instance(self):
        s=self.native;self.assertIn('NSFetchedResultsController<NSManagedObject>',s);self.assertIn('request: NSFetchRequest<NSManagedObject>',s);self.assertIn('let delegate = ClipboardSearchDifferenceDelegate(ids: initial)',s);self.assertIn('differenceDelegate = delegate',s);self.assertNotIn('PastoItemEntity',s)
    def test_initial_fetch_and_delegate_and_observer_order_reuses_original_generic_contract(self):
        s=body(self.native,'init(context:');self.order(s,['NSFetchedResultsController(fetchRequest: request','sectionNameKeyPath: nil, cacheName: nil','try controller.performFetch()','catch { fatalError','let initial = initialObjectIDs()','let delegate = ClipboardSearchDifferenceDelegate','controller.delegate = delegate','pending = (initial, [])','flushPending()','objectsObservation = NotificationCenter.default','.NSManagedObjectContextObjectsDidChange, object: context'])
    def test_clean_context_ID_optimization_and_fallback_is_the_existing_bound_method(self):
        s=body(self.native,'private func initialObjectIDs()');self.order(s,['guard !context.hasChanges','let ids = fetchInitialObjectIDs()','controller.sections?.first?.numberOfObjects','ids.count == count','ids.first == fetchedObjectID(at: 0)','ids.last == fetchedObjectID(at: ids.count - 1)','return (controller.fetchedObjects ?? []).map(\\.objectID)','return ids']);self.assertEqual(s,body(self.search,'private func initialObjectIDs()'))
    def test_ID_query_copies_shape_only_and_error_empty_candidate_keeps_FRC_fallback(self):
        s=body(self.native,'private func fetchInitialObjectIDs()');self.order(s,['controller.fetchRequest.entityName','NSFetchRequest<NSManagedObjectID>(entityName: entityName)','request.predicate = controller.fetchRequest.predicate','request.sortDescriptors = controller.fetchRequest.sortDescriptors','request.resultType = .managedObjectIDResultType','return (try? context.fetch(request)) ?? []']);self.assertNotIn('fetchLimit',s)
    def test_native_value_keeps_snapshot_order_and_optional_live_entity_lookup(self):
        s=body(self.native,'public var value:');self.order(s,['subject.value.identifiers.compactMap','context.existingObject(with: objectID)','object.entity.name == "ListEntity"','object.value(forKey: "identifier")','UUID(uuidString: identifier)','ClipboardPinboardTarget(id: id, object: object)'])
        for t in ['sorted','Set(','isDeleted','store.','ClipboardItem','decode(']:self.assertNotIn(t,s)
    def test_pending_changes_union_and_schedule_first_delivery_only(self):
        s=body(self.native,'private func receive(');self.order(s,['let schedulesDelivery = pending == nil','pending = (ids, (pending?.updated ?? []).union(updated))','if schedulesDelivery','context.perform { [weak self]','self?.flushPending()'])
    def test_pending_is_cleared_before_current_order_and_subject_delivery(self):
        s=body(self.native,'private func flushPending()');self.order(s,['guard let value = pending','pending = nil','objectIDs = value.ids','subject.send(Snapshot(identifiers: value.ids, updatedIdentifiers: value.updated))'])
    def test_object_update_and_refresh_use_live_or_pending_membership_only(self):
        s=body(self.native,'private func objectsDidChange(');self.order(s,['let ids = pending?.ids ?? objectIDs','Set(ids)','NSUpdatedObjectsKey','NSRefreshedObjectsKey','updated.union(refreshed)','intersection(membership)','receive(ids: ids, updated: changed)']);self.assertNotIn('removeDuplicates',s)
    def test_five_general_ID_methods_and_whole_difference_delegate_unchanged(self):
        self.assertEqual(len(self.proof['reused_methods']),5)
        for r in self.proof['reused_methods']:
            s=body(self.native,r['symbol']);self.assertEqual(s,body(self.search,r['symbol']));self.assertEqual(hashlib.sha256(s.encode()).hexdigest(),r['sha256'])
        s=self.src['ClipboardSearchCollection'];d=s[s.index('/// 354800/354f90'):];p='replica/Sources/PastoCore/ClipboardSearchCollection.swift';old=(self.phase/'before'/p).read_text();self.assertEqual(d,old[old.index('/// 354800/354f90'):]);self.assertEqual(hashlib.sha256(d.encode()).hexdigest(),self.proof['unchanged_delegate_sha256'])
    def test_eight_surgical_hunks_and_all_production_files_reverse_exactly(self):
        self.assertEqual(len(CHANGES),8);self.assertEqual({r[0]for r in CHANGES},set(self.proof['current_sources']));files={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()};self.assertEqual(files,set(self.base['production']))
        for p,h in self.base['production'].items():self.assertEqual(hashlib.sha256(pre_pinboard_collection_bytes(ROOT/p)).hexdigest(),h)
        for p,h in self.proof['current_sources'].items():self.assertEqual(hashlib.sha256(pre_preview_group_menu_bytes(ROOT/p)).hexdigest(),h);self.assertEqual(pre_pinboard_collection(pre_pinboard_collection((ROOT/p).read_text())),(self.phase/'before'/p).read_text())
    def test_shared_payload_and_entity_helpers_unchanged(self):
        self.assertEqual(len(self.proof['shared_sources']),4)
        for p,h in self.proof['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_preview_group_menu_bytes(ROOT/p)).hexdigest(),h);self.assertEqual(h,self.base['production'][p])
    def test_original_preview_shared_builder_is_known_but_not_falsely_claimed_migrated(self):
        self.assertIn('Original preview header07c378 also installs07637c',self.proof['correction']);self.assertFalse(self.proof['full_function_migration_verified']);self.assertFalse(self.proof['runtime_executed']);self.assertEqual(self.proof['new_difference_records'],1);self.assertEqual(len(self.proof['remaining']),4);self.assertEqual(self.proof['contracts'][0]['function_id'],'Paste:0x10009e510')

if __name__=='__main__':unittest.main()
