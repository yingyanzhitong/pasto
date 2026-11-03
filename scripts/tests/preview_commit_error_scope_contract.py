"""Isolate only reviewed158 four original preview transaction error boundaries."""
CHANGES = [['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  'func commitPreviewEditing() {\n'
  '        text.isEditable = false\n'
  '        guard let state else { return }\n'
  '        do {\n'
  '            let content = OriginalPreviewAttributedText.f_100212ccc(editor: text)\n'
  '            if let editInput {\n'
  '                try state.store.updateTextPreviewItem(editInput, attributedString: content)\n'
  '            } else {\n'
  '                try state.store.updateTextPreviewItem(id: itemID, attributedString: content)\n'
  '            }\n'
  '            state.normalizeSelection()\n'
  '        } catch { state.controller?.presentError(error) }\n'
  '        reloadStoredContent()\n'
  '    }',
  'func commitPreviewEditing() {\n'
  '        text.isEditable = false\n'
  '        guard let state else { return }\n'
  '        do {\n'
  '            let content = OriginalPreviewAttributedText.f_100212ccc(editor: text)\n'
  '            if let editInput {\n'
  '                try state.store.updateTextPreviewItem(editInput, attributedString: content)\n'
  '            } else {\n'
  '                try state.store.updateTextPreviewItem(id: itemID, attributedString: content)\n'
  '            }\n'
  '            state.normalizeSelection()\n'
  '        } catch {\n'
  '            // 3c0e08: consume the transaction error and continue the editing cleanup.\n'
  '        }\n'
  '        reloadStoredContent()\n'
  '    }',
  1],
 ['replica/Sources/Pasto/UI/ReplicaImagePreviewContent.swift',
  'func commitPreviewEditing() {\n'
  '        if let image = zoomView.f_100240a18(), let state {\n'
  '            do {\n'
  '                if let editInput {\n'
  '                    try state.store.updateImagePreviewItem(editInput, payloads: '
  'Self.encodedPayloads(image))\n'
  '                } else {\n'
  '                    try state.store.updateImagePreviewItem(id: itemID, payloads: '
  'Self.encodedPayloads(image))\n'
  '                }\n'
  '                state.normalizeSelection()\n'
  '            } catch { state.controller?.presentError(error) }\n'
  '        }\n'
  '        finishEditing(reloadNativeImage: false)\n'
  '    }',
  'func commitPreviewEditing() {\n'
  '        if let image = zoomView.f_100240a18(), let state {\n'
  '            do {\n'
  '                if let editInput {\n'
  '                    try state.store.updateImagePreviewItem(editInput, payloads: '
  'Self.encodedPayloads(image))\n'
  '                } else {\n'
  '                    try state.store.updateImagePreviewItem(id: itemID, payloads: '
  'Self.encodedPayloads(image))\n'
  '                }\n'
  '                state.normalizeSelection()\n'
  '            } catch {\n'
  '                // 3bde74: consume the transaction error and continue the editing cleanup.\n'
  '            }\n'
  '        }\n'
  '        finishEditing(reloadNativeImage: false)\n'
  '    }',
  1],
 ['replica/Sources/Pasto/UI/ReplicaLinkPreviewContent.swift',
  'func commitPreviewEditing() {\n'
  '        guard let state, let url = Self.normalizedURL(textView.string) else { return }\n'
  '        do {\n'
  '            if let editInput { try state.store.updateLinkItem(editInput, url: url) }\n'
  '            else { try state.store.updateLinkItem(id: itemID, url: url) }\n'
  '            state.normalizeSelection()\n'
  '        } catch { state.controller?.presentError(error) }\n'
  '        showContent(readOnlyContent)\n'
  '        updateMetadata(currentURL())\n'
  '    }',
  'func commitPreviewEditing() {\n'
  '        guard let state, let url = Self.normalizedURL(textView.string) else { return }\n'
  '        do {\n'
  '            if let editInput { try state.store.updateLinkItem(editInput, url: url) }\n'
  '            else { try state.store.updateLinkItem(id: itemID, url: url) }\n'
  '            state.normalizeSelection()\n'
  '        } catch {\n'
  '            // 3bf900: consume the transaction error and continue the editing cleanup.\n'
  '        }\n'
  '        showContent(readOnlyContent)\n'
  '        updateMetadata(currentURL())\n'
  '    }',
  1],
 ['replica/Sources/Pasto/UI/ReplicaColorPreviewContent.swift',
  'func commitPreviewEditing() {\n'
  '        editing = false\n'
  '        colorPanel.orderOut(nil)\n'
  '        guard let state else { return }\n'
  '        do {\n'
  '            let text = OriginalPreviewColorFormatting.f_100206b5c(displayedColor).uppercased()\n'
  '            if let editInput { try state.store.updateColorItem(editInput, text: text) }\n'
  '            else { try state.store.updateColorItem(id: itemID, text: text) }\n'
  '            state.normalizeSelection()\n'
  '        } catch { state.controller?.presentError(error) }\n'
  '    }',
  'func commitPreviewEditing() {\n'
  '        editing = false\n'
  '        colorPanel.orderOut(nil)\n'
  '        guard let state else { return }\n'
  '        do {\n'
  '            let text = OriginalPreviewColorFormatting.f_100206b5c(displayedColor).uppercased()\n'
  '            if let editInput { try state.store.updateColorItem(editInput, text: text) }\n'
  '            else { try state.store.updateColorItem(id: itemID, text: text) }\n'
  '            state.normalizeSelection()\n'
  '        } catch {\n'
  '            // 3bc01c: consume the transaction error and continue the editing cleanup.\n'
  '        }\n'
  '    }',
  1]]
BODY_CHANGES = [(old[old.index('{'):],new[new.index('{'):])for _,old,new,_ in CHANGES]

def pre_preview_commit_error(source):
    from raw_data_nil_bridge_scope_contract import pre_raw_data_nil_bridge
    source=pre_raw_data_nil_bridge(source)
    for _,old,new,count in reversed(CHANGES):
        if new in source:
            assert source.count(new)==count
            source=source.replace(new,old)
    for old,new in reversed(BODY_CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old)
    return source

def pre_preview_commit_error_bytes(path):
    data=path.read_bytes()
    return pre_preview_commit_error(data.decode()).encode()if path.suffix=='.swift'else data
