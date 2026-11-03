"""Exact entity lookup/projection separation deltas for historical contracts only."""
from pathlib import Path
from native_text_read_scope_contract import pre_native_text_read
CHANGES = [['replica/Sources/PastoCore/ClipboardCollectionItemReference.swift',
  '    // 3544dc: optional ID lookup, then the expected concrete entity class.\n'
  '    @MainActor public func item() -> ClipboardItem? {\n'
  '        guard let object = (try? context.existingObject(with: objectID)) as? PastoItemEntity else { '
  'return nil }\n'
  '        // Project the existing local representation only when the consumer asks for content.\n'
  '        return try? ClipboardPersistence.item(object)\n'
  '    }\n'
  '\n'
  '    // 35440c keeps a missing indexed element distinct from optional ID lookup.\n'
  '    @MainActor public func requiredItem() -> ClipboardItem {\n'
  '        guard let item = item() else { fatalError("Missing collection item") }\n'
  '        return item\n'
  '    }\n'
  '\n'
  '    // 06e1f8 -> 1b9698 uses the optional ID lookup, unlike required indexed access.\n',
  '    // 3544dc: lookup/class errors are optional; content projection is a later consumer operation.\n'],
 ['replica/Sources/PastoCore/ClipboardCollectionItemReference.swift',
  '        guard let object = (try? context.existingObject(with: objectID)) as? PastoItemEntity else {\n'
  '            fatalError("Missing restore item")\n'
  '        }\n'
  '        return ClipboardRestoreItem(id: id, object: object)\n',
  '        // 35440c uses the same optional entity getter, then requires a result.\n'
  '        guard let input = restoreItem(id: id) else { fatalError("Missing restore item") }\n'
  '        return input\n'],
 ['replica/Sources/PastoCore/ClipboardCollectionEntry.swift',
  '        if let reference { return reference.item() }',
  '        if let reference { return reference.restoreItem(id: id)?.resolvedItem() }'],
 ['replica/Sources/PastoCore/ClipboardCollectionEntry.swift',
  '        if let reference { return reference.requiredItem() }',
  '        if let reference { return reference.requiredRestoreItem(id: id).resolvedItem() }'],
 ['replica/Sources/PastoCore/ClipboardSearchCollection.swift',
  '            return reference.requiredItem()',
  '            return reference.requiredRestoreItem(id: identifier).resolvedItem()']]

def pre_entity_lookup(source):
    source = pre_native_text_read(source)
    for path, before, after in reversed(CHANGES):
        if after in source:
            assert source.count(after) == 1, path
            source = source.replace(after, before, 1)
    return source

def pre_entity_lookup_bytes(path):
    data = Path(path).read_bytes()
    if str(path).endswith(".swift"):
        return pre_entity_lookup(data.decode()).encode()
    return data
