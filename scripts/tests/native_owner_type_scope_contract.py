"""Reverse only phase113 native owner rawType gate for historical source checks."""
from native_stack_rendering_scope_contract import pre_native_stack_rendering
CHANGES = [['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '        if let list = object.value(forKey: "list") as? NSManagedObject,\n'
  '           let identifier = list.value(forKey: "identifier") as? String,',
  '        if let list = object.value(forKey: "list") as? NSManagedObject,\n'
  '           (list.value(forKey: "rawType") as? NSNumber)?.int64Value == 2,\n'
  '           let identifier = list.value(forKey: "identifier") as? String,']]

def pre_native_owner_type(source):
    source=pre_native_stack_rendering(source)
    for _,old,new in reversed(CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source
