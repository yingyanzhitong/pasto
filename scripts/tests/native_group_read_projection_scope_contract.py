"""Reverse only reviewed163 augmentation of native groups missing compatibility rows."""
CHANGES = [['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  '{\n'
  '        let lists = try allLists()\n'
  '        return pinboards.map { board in\n'
  '            guard let list = lists[board.id.uuidString] else { return board }\n'
  '            var value = board\n'
  '            value.name = list.value(forKey: "name") as? String ?? board.name\n'
  '            value.rawAttributes = list.value(forKey: "rawAttributes") as? Data\n'
  '            // Nil from legacy JSON is normalized when building the graph; readers use its real '
  'type.\n'
  '            let rawType = (list.value(forKey: "rawType") as? NSNumber)?.int64Value ?? 0\n'
  '            // Do not truncate an unknown 64-bit type into the ordinary-group value 2.\n'
  '            value.rawType = Int16(exactly: rawType) ?? 0\n'
  '            if let metadata = list.value(forKey: "metadata") as? NSManagedObject,\n'
  '               let index = metadata.value(forKey: "index") as? NSNumber { value.sortOrder = '
  'index.intValue }\n'
  '            return value\n'
  '        }\n'
  '    }',
  '{\n'
  '        let lists = try allLists()\n'
  '        var values = pinboards.map { board in\n'
  '            guard let list = lists[board.id.uuidString] else { return board }\n'
  '            var value = board\n'
  '            value.name = list.value(forKey: "name") as? String ?? board.name\n'
  '            value.rawAttributes = list.value(forKey: "rawAttributes") as? Data\n'
  '            // Nil from legacy JSON is normalized when building the graph; readers use its real '
  'type.\n'
  '            let rawType = (list.value(forKey: "rawType") as? NSNumber)?.int64Value ?? 0\n'
  '            // Do not truncate an unknown 64-bit type into the ordinary-group value 2.\n'
  '            value.rawType = Int16(exactly: rawType) ?? 0\n'
  '            if let metadata = list.value(forKey: "metadata") as? NSManagedObject,\n'
  '               let index = metadata.value(forKey: "index") as? NSNumber { value.sortOrder = '
  'index.intValue }\n'
  '            return value\n'
  '        }\n'
  '        // A native List does not require a separate compatibility Pinboard row to exist.\n'
  '        var represented = Set(values.map(\\.id))\n'
  '        for list in lists.values {\n'
  '            guard !list.isDeleted,\n'
  '                  (list.value(forKey: "rawType") as? NSNumber)?.int64Value == 2,\n'
  '                  let identifier = list.value(forKey: "identifier") as? String,\n'
  '                  let id = UUID(uuidString: identifier), represented.insert(id).inserted else { '
  'continue }\n'
  '            let attributes = list.value(forKey: "rawAttributes") as? Data\n'
  '            let colorHex = OriginalPinboardAttributes.colorCode(from: attributes)\n'
  '                .map { String(format: "#%06llX", $0) } ?? "#FF9500"\n'
  '            let metadata = list.value(forKey: "metadata") as? NSManagedObject\n'
  '            let index = (metadata?.value(forKey: "index") as? NSNumber)?.intValue ?? 0\n'
  '            values.append(Pinboard(id: id, name: list.value(forKey: "name") as? String ?? "",\n'
  '                colorHex: colorHex, sortOrder: index, rawType: 2, rawAttributes: attributes))\n'
  '        }\n'
  '        return values.sorted {\n'
  '            $0.sortOrder == $1.sortOrder ? $0.id.uuidString < $1.id.uuidString : $0.sortOrder < '
  '$1.sortOrder\n'
  '        }\n'
  '    }',
  1]]

from native_tab_list_delivery_scope_contract import pre_native_tab_list_delivery

def pre_native_group_read_projection(source):
    source=pre_native_tab_list_delivery(source)
    for _,old,new,count in reversed(CHANGES):
        if new in source:
            assert source.count(new)==count
            source=source.replace(new,old)
    return source

def pre_native_group_read_projection_bytes(path):
    data=path.read_bytes()
    return pre_native_group_read_projection(data.decode()).encode()if path.suffix=='.swift'else data
