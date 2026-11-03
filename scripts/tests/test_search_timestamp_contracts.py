"""Static source/metadata contracts; never executes Swift, Core Data or Spotlight."""
import json
import struct
import unittest

from test_offline_p0_contracts import ROOT, CORE, body


def optional_history_date(text):
    try:
        entry = body(text, "private struct Entry: Equatable")
        return ("let modified: Date?" in entry
                and "modified = item.isInHistory ? item.createdAt : nil" in entry
                and "item.updatedAt" not in entry
                and "Date()" not in entry)
    except ValueError:
        return False


class SearchTimestampContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ui = (ROOT / "replica/Sources/Pasto/UI/ReplicaUIController.swift").read_text()
        cls.index = (ROOT / "replica/Sources/Pasto/UI/ReplicaSearchIndex.swift").read_text()
        cls.original_index = {r["address"]: r for r in json.loads((ROOT / "reports/Paste/function-index.json").read_text())}
        cls.proof = json.loads((ROOT / "reports/replica/offline-migration-p0-round12.json").read_text())["static_bindings"]

    @classmethod
    def original(cls, address):
        text = (ROOT / cls.original_index[address]["file"]).read_text()
        start = text.index("/* Address: " + address + " |")
        end = text.find("/* Address:", start + 1)
        return text[start:end if end != -1 else None]

    def test_original_snapshot_key_is_timestamp_not_edit_time(self):
        words = struct.unpack("<6I", bytes.fromhex(self.proof["timestamp_key"]["bytes"]))
        x0 = sum(((word >> 5) & 0xffff) << (i * 16) for i, word in enumerate(words[:4]))
        x1 = ((words[4] >> 5) & 0xffff) + (((words[5] >> 5) & 0xffff) << 48)
        self.assertEqual((x0.to_bytes(8, "little") + x1.to_bytes(8, "little"))[:9], b"timestamp")
        snapshot = self.original("0x100371998")
        self.assertIn("objc_stub::valueForKeyPath_(param_2,pNVar6)", snapshot)
        self.assertIn("if (lStack_88 == 0)", snapshot)
        self.assertIn("_swift_dynamicCast(lVar9", snapshot)

    def test_metadata_field_six_is_optional_foundation_date(self):
        item = self.proof["item_metadata"]
        self.assertEqual(item["name"], "SearchableItemEntity")
        descriptor = bytes.fromhex(item["descriptor_bytes"])
        self.assertEqual(struct.unpack_from("<I", descriptor)[0] & 31, 17)  # Struct
        self.assertEqual(struct.unpack_from("<I", descriptor, 20)[0], 9)
        self.assertEqual(item["fields"][6]["name"], "timestamp")
        type_ref = self.proof["timestamp_type"]
        raw = bytes.fromhex(type_ref["mangled_ref_bytes"])
        self.assertEqual(raw[0], 2)  # Indirect context symbolic reference
        self.assertEqual(raw[5:7], b"Sg")  # Optional
        slot = int(type_ref["mangled_ref"], 16) + 1 + struct.unpack_from("<i", raw, 1)[0]
        self.assertEqual(slot, int(type_ref["indirect_slot"], 16))
        self.assertEqual(type_ref["symbol"], "_$s10Foundation4DateVMn")

    def test_conformance_and_real_dyld_chain_select_date_getter(self):
        conformance = self.proof["conformance"]
        raw = bytes.fromhex(conformance["bytes"])
        address = int(conformance["address"], 16)
        self.assertEqual(address + 4 + struct.unpack_from("<i", raw, 4)[0], 0x100cad06c)
        self.assertEqual(address + 8 + struct.unpack_from("<i", raw, 8)[0], 0x100ecd440)
        witness = self.proof["timestamp_witness"]
        self.assertEqual(int(witness["slot"], 16), 0x100ecd440 + 0x18)
        self.assertEqual(witness["pointer_format"], 6)
        self.assertTrue(witness["declared_dyld_chain_reachable"])
        pointer, = struct.unpack("<Q", bytes.fromhex(witness["bytes"]))
        self.assertEqual(pointer >> 63, 0)  # Rebase, not imported function bind
        self.assertEqual(0x100000000 + (pointer & ((1 << 36) - 1)), 0x100375200)

    def test_getter_offset_vector_and_attribute_slot_are_the_same_field(self):
        descriptor = bytes.fromhex(self.proof["item_metadata"]["descriptor_bytes"])
        vector_words, = struct.unpack_from("<I", descriptor, 24)
        self.assertEqual(vector_words * 8 + 6 * 4, 0x28)
        getter = struct.unpack("<4I", bytes.fromhex(self.proof["getter_instructions"]["bytes"]))
        self.assertEqual(getter[1], 0xb9802808)  # ldrsw x8, [x0,#0x28]
        attribute = struct.unpack("<5I", bytes.fromhex(self.proof["attribute_witness_load"]["bytes"]))
        self.assertEqual(attribute[0], 0xf9400f29)  # ldr x9, [x25,#0x18]
        self.assertEqual(attribute[-1], 0xd63f0120)  # blr x9
        self.assertIn("*(int *)(param_2 + 0x28)", self.original("0x100375200"))
        self.assertIn("setContentModificationDate_(IVar6,pNVar19)", self.original("0x1002e3ce8"))

    def test_index_preserves_missing_history_date_as_nil(self):
        self.assertTrue(optional_history_date(self.index))
        attributes = body(self.index, "private func searchableItem(_ entry: Entry)")
        self.assertIn("attributes.contentModificationDate = entry.modified", attributes)
        self.assertNotIn("Date()", attributes)

    def test_guard_rejects_edit_date_creation_date_fallback_or_nonoptional_projection(self):
        for changed in [
            self.index.replace("modified = item.isInHistory ? item.createdAt : nil", "modified = item.updatedAt"),
            self.index.replace("modified = item.isInHistory ? item.createdAt : nil", "modified = item.createdAt"),
            self.index.replace("let modified: Date?", "let modified: Date"),
            self.index.replace("modified = item.isInHistory ? item.createdAt : nil", "modified = Date()"),
        ]:
            self.assertFalse(optional_history_date(changed))

    def test_capture_and_visible_order_use_the_same_compatibility_timestamp(self):
        store = (CORE / "ClipboardStore.swift").read_text()
        capture = body(body(store, "func addWithInsertionResult("), "if recordCapture")
        self.assertIn("state.items[result.index].createdAt = timestamp", capture)
        self.assertIn("state.items[result.index].isInHistory = true", capture)
        visible = body(self.ui, "var visibleItems: [ClipboardItem]")
        self.assertIn("return $0.createdAt > $1.createdAt", visible)
        self.assertIn("guard $0.isInHistory else { return false }", visible)

    def test_regular_tab_selection_does_not_call_the_reveal_query_reset_entry(self):
        original = self.original("0x100099adc")
        self.assertIn("FUN_100039c50(SVar1.str,SVar1.bridgeObject,1)", original)
        self.assertNotIn("FUN_10007d9c8", original)
        self.assertNotIn("FUN_1002ddf60", original)
        choose = body(self.ui, "func chooseBoard(_ id: UUID?)")
        self.assertNotIn("applySearchInput(", choose)
        self.assertNotIn("searchInputChanged()", choose)

    def test_reveal_callback_clears_query_before_selecting_list(self):
        original = self.original("0x10007d9c8")
        self.assertLess(original.index("FUN_1002ddf60()"), original.index("FUN_100039c50("))
        self.assertIn("FUN_10007d9c8(param_1)", self.original("0x100036860"))
        reveal = self.original("0x10006c338")
        self.assertLess(reveal.index("::pendingFocus"), reveal.index("::onSelectList"))

    def test_closed_automatic_routes_keep_query_and_normal_restore_guard(self):
        closed = body(self.ui, "private func beginClosedState()")
        create_restore = closed[:closed.index("closedSearchTimer = Timer.")]
        self.assertEqual(create_restore.count("self.state.chooseBoard(nil)"), 2)
        self.assertNotIn("applySearchInput(", create_restore)
        self.assertIn("self.state.isCollectionSearchQueryEmpty, self.state.pinboardID == nil", create_restore)
        for address in ["0x1000217a8", "0x100021908"]:
            self.assertNotIn("FUN_1002ddf60", self.original(address))


if __name__ == "__main__":
    unittest.main()
