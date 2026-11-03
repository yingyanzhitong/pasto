"""Current native group factory/validation lifecycle and compatibility consumers, source only."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts/tests'),str(ROOT/'scripts')]
from function_ledger import source_fragments
from native_tab_list_delivery_scope_contract import pre_native_tab_list_delivery, pre_native_tab_list_delivery_bytes
from native_group_read_projection_scope_contract import pre_native_group_read_projection
from test_offline_p0_contracts import body
from native_list_creation_lifecycle_scope_contract import CHANGES,pre_native_list_creation_lifecycle,pre_native_list_creation_lifecycle_bytes
class NativeListCreationLifecycle(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ph=ROOT/'.local/p0-repair/phase-162';cls.p=json.loads((cls.ph/'native-list-creation-contract.json').read_text());cls.base=json.loads((cls.ph/'baseline.json').read_text());cls.paths=list(cls.p['current_sources']);cls.sources={Path(p).stem:(ROOT/p).read_text()for p in cls.paths};cls.lists=cls.sources['ClipboardListPersistence'];cls.persistence=cls.sources['ClipboardPersistence'];cls.store=cls.sources['ClipboardStore'];cls.factory=body(cls.lists,'func insertPinboard(');cls.sync=body(cls.lists,'func synchronize(');cls.commit=body(cls.persistence,'func commit<T>(previous:');cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def order(self,s,tokens):
  positions=[s.index(t)for t in tokens];self.assertEqual(positions,sorted(positions))
 def test_eight_original_fragments_and_previous_native_validator_evidence_are_bound(self):
  self.assertEqual(len(self.p['original_fragments']),8)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for k in ['binary','decoder','prior_validator_proof','validator_source']:
   r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
 def test_complete_original_creator_machine_range_and39_calls_are_bound(self):
  m=self.p['machine'];a=int(m['start'],16);end=int(m['end'],16);self.assertEqual(hashlib.sha256(self.n['read'](a,end-a)).hexdigest(),m['sha256']);calls=[]
  for q in range(a,end,4):
   b=self.n['read'](q,4);w=int.from_bytes(b,'little')
   if w&0xfc000000==0x94000000:
    d=w&0x3ffffff;d=d-(1<<26)if d&(1<<25)else d;calls.append(dict(address=hex(q),bytes=b.hex(),target=hex(q+4*d)))
  self.assertEqual(calls,self.p['calls']);self.assertEqual(len(calls),39)
 def test_six_true_creator_selectors_exclude_metadata_date_and_index_writes(self):
  for r in self.p['selectors']:
   x,y=struct.unpack('<II',self.n['read'](int(r['stub'],16),8));self.assertEqual(x&0x9f00001f,0x90000001);self.assertEqual(y&0xffc003ff,0xf9400021);imm=((x>>5)&0x7ffff)*4+((x>>29)&3);imm=imm-(1<<21)if imm&(1<<20)else imm;p=(int(r['stub'],16)&~4095)+(imm<<12)+((y>>10)&0xfff)*8;self.assertEqual(hex(p),r['pointer']);v,c=self.n['reachable_pointer'](p);self.assertEqual(c,r['chain']);self.assertFalse(v>>63);dest=self.n['base']+(v&((1<<36)-1));self.assertEqual(hex(dest),r['selector_address']);self.assertEqual(self.n['read'](dest,120).split(b'\0')[0].decode(),r['selector'])
  self.assertEqual([r['selector']for r in self.p['selectors']],['initWithContext:','setIdentifier:','setName:','obtainPermanentIDsForObjects:error:','setRawAttributes:','setRawType:'])
 def test_current_native_factory_keeps_original_order_and_lets_actual_entities_own_lifecycle(self):
  self.order(self.factory,['let list = PastoListEntity(context: context)','list.setValue(identifier, forKey: "identifier")','list.setValue(name, forKey: "name")','nativeLists[identifier] = list','try? context.obtainPermanentIDs(for: [list])','let attributes = try? encodeAttributes()','list.setValue(attributes, forKey: "rawAttributes")','list.setValue(Int64(2), forKey: "rawType")','return (list, attributes)'])
  for t in ['Date()', 'ListMetadataEntity','forKey: "metadata"','forKey: "createdAt"','forKey: "index"','validateForInsert','context.save','context.fetch']:self.assertNotIn(t,self.factory)
  self.assertNotIn('index: Int64',self.lists[self.lists.index('func insertPinboard('):self.lists.index('func insertPinboard(')+170])
 def test_model_typed_registration_and_real_awake_validator_are_still_the_actual_path(self):
  for cls,entity in [('PastoListEntity','ListEntity'),('PastoListMetadataEntity','ListMetadataEntity')]:
   self.assertIn('model.entitiesByName["'+entity+'"]!.managedObjectClassName = NSStringFromClass('+cls+'.self)',self.persistence)
  s=(ROOT/self.p['validator_source']['path']).read_text();v=body(s,'override func validateForInsert()');self.assertIn('"list:" + String._unconditionallyBridgeFromObjectiveC',v);self.assertIn('let nextIndex = lastIndex + 1',v);self.assertIn('metadata.setValue(self, forKey: "list")',v);self.assertIn('try super.validateForInsert()',v)
  for sig in ['class PastoListEntity:','class PastoListMetadataEntity:']:
   a=body(body(s,sig),'override func awakeFromInsert()');self.order(a,['super.awakeFromInsert()','setPrimitiveValue(Date(), forKey: "createdAt")'])
 def test_sync_skips_only_same_created_object_and_retains_strict_old_metadata_guard(self):
  self.order(self.sync,['if nativeLists[identifier] === list { continue }','set(board.rawAttributes, key: "rawAttributes", on: list)','guard let metadata = list.value(forKey: "metadata")','throw CocoaError(.fileReadCorruptFile)','set(Int64(board.sortOrder), key: "index", on: metadata)']);self.assertEqual(self.sync.count('nativeLists['),1);self.assertNotIn('try? list',self.sync)
 def test_after_save_projection_preserves_native_index_and_canonical_value_sort_without_fetch_save_or_validation(self):
  p=body(self.lists,'func projectNativePinboards(');self.order(p,['guard !nativeLists.isEmpty else { return pinboards }','nativeLists[board.id.uuidString]','list.value(forKey: "metadata")','metadata.value(forKey: "index")','value.sortOrder = index.intValue','return value','}.sorted {']);self.assertIn('$0.id.uuidString < $1.id.uuidString',p)
  for t in ['context.fetch','context.save','validateForInsert','Date()','throw','try?','setValue']:self.assertNotIn(t,p)
  self.order(self.commit,['var outcome = try operation(transaction)','if context.hasChanges','try context.save()','context.rollback()','throw error','viewHistoryToken =','outcome.state.pinboards = transaction.repository.lists.projectNativePinboards(outcome.state.pinboards)','return outcome']);self.assertEqual(self.commit.count('try context.save()'),1)
 def test_store_retains_created_target_and_projects_the_returned_board_from_that_object(self):
  f=body(self.store,'private func insertPinboard(name:');self.order(f,['let result: (board: Pinboard, target: ClipboardPinboardTarget) = try mutateInTransaction','let id = UUID()','transaction.repository.lists.insertPinboard(identifier: id.uuidString','name: name) {','state.pinboards.append(board)','return (board, ClipboardPinboardTarget(id: id, object: created.object))','var board = result.board','result.target.nativeObject.value(forKey: "metadata")','board.sortOrder = index.intValue','return (board, result.target)']);self.assertNotIn('list(identifier:',f);self.assertNotIn('context.fetch',f);self.assertEqual(f.count('UUID()'),1);self.assertNotIn('.max()',f);self.assertIn('sortOrder: 0,',f)
  old=body((self.ph/'before/replica/Sources/PastoCore/ClipboardStore.swift').read_text(),'private func insertPinboard(name:');self.assertEqual(f[f.index('let code: UInt64?'):f.index('let id = UUID()')],old[old.index('let code: UInt64?'):old.index('let id = UUID()')])
 def test_markers_are_per_repository_transaction_not_shared_static_or_persistent_state(self):
  self.assertIn('private var nativeLists: [String: NSManagedObject] = [:]',self.lists);self.assertNotIn('static var nativeLists',self.lists);repo=body(self.persistence,'final class ManagedRepository');self.assertIn('lists = ClipboardListPersistence(context: context)',body(repo,'init(context:'));self.assertIn('withExtendedLifetime(transaction)',self.commit)
  store=body(self.store,'private func mutateInTransaction<T>(historyAction:');self.order(store,['try persistence.commit(previous: remote','diskRevision = try revision()','publish(state)']);self.assertNotIn('catch',store)
 def test_save_failure_diagnostics_rollback_and_original_error_are_unchanged(self):
  current=body(body(self.commit,'if context.hasChanges'),'try context.save() }\n                    } catch');before=body(body(body((self.ph/'before/replica/Sources/PastoCore/ClipboardPersistence.swift').read_text(),'func commit<T>(previous:'),'if context.hasChanges'),'try context.save() }\n                    } catch');self.assertEqual(current,before);self.order(current,['context.insertedObjects','validateForInsert()','validateForUpdate()','context.rollback()','throw error']);self.assertNotIn('projectNativePinboards',current)
 def test_thirteen_legacy_and_neighbor_methods_stay_byte_identical(self):
  self.assertEqual(len(self.p['unchanged_methods']),13)
  for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body(pre_native_group_read_projection((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256']);self.assertEqual(body(pre_native_group_read_projection((ROOT/r['path']).read_text()),r['symbol']),body((self.ph/'before'/r['path']).read_text(),r['symbol']))
 def test_seven_exact_deltas_reverse247_files_and_no_function_runtime_or_unknown_closure_is_claimed(self):
  self.assertEqual(len(CHANGES),7);changed=[]
  for p,h in self.base['production'].items():
   if hashlib.sha256(pre_native_tab_list_delivery_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_native_list_creation_lifecycle_bytes(ROOT/p)).hexdigest(),h)
  self.assertEqual(set(changed),set(self.paths));self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertEqual(self.p['new_difference_records'],0);self.assertEqual(self.p['additional_repaired_contracts'],1)
if __name__=='__main__':unittest.main()
