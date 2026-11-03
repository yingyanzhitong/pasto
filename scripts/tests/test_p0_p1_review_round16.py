"""Read-only finite comparisons; guard corrected control flow and primary provenance."""
import hashlib
import json
import struct
import subprocess
import unittest
from collections import Counter

from test_offline_p0_contracts import ROOT, body
from test_p0_p1_review_round2 import digest, fragment


class P0P1ReviewRound16(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((ROOT/'reports/replica/p0-p1-review-round16.json').read_text())
        cls.prior=json.loads((ROOT/'reports/replica/p0-p1-review-round15.json').read_text())
        cls.rows={r['function_id']:r for r in cls.report['records']}
        cls.proof=json.loads((ROOT/cls.report['static_proof']['path']).read_text())
        cls.binary=(ROOT/cls.proof['binary_path']).read_bytes()

    def native(self, address):
        index=json.loads((ROOT/'reports/Paste/function-index.json').read_text())
        return fragment(address,next(x['file'] for x in index if x['address']==address))

    def offset(self, address):
        for seg in self.proof['segments']:
            if seg['vmaddr']<=address<seg['vmaddr']+seg['filesize']:
                return seg['fileoff']+address-seg['vmaddr']
        self.fail(hex(address))

    def string(self, address):
        start=self.offset(address)
        return self.binary[start:self.binary.index(b'\0',start)].decode()

    def relative(self, address):
        return address+struct.unpack_from('<i',self.binary,self.offset(address))[0]

    def test_only_14_existing_records_change_and_old_explanation_correction_is_not_new_progress(self):
        old={r['function_id']:r for r in self.prior['records']}
        changed=set(self.report['round_delta']['reviewed_function_ids'])
        self.assertEqual(set(old),set(self.rows));self.assertEqual(len(self.rows),646)
        self.assertEqual(len(changed),14);self.assertEqual(self.report['round_delta']['scope_added'],0)
        self.assertEqual(self.report['scope_manifest_sha256'],self.prior['scope_manifest_sha256'])
        for fid in old:
            if fid not in changed:self.assertEqual(self.rows[fid],old[fid])
            elif fid!='Paste:0x100040054':self.assertEqual(old[fid]['status'],'unclosed')
        self.assertEqual(self.report['round_delta']['existing_contract_corrections'],['Paste:0x100040054'])
        self.assertEqual(self.rows['Paste:0x100040054']['historical_contract_correction'],old['Paste:0x100040054']['contract'])
        self.assertFalse(any(r['full_function_migration_verified'] for r in self.rows.values()))
        self.assertIsNone(self.report['full_priority_completion_percent'])

    def test_all_new_primary_and_supporting_evidence_hashes_bind_actual_fragments_and_literals(self):
        for path,sha in self.report['source_inputs'].items():self.assertEqual(digest(path),sha,path)
        self.assertEqual(digest(self.report['static_proof']['path']),self.report['static_proof']['sha256'])
        self.assertEqual(hashlib.sha256(self.binary).hexdigest(),self.proof['binary_sha256'])
        for fid in self.report['round_delta']['reviewed_function_ids']:
            row=self.rows[fid]
            for ref in [dict(row['original'],function_id=fid)]+row.get('supporting_original_fragments',[]):
                address=ref.get('address') or ref['function_id'].split(':')[1]
                self.assertEqual(hashlib.sha256(fragment(address,ref['path']).encode()).hexdigest(),ref['sha256'])
            for ref in row['current_references']:
                self.assertEqual(digest(ref['path']),ref['sha256'])
                self.assertIn(ref['symbol'],(ROOT/ref['path']).read_text())

    def test_search_end_editing_active_branch_refocuses_and_lazy_getter_never_closes_search(self):
        native=self.native('0x100040054');getter=self.native('0x10003e7d0')
        self.assertIn('SearchBar::isActive] == (code)0x1',native)
        self.assertIn('objc_stub::makeFirstResponder_(self,IVar2)',native)
        self.assertIn('FUN_1002f7d60(0)',native)
        self.assertIn('___lazy_storage___searchField',getter)
        self.assertNotIn('isActive',getter)
        self.assertIn('FUN_100040054',self.native('0x100041b88'))
        current=(ROOT/'replica/Sources/Pasto/UI/SearchEditor.swift').read_text()
        self.assertIn('if self.parent.focused { self.parent.focused = false }',current)
        self.assertEqual(self.rows['Paste:0x100040054']['status'],'difference_confirmed')
        self.assertEqual(self.rows['Paste:0x1002f7d60']['status'],'unclosed')
        self.assertIn('runtime_final_first_responder',self.rows['Paste:0x100040054']['coverage_boundaries']['not_verified'])

    def test_suggestion_task_has_no_suspension_between_provider_and_show_and_cancel_race_is_not_proven(self):
        text=(ROOT/'replica/Sources/Pasto/UI/SearchEditor.swift').read_text()
        update=body(text,'private func updateSuggestions(_ field: SearchField, editor: SearchTextView)')
        self.assertIn('Task { @MainActor',update)
        chain=update[update.index('let candidates ='):update.index('menu.show(')]
        self.assertNotIn('await ',chain)
        self.assertIn('guard !Task.isCancelled else { return }',chain)
        self.assertIn('manager.textViewportLayoutController.layoutViewport()',chain)
        self.assertIn('editor.convert(textRect, to: field)',chain)
        self.assertEqual(self.rows['Paste:0x100041190']['status'],'unclosed')
        self.assertEqual(self.rows['Paste:0x1000407f8']['status'],'local_contract_consistent')

    def test_search_placeholder_values_use_actual_original_bundle_not_only_derived_dictionary(self):
        proof=self.proof['localization']
        from macho_imports import parse_macho
        parsed=parse_macho(ROOT/proof['original_binary']['path'])
        self.assertEqual(parsed['arm64_sha256'],self.proof['binary_sha256'])
        self.assertEqual(parsed['container_sha256'],proof['original_binary']['sha256'])
        expected={'en':'Search','zh-Hans':'搜索'}
        current=(ROOT/'replica/Sources/PastoCore/OriginalSearchAppearance.swift').read_text()
        for resource in proof['resources']:
            self.assertEqual(digest(resource['path']),resource['sha256'])
            values=json.loads(subprocess.check_output(['/usr/bin/plutil','-convert','json','-o','-',resource['path']]))
            self.assertEqual(values['general.search'],expected[resource['locale']])
            self.assertIn('"'+resource['locale']+'": "'+resource['value']+'"',current)
        self.assertEqual(len(proof['resources']),2)
        self.assertIn('all_locale_selection_or_fallback',self.rows['Paste:0x10004371c']['coverage_boundaries']['not_verified'])

    def test_completed_index_health_query_and_state_schema_are_real_binary_inputs(self):
        data=self.proof['indexing_state'];nominal=int(data['nominal'],16)
        self.assertEqual(self.string(self.relative(nominal+8)),'IndexingState')
        fields=self.relative(nominal+16);size,count=struct.unpack_from('<HI',self.binary,self.offset(fields)+10)
        names=[self.string(self.relative(fields+16+size*i+8)) for i in range(count)]
        self.assertEqual(names,['schemaVersion','totalItems','indexedItems','oldestTimestamp','invalidItems'])
        probe=self.proof['health_probe'];start=self.offset(int(probe['address'],16))
        self.assertEqual(self.binary[start:start+probe['length']].decode(),probe['value'])
        self.assertEqual(probe['value'],'contentModificationDate >= $time.iso(1970-01-01T00:00:00Z)')
        self.assertIn('CSSearchQuery',self.native('0x1002e2930'))
        current=(ROOT/'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        self.assertIn('private var needsReset = true',current)
        self.assertIn('index.deleteSearchableItems(withDomainIdentifiers: [domain])',body(current,'private func drain() async'))
        row=self.rows['Paste:0x1002f00dc'];self.assertEqual(row['status'],'difference_confirmed')
        self.assertIn('persistence_backend_of_supplied_state',row['coverage_boundaries']['not_verified'])

    def test_stack_icon_uses_original_item_raw_type_but_real_current_consumer_uses_source_application(self):
        native=self.native('0x100051d2c');kind=self.native('0x10031eba8')
        self.assertIn('FUN_10031eba8()',native);self.assertIn('param_1 = param_1 & 0xff',native)
        self.assertIn('objc_stub::rawType',kind);self.assertIn('if (5 < IVar2)',kind)
        self.assertIn('imageNamed',native)
        consumer=(ROOT/'replica/Sources/Pasto/UI/AuxiliaryViews.swift').read_text()
        self.assertIn('OriginalStackSnippetCellView(item: item, imageProvider:',consumer)
        self.assertIn('state.store.sourceApplication(for: item)',consumer)
        self.assertIn('application.rawIcon.flatMap(NSImage.init(data:))',consumer)
        self.assertEqual(self.rows['Paste:0x1000519f8']['status'],'difference_confirmed')
        self.assertEqual(self.rows['Paste:0x100051ec8']['status'],'unclosed')

    def test_first_item_text_and_finite_source_icon_sampling_contracts_have_real_consumers(self):
        preview=(ROOT/'replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift').read_text()
        extract=body(preview,'private static func attributedContent(_ item: ClipboardItem) -> NSAttributedString')
        self.assertIn('items.first?.f_10037d33c()',extract)
        self.assertNotIn('compactMap',extract)
        pasteboard=(ROOT/'replica/Sources/PastoCore/OriginalPasteboard.swift').read_text()
        decode=body(pasteboard,'public func f_10037d33c() -> NSAttributedString?')
        self.assertIn('.flatRTFD, .rtfd, .rtf',decode)
        self.assertIn('f_10037c9a8()',decode)
        color=(ROOT/'replica/Sources/PastoCore/OriginalSourceApplicationColors.swift').read_text()
        self.assertIn('(alphaValue << 24) | (redValue << 16) | (greenValue << 8) | blueValue',color)
        native=self.native('0x100308c8c');self.assertIn('<< 0x18',native)
        image=(ROOT/'replica/Sources/PastoCore/OriginalSourceApplicationImageColor.swift').read_text()
        for token in ['width: 128, height: 128','bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true','bytesPerRow: width * 4, bitsPerPixel: 32','representation.draw(in: rect)','defer { NSGraphicsContext.restoreGraphicsState() }']:
            self.assertIn(token,image)
        self.assertIn('8,4,1,0,uVar4,lVar3 << 2,0x20',self.native('0x1003c7c4c'))
        for fid in ['Paste:0x100308c8c','Paste:0x1003c05d4','Paste:0x1003c7c4c']:
            self.assertEqual(self.rows[fid]['status'],'local_contract_consistent')
            self.assertFalse(self.rows[fid]['full_function_migration_verified'])

    def test_recount_and_frozen_production_ledger_and_head_match(self):
        counts=Counter(r['status'] for r in self.rows.values())
        self.assertEqual(dict(counts),self.report['outcomes'])
        resolved=646-counts['unclosed'];self.assertEqual(resolved,625)
        self.assertEqual(self.report['resolved_comparison_percent'],round(resolved/646*100,2))
        self.assertEqual(self.report['round_delta']['newly_resolved'],7)
        before=json.loads((ROOT/'.local/p0-review/production-before.json').read_text())
        now={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'replica/Sources').rglob('*') if p.is_file()}
        self.assertEqual(now,before);self.assertEqual(len(now),218)
        self.assertEqual(digest('replica/function-map.json'),self.report['function_map_sha256'])
        self.assertEqual(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'050e6878a5a52f96fe33aa40f48bb8a056cd0f05')
        for flag in ['production_source_edited','compiled','application_executed','committed','pushed']:
            self.assertFalse(self.report[flag])


if __name__=='__main__':unittest.main()
