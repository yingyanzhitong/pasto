"""Primary-model and value-copy provenance; corrected finite search callback branches."""
import hashlib
import json
import plistlib
import struct
import subprocess
import unittest
from collections import Counter

from test_offline_p0_contracts import ROOT, body
from test_p0_p1_review_round2 import digest, fragment


class P0P1ReviewRound17(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((ROOT/'reports/replica/p0-p1-review-round17.json').read_text())
        cls.prior=json.loads((ROOT/'reports/replica/p0-p1-review-round16.json').read_text())
        cls.rows={x['function_id']:x for x in cls.report['records']}
        cls.proof=json.loads((ROOT/cls.report['static_proof']['path']).read_text())
        cls.binary=(ROOT/cls.proof['binary_path']).read_bytes()
        cls.index={x['address']:x for x in json.loads((ROOT/'reports/Paste/function-index.json').read_text())}

    def native(self,a):return fragment(a,self.index[a]['file'])
    def offset(self,a):
        for s in self.proof['segments']:
            if s['vmaddr']<=a<s['vmaddr']+s['filesize']:return s['fileoff']+a-s['vmaddr']
        self.fail(hex(a))
    def word(self,a):return struct.unpack_from('<I',self.binary,self.offset(a))[0]
    def pointer(self,a):return 0x100000000+(struct.unpack_from('<Q',self.binary,self.offset(a))[0]&((1<<36)-1))
    def relative(self,a):return a+struct.unpack_from('<i',self.binary,self.offset(a))[0]
    def string(self,a):
        o=self.offset(a);return self.binary[o:self.binary.index(b'\0',o)].decode()
    def adrp_add(self,a):
        adrp,add=self.word(a),self.word(a+4)
        self.assertEqual(adrp&0x9f000000,0x90000000);self.assertEqual(add&0xffc00000,0x91000000)
        imm=((adrp>>5)&0x7ffff)*4+((adrp>>29)&3)
        if imm&(1<<20):imm-=1<<21
        self.assertEqual(adrp&31,(add>>5)&31)
        return (a&~4095)+(imm<<12)+((add>>10)&4095)

    def test_646_scope_fixed_and_old_reducer_schema_correction_is_separate_from_new_progress(self):
        old={x['function_id']:x for x in self.prior['records']};changed=set(self.report['round_delta']['reviewed_function_ids'])
        self.assertEqual(set(old),set(self.rows));self.assertEqual(len(self.rows),646)
        self.assertEqual(len(changed),12);self.assertEqual(self.report['round_delta']['scope_added'],0)
        self.assertEqual(self.report['scope_manifest_sha256'],self.prior['scope_manifest_sha256'])
        for fid in old:
            if fid not in changed:self.assertEqual(self.rows[fid],old[fid])
            elif fid!='Paste:0x10036fa2c':self.assertEqual(old[fid]['status'],'unclosed')
        self.assertEqual(self.rows['Paste:0x10036fa2c']['historical_contract_correction'],old['Paste:0x10036fa2c']['contract'])
        self.assertEqual(self.report['round_delta']['newly_resolved'],5)
        self.assertFalse(any(x['full_function_migration_verified'] for x in self.rows.values()))
        self.assertIsNone(self.report['full_priority_completion_percent'])

    def test_all_new_fragments_current_references_sdk_and_primary_resource_hashes_are_verified(self):
        for p,h in self.report['source_inputs'].items():self.assertEqual(digest(p),h,p)
        self.assertEqual(digest(self.report['static_proof']['path']),self.report['static_proof']['sha256'])
        self.assertEqual(hashlib.sha256(self.binary).hexdigest(),self.proof['binary_sha256'])
        for fid in self.report['round_delta']['reviewed_function_ids']:
            row=self.rows[fid]
            for ref in [dict(row['original'],function_id=fid)]+row.get('supporting_original_fragments',[]):
                a=ref.get('address') or ref['function_id'].split(':')[1]
                self.assertEqual(hashlib.sha256(fragment(a,ref['path']).encode()).hexdigest(),ref['sha256'])
            for ref in row['current_references']:
                self.assertEqual(digest(ref['path']),ref['sha256']);self.assertIn(ref['symbol'],(ROOT/ref['path']).read_text())
            for ref in row.get('sdk_evidence',[]):
                self.assertEqual(digest(ref['path']),ref['sha256'])
                for symbol in ref['symbols']:self.assertIn(symbol,(ROOT/ref['path']).read_text())

    def test_original_model_is_actual_v10_archive_item_entity_identifier_not_current_item_key(self):
        version,model=self.proof['original_resources']
        self.assertEqual(plistlib.loads((ROOT/version['path']).read_bytes())['NSManagedObjectModel_CurrentVersionName'],'v10')
        archive=plistlib.loads((ROOT/model['path']).read_bytes());objects=archive['$objects']
        self.assertEqual(archive['$archiver'],'NSKeyedArchiver')
        def deref(x):return objects[x.data] if isinstance(x,plistlib.UID) else x
        def dictionary(x):x=deref(x);return {deref(k):deref(v) for k,v in zip(x['NS.keys'],x['NS.objects'])}
        item=objects[model['entities']['ItemEntity']['object_index']]
        self.assertEqual(deref(item['NSEntityName']),'ItemEntity')
        self.assertEqual(deref(item['NSClassNameForEntity']),'PasteCore.ItemEntity')
        properties=dictionary(item['NSProperties'])
        self.assertEqual(properties['identifier']['NSAttributeType'],700)
        self.assertEqual(deref(properties['identifier']['NSAttributeValueClassName']),'NSString')
        self.assertNotIn('key',properties);self.assertNotIn('isDeleted',properties)
        self.assertTrue(properties['timestamp']['NSIsOptional'])
        self.assertEqual(deref(properties['list']['_NSDestinationEntityName']),'ListEntity')
        self.assertEqual(properties['list']['NSMaxCount'],1)
        for fid in ['Paste:0x100024274','Paste:0x1003594e4','Paste:0x100368250']:
            self.assertEqual(self.rows[fid]['status'],'unclosed')

    def test_identity_difference_is_bound_to_actual_writes_reads_and_consumer_not_renaming_alone(self):
        original=self.native('0x10037063c');reducer=self.native('0x10036fa2c')
        self.assertIn('objc_stub::identifier(IVar1)',original)
        self.assertIn('_swift_dynamicCastClass',original)
        self.assertIn('Swift::__typeName(false)',reducer)
        encoded=self.proof['small_string_tombstone_key'];a=int(encoded['word1'],16);b=int(encoded['word2'],16)
        self.assertEqual((a.to_bytes(8,'little')+b.to_bytes(8,'little'))[:10],b'identifier')
        current=(ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        self.assertIn('entity: "Item", key: { $0.id.uuidString }',current)
        self.assertIn('object.setValue(id, forKey: "key")',current)
        history=(ROOT/'replica/Sources/PastoCore/OriginalSearchHistory.swift').read_text()
        self.assertIn('change.changedObjectID.entity.name == "Item"',history)
        self.assertIn('value(forKey: "key") as? String',history)
        self.assertIn('identifier = change.tombstone?["key"] as? String',history)
        self.assertEqual(hashlib.md5(b'pasto-p0-fresh-item').hexdigest(),'d84e1a0775d13912d49cd129e7e579ba')
        for fid in ['Paste:0x10037063c','Paste:0x10036fa2c']:
            self.assertEqual(self.rows[fid]['status'],'difference_confirmed')
            self.assertEqual(self.rows[fid]['shared_difference_origin'],'Paste:0x100360d9c')

    def test_value_witness_template_and_dispatch_reach_copy_that_retains_content_callbacks(self):
        p=self.proof['value_copy'];self.assertEqual(self.relative(0x100cad08c),0x100fc1560)
        self.assertEqual(self.pointer(0x100fc1558),0x100fc14e0)
        self.assertEqual(self.pointer(0x100fc1568),0x100cad06c)
        self.assertEqual(self.pointer(int(p['initializing_copy_slot'],16)),0x10037582c)
        self.assertEqual(self.word(0x1002fc10c),0xf85f8008)  # ldur x8,[x0,#-8]
        self.assertEqual(self.word(0x1002fc110),0xf9400908)  # ldr x8,[x8,#0x10]
        self.assertEqual(self.word(0x1002fc11c),0xd63f0100)  # blr x8
        copy=self.native('0x10037582c')
        for token in ['lVar9 = param_2[6]','lVar9 = param_2[10]','param_1[7] = uVar5','param_1[0xb] = uVar5']:
            self.assertIn(token,copy)
        self.assertGreaterEqual(copy.count('_swift_retain();'),2)
        self.assertNotIn('objc_stub::data',copy)
        fields=self.relative(0x100cad06c+16);size,count=struct.unpack_from('<HI',self.binary,self.offset(fields)+10)
        names=[self.string(self.relative(fields+16+size*i+8))for i in range(count)]
        self.assertEqual(names[3],'content');self.assertEqual(names[5],'imageData')
        current=(ROOT/'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        entry=body(current,'private struct Entry: Equatable')
        self.assertIn('let text: String',entry);self.assertNotIn('let content:',entry);self.assertNotIn('let imageData:',entry)
        self.assertIn('attributes.textContent = entry.text',current)
        self.assertEqual(self.rows['Paste:0x1002fc0ec']['shared_difference_origin'],'Paste:0x100371998')

    def test_constructor_slots_and_normalization_branch_prove_display_publish_order_without_inverting_equal_case(self):
        self.assertEqual(self.adrp_add(0x10003f660),0x100041ba0)
        self.assertEqual(self.adrp_add(0x10003f668),0x100041ba8)
        self.assertEqual(self.adrp_add(0x10003f670),0x100041bb0)
        self.assertEqual(self.adrp_add(0x10003f678),0x100041bb8)
        self.assertEqual(self.word(0x1002f72bc),0xa9010288)
        self.assertEqual(self.word(0x1002f72c0),0xa9020a81)
        self.assertEqual(self.word(0x1002f72c4),0xa9031283)
        self.assertEqual(self.word(0x1002f72c8),0xa9041a85)
        native=self.native('0x1002f7370')
        block=native[native.index('FUN_1002de150(uVar12,uVar8)'):]
        self.assertIn('if ((uVar10 & 1) == 0)',block)
        self.assertLess(block.index('unaff_x20 + 0x28'),block.index('unaff_x20 + 0x18'))
        self.assertIn('return 0;',block);self.assertTrue(block.rstrip().endswith('return 1;\n}'))
        current=(ROOT/'replica/Sources/Pasto/UI/SearchEditor.swift').read_text()
        propose=body(current,'private func propose(_ proposed: NSAttributedString, selection: NSRange,')
        self.assertLess(propose.index('publish(value)'),propose.index('guard value.needsNormalization else { return true }'))
        self.assertLess(propose.index('publish(value)'),propose.index('display(rendered,'))
        row=self.rows['Paste:0x1002f7370'];self.assertIn('rawNodes != normalizedNodes',row['contract'])
        self.assertIn('普通规范输入',row['contract'])

    def test_undo_suggestion_cleanup_order_differs_but_inactive_history_reset_remains_unknown(self):
        native=self.native('0x1002f7c14')
        offsets=['unaff_x20 + 0x48','unaff_x20 + 0x28','unaff_x20 + 0x18','unaff_x20 + 0x38']
        self.assertEqual([native.index(x)for x in offsets],sorted(native.index(x)for x in offsets))
        for a,slot in [(0x1002f7c70,0x48),(0x1002f7c80,0x28),(0x1002f7c90,0x18),(0x1002f7c9c,0x38)]:
            instruction=self.word(a);self.assertEqual(((instruction>>15)&127)*8,slot)
        current=(ROOT/'replica/Sources/Pasto/UI/SearchEditor.swift').read_text()
        restore=body(current,'private func restore(_ snapshot: OriginalSearchInputHistory.Snapshot?,')
        self.assertLess(restore.index('dismissSuggestions()'),restore.index('attributedString(snapshot.nodes'))
        self.assertLess(restore.index('display(rendered,'),restore.index('parent.onInputChange'))
        self.assertEqual(self.rows['Paste:0x1002f7c14']['status'],'difference_confirmed')
        self.assertEqual(self.rows['Paste:0x1002f7d60']['status'],'unclosed')

    def test_stack_summary_is_only_valid_preview_domain_and_textkit_constructor_dispatch_not_assumed(self):
        current=(ROOT/'replica/Sources/Pasto/UI/OriginalStackSnippetText.swift').read_text()
        for token in ['String(metadata.text.characters)','metadata.url.absoluteString','URL(fileURLWithPath: path).lastPathComponent']:
            self.assertIn(token,current)
        producer=(ROOT/'replica/Sources/PastoCore/OriginalTextPreviewMetadata.swift').read_text()
        self.assertIn('items.first?.f_10037d33c()',producer)
        self.assertIn('let length = source.length',producer)
        self.assertIn('NSRange(location: 0, length: 500)',producer)
        self.assertEqual(self.rows['Paste:0x100051ec8']['status'],'local_contract_consistent')
        self.assertIn('UTF-16',self.rows['Paste:0x100051ec8']['contract'])
        for fid in ['Paste:0x100044aec','Paste:0x10004430c']:
            self.assertEqual(self.rows[fid]['status'],'unclosed')
            self.assertTrue(self.rows[fid]['sdk_evidence'])
        self.assertIn('OriginalSearchTextView(usingTextLayoutManager: true)',(ROOT/'replica/Sources/PastoCore/OriginalSearchInputView.swift').read_text())

    def test_recomputed_progress_and_frozen_production_ledger_and_head(self):
        counts=Counter(x['status']for x in self.rows.values());self.assertEqual(dict(counts),self.report['outcomes'])
        self.assertEqual(646-counts['unclosed'],630)
        self.assertEqual(self.report['resolved_comparison_percent'],round(630/646*100,2))
        self.assertEqual(self.report['p0_component']['unclosed'],3)
        self.assertEqual(self.report['p1_additional_component']['unclosed'],13)
        before=json.loads((ROOT/'.local/p0-review/production-before.json').read_text())
        now={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in (ROOT/'replica/Sources').rglob('*')if p.is_file()}
        self.assertEqual(now,before);self.assertEqual(len(now),218)
        self.assertEqual(digest('replica/function-map.json'),self.report['function_map_sha256'])
        self.assertEqual(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'050e6878a5a52f96fe33aa40f48bb8a056cd0f05')
        for flag in ['production_source_edited','compiled','application_executed','committed','pushed']:self.assertFalse(self.report[flag])


if __name__=='__main__':unittest.main()
