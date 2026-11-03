"""Reverse only reviewed161 removal of the guessed setter integer result for historical snapshots."""
CHANGES = [['replica/Sources/PastoCore/OriginalSearchTextValue.swift',
  '    @MainActor @discardableResult\n'
  '    func f_1000f733c(_ value: String) -> Int {\n'
  '        string = value\n'
  '        return 0\n'
  '    }',
  '    @MainActor func f_1000f733c(_ value: String) {\n        string = value\n    }',
  1]]

from native_list_creation_lifecycle_scope_contract import pre_native_list_creation_lifecycle

def pre_text_setter_return(source):
    source=pre_native_list_creation_lifecycle(source)
    for _,old,new,count in reversed(CHANGES):
        if new in source:
            assert source.count(new)==count
            source=source.replace(new,old)
    return source

def pre_text_setter_return_bytes(path):
    data=path.read_bytes()
    return pre_text_setter_return(data.decode()).encode()if path.suffix=='.swift'else data
