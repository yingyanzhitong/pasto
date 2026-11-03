"""Reverse only reviewed117 preparation ordering delta for older source contracts."""
from shared_pasteboard_state_scope_contract import pre_shared_pasteboard_state
CHANGES = [['replica/Sources/PastoCore/Pasteboard.swift',
  '{\n'
  '        if let first = objects.first {\n'
  '            first.f_10037d8c8(Data(), forType: generatedType.rawValue)\n'
  '            first.f_10037d8c8(Data(), forType: replicaGeneratedType.rawValue)\n'
  '        }\n'
  '        // The original writer clears and writes even when processing produced no representations.\n'
  '        let restoration = try prepareRestoration()\n'
  '        let writer = OriginalPasteboardWriter(pasteboard: pasteboard)\n'
  '        writer.f_10037875c(objects)\n'
  '        if let state = OriginalPasteboardCaptureState.current(for: pasteboard) {\n'
  '            state.persistChangeCount?(state.lastChangeCount)\n'
  '        }\n'
  '        // 0x10037a144: performAndWait + save, then undo cleanup and DidRestore, before deactivation.\n'
  '        do {\n'
  '            try recordRestoredSelection(restoration)\n'
  '        } catch {\n'
  '            // Original 0x10037a144 releases the transaction error and continues below.\n'
  '        }\n'
  '        Self.restoreUndoManager.f_1000da768().removeAllActions()\n'
  '        // 37a144 posts process-wide with the restoring manager as object.\n'
  '        // Keep the legacy subject for the existing local sound subscriber.\n'
  '        NotificationCenter.default.post(name: Self.didRestoreItemNotification, object: self)\n'
  '        didRestoreItem.send()\n'
  '    }',
  '{\n'
  '        if let first = objects.first {\n'
  '            first.f_10037d8c8(Data(), forType: generatedType.rawValue)\n'
  '            first.f_10037d8c8(Data(), forType: replicaGeneratedType.rawValue)\n'
  '        }\n'
  '        // The original writer clears and writes even when processing produced no representations.\n'
  '        let writer = OriginalPasteboardWriter(pasteboard: pasteboard)\n'
  '        writer.f_10037875c(objects)\n'
  '        if let state = OriginalPasteboardCaptureState.current(for: pasteboard) {\n'
  '            state.persistChangeCount?(state.lastChangeCount)\n'
  '        }\n'
  '        // 0x10037a144: performAndWait + save, then undo cleanup and DidRestore, before deactivation.\n'
  '        do {\n'
  '            let restoration = try prepareRestoration()\n'
  '            try recordRestoredSelection(restoration)\n'
  '        } catch {\n'
  '            // Original 0x10037a144 releases the transaction error and continues below.\n'
  '        }\n'
  '        Self.restoreUndoManager.f_1000da768().removeAllActions()\n'
  '        // 37a144 posts process-wide with the restoring manager as object.\n'
  '        // Keep the legacy subject for the existing local sound subscriber.\n'
  '        NotificationCenter.default.post(name: Self.didRestoreItemNotification, object: self)\n'
  '        didRestoreItem.send()\n'
  '    }']]

def pre_postwrite_restore(source):
    source=pre_shared_pasteboard_state(source)
    for _,old,new in reversed(CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source
