"""The three phase80 supplied-input adapter deltas for earlier frozen source contracts.

Current input preservation and actual consumers are checked in test_p1_repair_supplied_input_adapters.
"""
from pathlib import Path
from stack_occurrence_scope_contract import pre_stack_occurrences

CHANGES = [('replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '{\n        copy(ids: [item.id], plainTextOnly: plainTextOnly)\n    }',
  '{\n'
  '        performCopy {\n'
  '            try store.writeToPasteboard(selectedItems: [item], pasteboard: pasteboard, plainTextOnly: '
  'plainTextOnly)\n'
  '        }\n'
  '    }'),
 ('replica/Sources/PastoCore/ClipboardStore.swift',
  '{\n        try assign(orderedIDs: items.filter { ids.contains($0.id) }.map(\\.id), to: pinboardID)\n    }',
  '{\n'
  '        var ordered = items.filter { ids.contains($0.id) }.map(\\.id)\n'
  '        let cached = Set(ordered)\n'
  "        // A UUID absent from the cached value array must still reach the transaction's current state.\n"
  '        ordered += ids.subtracting(cached).sorted { $0.uuidString < $1.uuidString }\n'
  '        try assign(orderedIDs: ordered, to: pinboardID)\n'
  '    }'),
 ('replica/Sources/PastoCore/ClipboardStore.swift',
  '{\n'
  '        let local = current\n'
  '        try validate(local)\n'
  '        let available = Set(local.items.filter { !$0.isDeleted }.map(\\.id))\n'
  '        guard selected.allSatisfy({ available.contains($0.id) }) else { throw '
  'ClipboardStoreError.itemNotFound }\n'
  '        return try withLock {\n'
  '            HistoryRestoreOperation(local: local, previous: baseline,\n'
  '                native: try persistence.prepareHistoryRestore(ids: selected.map(\\.id)))\n'
  '        }\n'
  '    }',
  '{\n'
  '        let local = current\n'
  '        try validate(local)\n'
  '        return try withLock {\n'
  '            var state = local\n'
  '            var previous = baseline\n'
  '            // Keep the selected native input while adapting a newer persisted state for restoration '
  'metadata.\n'
  '            if try revision() != diskRevision {\n'
  '                previous = try latestState()\n'
  '                state = merge(local, onto: previous)\n'
  '                try validate(state)\n'
  '            }\n'
  '            let available = Set(state.items.filter { !$0.isDeleted }.map(\\.id))\n'
  '            guard selected.allSatisfy({ available.contains($0.id) }) else { throw '
  'ClipboardStoreError.itemNotFound }\n'
  '            return HistoryRestoreOperation(local: state, previous: previous,\n'
  '                native: try persistence.prepareHistoryRestore(ids: selected.map(\\.id)))\n'
  '        }\n'
  '    }')]

def pre_supplied_input_adapters(source):
    source = pre_stack_occurrences(source)
    for path, previous, current in CHANGES:
        if current in source:
            assert source.count(current) == 1, path
            source = source.replace(current, previous, 1)
    return source


def pre_supplied_input_adapters_bytes(path):
    path = Path(path)
    value = path.read_bytes()
    return pre_supplied_input_adapters(value.decode()).encode() if path.suffix == '.swift' else value
