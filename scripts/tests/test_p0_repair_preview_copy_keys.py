"""Bounded copy/popover keyboard contracts, source and original ARM data only."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from macho_imports import parse_macho
from test_offline_p0_contracts import body
from popover_entity_input_scope_contract import pre_popover_entity_input
UI=ROOT/'replica/Sources/Pasto/UI/ReplicaUIController.swift'

class PreviewCopyKeys(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ui=pre_popover_entity_input(UI.read_text())
        cls.handle=body(cls.ui,'private func handleKey(_ event: NSEvent) -> Bool')
        cls.copy=body(cls.handle,'if !isEditing, let options = OriginalCollectionShortcutActions.copyOptions(')

    def test_original_fragments_and_raw_lifecycle_segments_are_bound(self):
        proof=json.loads((ROOT/'.local/p0-repair/phase-5/preview-key-original-proof.json').read_text())
        for r in proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT/r['path'])[r['function_id'].split(':')[1]]['sha256'],r['sha256'])
        machine=json.loads((ROOT/'.local/p0-repair/phase-5/preview-key-machine-proof.json').read_text())
        data=(ROOT/machine['binary_path']).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),machine['binary_sha256'])
        for r in machine['segments']:
            actual=data[r['file_offset']:r['file_offset']+r['length']]
            self.assertEqual(actual.hex(),r['hex'])
            self.assertEqual(hashlib.sha256(actual).hexdigest(),r['sha256'])

    def test_native_time_constant_and_callback_targets_override_decompiler_aliases(self):
        data=(ROOT/'.local/paste-arm64-static.bin').read_bytes()
        def word(address):return struct.unpack_from('<I',data,address-0x100000000)[0]
        for start in [0x10006a220,0x10006a570]:
            # MOV + MOVK sequence constructs Double bit pattern 0x3fb999999999999a.
            self.assertEqual([word(start+i*4) for i in range(4)],
                             [0xb201e7e8,0xf2933348,0xf2e7f728,0x9e670100])
        self.assertEqual(struct.unpack('<d',struct.pack('<Q',0x3fb999999999999a))[0],0.1)
        def address_pair(pc):
            adrp=word(pc);add=word(pc+4)
            self.assertEqual(adrp&0x9f000000,0x90000000)
            immediate=((adrp>>5)&0x7ffff)<<2|((adrp>>29)&3)
            if immediate&(1<<20):immediate-=1<<21
            self.assertEqual(add&0xffc00000,0x91000000)
            return (pc&~0xfff)+(immediate<<12)+((add>>10)&0xfff)
        self.assertEqual(address_pair(0x10006a274),0x10007676c)
        self.assertEqual(address_pair(0x10006a5c4),0x100076734)
        self.assertEqual(word(0x10006a270),0xf9000813)  # self into first closure box+0x10
        self.assertEqual(word(0x10006a5c0),0xf9000813)
        macho=parse_macho(ROOT/'.local/paste-arm64-static.bin')
        self.assertEqual(macho['stubs']['0x100bfbf70']['symbol'],'_objc_retain')

    def test_only_owner_gated_recognized_copy_shortcuts_reach_the_nonnil_delay(self):
        self.assertLess(self.handle.index('if !ownsCollectionFocus'),self.handle.index('OriginalCollectionShortcutActions.copyOptions('))
        self.assertIn('plainTextModifierRawValue: store.preferences.plainTextModifierRawValue',self.handle)
        nonnil=body(self.copy,'if previewPopover != nil')
        self.assertIn('DispatchQueue.main.asyncAfter(deadline: .now() + 0.1)',nonnil)
        self.assertIn('return true',nonnil)
        self.assertNotIn('isDisplayed',nonnil)
        self.assertNotIn('isShown',nonnil)
        self.assertNotIn('copySelection',nonnil)
        self.assertNotIn('paste(',nonnil)

    def test_delayed_callback_retains_owner_and_reads_the_current_optional_popover(self):
        callback=body(self.copy,'DispatchQueue.main.asyncAfter(deadline: .now() + 0.1)')
        self.assertIn('[self] in',callback)
        self.assertIn('previewPopover?.performClose(self)',callback)
        self.assertNotIn('[weak self]',callback)
        self.assertNotIn('guard let popover',callback)
        self.assertNotIn('popover.close()',callback)
        self.assertNotIn('copySelection',callback)

    def test_nil_popover_keeps_immediate_copy_and_its_original_options(self):
        nonnil=body(self.copy,'if previewPopover != nil')
        after=self.copy[self.copy.index(nonnil)+len(nonnil):]
        self.assertIn('copySelection(plainTextOnly: options.contains(.plainTextAndLinks))',after)
        self.assertIn('return true',after)
        self.assertNotIn('DispatchQueue',after)
        self.assertEqual(self.copy.count('copySelection('),1)

    def test_will_close_weakly_clears_the_owner_field_before_registry_cleanup(self):
        factory=body(self.ui,'private func makePreviewPopover() -> OriginalPreviewPopover')
        self.assertIn('popover.onWillClose = { [weak self] in self?.previewPopover = nil }',factory)
        self.assertLess(factory.index('popover.onWillClose ='),factory.index('return popover'))
        popover=(ROOT/'replica/Sources/PastoCore/OriginalPreviewPopover.swift').read_text()
        closing=body(popover,'public func f_100029da8() -> Int')
        order=['isDisplayed = false','onWillClose?()','registry.popoverItemIdentifier = nil']
        self.assertEqual([closing.index(t) for t in order],sorted(closing.index(t) for t in order))

    def test_ordinary_space_keeps_its_separate_immediate_preview_route(self):
        space=body(self.handle,'if event.keyCode == 49, !isEditing')
        self.assertIn('showPreview(item: item)',space)
        self.assertNotIn('asyncAfter',space)
        preview=body(self.ui,'func showPreview(item: ClipboardItem)')
        self.assertIn('if popover.isDisplayed',preview)
        self.assertIn('popover.close()',preview)
        self.assertNotIn('asyncAfter',preview)

    def test_pending_deletion_and_title_editor_gates_are_preserved(self):
        self.assertLess(self.handle.index('if state.hasPendingDeletion'),self.handle.index('if !ownsCollectionFocus'))
        send=body(self.ui,'override func sendEvent(_ event: NSEvent)')
        self.assertLess(send.index('tabTitleEditingOwner?.ownsEditor'),send.index('keyHandler?(event)'))
        self.assertNotIn('previewPopover',send)

if __name__=='__main__':unittest.main()
