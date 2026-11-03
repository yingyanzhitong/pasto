"""Isolate only reviewed159 raw NSData nil bridge, preserving original ObjC exception handling."""
CHANGES = [['replica/Sources/PastoCore/ClipboardItemDataPersistence.swift',
  '                guard let raw = data.value(forKey: "rawPasteboardItems") as? Data else {\n'
  '                    throw CocoaError(.fileReadCorruptFile)\n'
  '                }\n'
  '                return raw',
  '                let raw = data.value(forKey: "rawPasteboardItems") as? NSData\n'
  '                return Data._unconditionallyBridgeFromObjectiveC(raw)',
  1]]

from save_failure_rollback_scope_contract import pre_save_failure_rollback

def pre_raw_data_nil_bridge(source):
    source=pre_save_failure_rollback(source)
    for _,old,new,count in reversed(CHANGES):
        if new in source:
            assert source.count(new)==count
            source=source.replace(new,old)
    return source

def pre_raw_data_nil_bridge_bytes(path):
    data=path.read_bytes()
    return pre_raw_data_nil_bridge(data.decode()).encode()if path.suffix=='.swift'else data
