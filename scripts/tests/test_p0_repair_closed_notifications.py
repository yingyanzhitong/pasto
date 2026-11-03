from native_restore_writer_scope_contract import pre_native_restore_writer
"""Closed-state notification source/data tests, no real event/app execution."""
import hashlib,json
from pathlib import Path
import sys,unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment


class ClosedNotificationContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-20'
        cls.proof=json.loads((cls.phase/'closed-root-contract.json').read_text())
        cls.ui=(ROOT/'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        cls.store=(ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        cls.board=pre_native_restore_writer((ROOT/'replica/Sources/PastoCore/Pasteboard.swift').read_text())
        cls.closed=body(cls.ui,'private func beginClosedState()')
        cls.writer=body(cls.board,'private func writeToPasteboard(ids:')

    def original(self,a):
        r=next(r for r in self.proof['original_fragments'] if r['address']==a)
        return original_fragment((ROOT/r['path']).read_text(),a[2:])

    def test_original_fragments_machine_ranges_and_notification_literals_are_bound(self):
        for r in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        raw=(ROOT/self.proof['binary']['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),self.proof['binary']['sha256'])
        for r in self.proof['machine_ranges']+self.proof['notification_literals']:
            data=raw[r['file_offset']:r['file_offset']+r['length']]
            self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'])
            if 'value' in r:self.assertEqual(data.decode(),r['value'])
        values=[r['value'] for r in self.proof['notification_literals']]
        self.assertEqual(values,['pasteboardHistoryManagerDidCreateItem','pasteboardHistoryManagerDidRestoreItem'])

    def test_timer_is_original_scheduled_nstimer_and_was_not_replaced_with_dispatch(self):
        original=self.original('0x100385984')
        self.assertIn('scheduledTimerWithTimeInterval_repeats_block_',original)
        self.assertIn('FUN_100385984(0x4024000000000000,0,',self.original('0x100021518'))
        before=(self.phase/'before/replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        old=body(before,'private func beginClosedState()')
        token='closedSearchTimer = Timer.scheduledTimer'
        self.assertEqual(self.closed[self.closed.index(token):],old[old.index(token):])
        self.assertIn('withTimeInterval: 10, repeats: false',self.closed)
        self.assertNotIn('DispatchQueue',self.closed)
        self.assertNotIn('Task {',self.closed)

    def test_controller_already_invalidated_timer_on_deinit_and_reopen(self):
        before=(self.phase/'before/replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        self.assertEqual(body(self.ui,'deinit'),body(before,'deinit'))
        self.assertIn('cancelClosedState()',body(self.ui,'deinit'))
        self.assertIn('cancelClosedState()',body(self.ui,'func showPanel()'))
        cancel=body(self.ui,'private func cancelClosedState()')
        self.assertIn('closedSearchTimer?.invalidate()',cancel)
        self.assertIn('closedSearchTimer = nil',cancel)
        self.assertIn('objc_stub::invalidate',self.original('0x100385af0'))

    def test_two_global_notification_publishers_have_no_queue_hop_or_store_filter(self):
        original=self.original('0x100021518')
        self.assertEqual(original.count('NSNotificationCenter::_publisher('),2)
        self.assertIn('FUN_10037a6cc()',original)
        self.assertIn('FUN_10037a7ec()',original)
        self.assertEqual(self.closed.count('NotificationCenter.default.publisher('),2)
        for name in ['ClipboardMonitor.didCreateItemNotification','ClipboardStore.didRestoreItemNotification']:
            self.assertIn('for: '+name+', object: nil).sink { [weak self] _ in',self.closed)
        self.assertNotIn('queue: .main',self.closed)
        self.assertNotIn('receive(on:',self.closed)
        self.assertNotIn('store.didRestoreItem.sink',self.closed)
        self.assertNotIn('notification.object',self.closed)
        self.assertIn('MainActor.assumeIsolated',self.closed)

    def test_restore_producer_posts_original_name_after_undo_then_keeps_legacy_subject(self):
        self.assertIn('Notification.Name("pasteboardHistoryManagerDidRestoreItem")',self.store)
        original=self.original('0x10037a144')
        self.assertLess(original.index('objc_stub::removeAllActions'),original.index('postNotificationName_object_'))
        self.assertIn('DAT_1010579a0,unaff_x20',original)
        order=['try recordRestoredSelection(restoration)','removeAllActions()',
               'NotificationCenter.default.post(name: Self.didRestoreItemNotification, object: self)',
               'didRestoreItem.send()']
        self.assertEqual([self.writer.index(t) for t in order],sorted(self.writer.index(t) for t in order))
        self.assertEqual(self.writer.count('NotificationCenter.default.post('),1)
        self.assertEqual(self.writer.count('didRestoreItem.send()'),1)

    def test_save_failure_still_reaches_both_delivery_channels_without_hiding_early_errors(self):
        catch=self.writer.split('} catch {',1)[1].split('}',1)[0]
        self.assertFalse(''.join(l.split('//',1)[0] for l in catch.splitlines()).strip())
        prefix=self.writer[:self.writer.index('        do {')]
        self.assertIn('throw ClipboardStoreError.itemNotFound',prefix)
        self.assertNotIn('try? reload',prefix)
        tail=self.writer[self.writer.index('} catch {'):]
        self.assertIn('didRestoreItemNotification',tail)
        self.assertIn('didRestoreItem.send()',tail)

    def test_normal_history_restore_gate_and_create_reset_logic_are_preserved(self):
        restore=self.closed[self.closed.index('closedRestoreObservation ='):self.closed.index('closedSearchTimer = Timer.')]
        order=['self.state.isCollectionSearchQueryEmpty, self.state.pinboardID == nil',
               'self.state.chooseBoard(nil)','self.closedSearchTimer?.invalidate()','self.closedSearchTimer = nil']
        self.assertEqual([restore.index(t) for t in order],sorted(restore.index(t) for t in order))
        self.assertNotIn('applySearchInput(',restore)
        self.assertNotIn('hidePanel()',restore)
        create=self.closed[:self.closed.index('closedRestoreObservation =')]
        self.assertIn('self.state.chooseBoard(nil)',create)
        self.assertIn('self.closedSearchTimer?.invalidate()',create)
        self.assertIn('FUN_100021908(0,1)',self.original('0x100021a34'))

    def test_subscription_tokens_are_owned_and_cancelled_without_leaving_observers(self):
        self.assertIn('private var closedCreateObservation: AnyCancellable?',self.ui)
        self.assertIn('private var closedRestoreObservation: AnyCancellable?',self.ui)
        cancel=body(self.ui,'private func cancelClosedState()')
        for kind in ['Create','Restore']:
            self.assertIn('closed'+kind+'Observation?.cancel()',cancel)
            self.assertIn('closed'+kind+'Observation = nil',cancel)
        self.assertNotIn('closedCreateObserver',self.ui)
        self.assertLess(self.closed.index('cancelClosedState()'),self.closed.index('NotificationCenter.default.publisher'))

    def test_legacy_sound_is_not_subscribed_to_both_notification_and_subject(self):
        path='replica/Sources/PastoCore/OriginalSoundEffects.swift'
        baseline=json.loads((self.phase/'baseline.json').read_text())
        data=(ROOT/path).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),baseline['production'][path])
        sound=data.decode()
        self.assertEqual(sound.count('store.didRestoreItem.sink'),1)
        self.assertNotIn('didRestoreItemNotification',sound)
        self.assertNotIn('store.didRestoreItem.sink',self.closed)

    def test_scope_repair_is_counted_once_without_false_timer_or_full_parent_claim(self):
        self.assertEqual(len(self.proof['contracts']),1)
        self.assertEqual(self.proof['contracts'][0]['function_id'],'Paste:0x100021518')
        self.assertFalse(self.proof['contracts'][0]['full_function_migration_verified'])
        self.assertEqual(len(self.proof['reused_unchanged_contracts']),2)
        before=(self.phase/'before/replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        self.assertIn('closedRestoreObservation = store.didRestoreItem.sink',before)
        self.assertTrue(any(r['function_id']=='Paste:0x100021908' for r in self.proof['retained_partial_contracts']))


if __name__=='__main__':unittest.main()
