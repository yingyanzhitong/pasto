"""Offline repository/capture source contracts; never executes Swift or an app."""
import json
import struct
import unittest

from test_offline_p0_contracts import ROOT, CORE, body
from native_stack_rendering_scope_contract import pre_native_stack_rendering


class CaptureRepositoryContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = {r["address"]: r for r in json.loads((ROOT / "reports/Paste/function-index.json").read_text())}
        cls.store = (CORE / "ClipboardStore.swift").read_text()
        cls.pasteboard = (CORE / "Pasteboard.swift").read_text()
        cls.ui = pre_native_stack_rendering((ROOT / "replica/Sources/Pasto/UI/ReplicaUIController.swift").read_text())

    @classmethod
    def original(cls, address):
        text = (ROOT / cls.index[address]["file"]).read_text()
        start = text.index("/* Address: " + address + " |")
        end = text.find("/* Address:", start + 1)
        return text[start:end if end != -1 else None]

    def test_original_device_is_set_on_creation_but_not_checksum_hit(self):
        self.assertIn("objc_stub::setDevice_", self.original("0x100360d9c"))
        for address in ["0x100360ff8", "0x100364ab4", "0x10037b204", "0x100361ec0"]:
            with self.subTest(address=address):
                self.assertNotIn("objc_stub::setDevice_", self.original(address))
        add = body(self.store, "func addWithInsertionResult(")
        self.assertNotIn("state.items[i].sourceDevice =", add)
        self.assertIn("state.items.append(item)", add, "New records still retain their input creation device")
        self.assertNotIn("state.items[i].title =", add)
        self.assertNotIn("state.items[i].id =", add)

    def test_actual_capture_stamps_history_after_content_source_and_identity_updates(self):
        add = body(self.store, "func addWithInsertionResult(")
        stamp = body(add[add.rindex("if recordCapture"):], "if recordCapture")
        self.assertIn("let timestamp = transaction.repository.restoreHistoryItems([target!])[0].timestamp", stamp)
        self.assertIn("state.items[result.index].createdAt = timestamp", stamp)
        self.assertIn("state.items[result.index].updatedAt = timestamp", stamp)
        self.assertIn("state.items[result.index].isInHistory = true", stamp)
        for token in ["Self.withPreviewMetadata(", "Self.upsertSourceApplication(",
                      "let result: (index: Int, isNew: Bool)", "result = (i, false)",
                      "result = (state.items.count - 1, true)"]:
            self.assertLess(add.index(token), add.rindex("if recordCapture"))
        self.assertLess(add.rindex("if recordCapture"), add.index("return (state.items[result.index].id, result.isNew)"))
        self.assertIn("mutateInTransaction(historyAction: recordCapture || item.isInHistory)", add)
        capture = body(self.pasteboard, "func captureWithInsertionResult(")
        self.assertIn("sourceApplication: sourceApplication, recordCapture: true", capture)

    def test_general_value_addition_keeps_explicit_dates_without_capture_promotion(self):
        self.assertIn("recordCapture: Bool = false", self.store)
        value_add = body(self.store, "public func add(_ item: ClipboardItem,")
        self.assertNotIn("recordCapture: true", value_add)
        self.assertNotIn("Date()", value_add)
        add = body(self.store, "func addWithInsertionResult(")
        self.assertIn("if item.isInHistory { state.items[i].createdAt = item.createdAt }", add)
        capture = body(add[add.rindex("if recordCapture"):], "if recordCapture")
        for preserved in ["sourceDevice =", "title =", "pinboardIDs =", "pinboardOwnerID ="]:
            self.assertNotIn(preserved, capture)

    def test_original_repository_distinguishes_empty_lookup_create_and_update(self):
        repository = self.original("0x1003611b0")
        self.assertLess(repository.index("if (puVar2 == (undefined1 *)0x0)"), repository.index("FUN_1003214c8("))
        self.assertIn("_swift_willThrow", repository)
        self.assertIn("FUN_100360d9c()", repository)
        self.assertIn("FUN_100360ff8(puVar3,param_1)", repository)
        lookup = self.original("0x1003214c8")
        order = ["FUN_10032362c()", "FUN_1003216bc()", "if (lVar1 == 0)", "FUN_100328950("]
        self.assertEqual([lookup.index(t) for t in order], sorted(lookup.index(t) for t in order))
        update = self.original("0x100360ff8")
        order = ["setRawType_", "setChecksum_", "deleteObject_", "FUN_10031a8e8()", "setData_", "FUN_100322504("]
        self.assertEqual([update.index(t) for t in order], sorted(update.index(t) for t in order))

    def test_is_new_flag_distinguishes_checksum_hit_from_creation_without_changing_id(self):
        proof = json.loads((ROOT / "reports/replica/offline-migration-p0-round8.json").read_text())["static_bindings"]
        self.assertEqual(struct.unpack("<II", bytes.fromhex(proof["is_new_instructions"]["bytes"])),
                         (0xf10002ff, 0x1a9f17e8))  # cmp x23, #0; cset w8, eq
        add = body(self.store, "func addWithInsertionResult(")
        self.assertIn("result = (i, false)", add)
        self.assertIn("result = (state.items.count - 1, true)", add)
        self.assertIn("return (state.items[result.index].id, result.isNew)", add)
        self.assertNotIn("state.items[i].id =", add)
        capture = body(self.pasteboard, "func f_10037b034(_ items:")
        self.assertIn("return captured.isNew", capture)

    def test_stack_production_capture_consumes_success_notification_not_pre_undo_callback(self):
        app = (ROOT / "replica/Sources/Pasto/AppMain.swift").read_text()
        self.assertNotIn("monitor?.onCapture =", app)
        create = body(self.pasteboard, "func f_10037ae9c(_ items:")
        self.assertLess(create.index("removeAllActions()"), create.index("Self.didCaptureItemNotification"))
        show = body(self.ui, "func showStack()")
        once = body(show, "if stackWindow == nil")
        self.assertIn("stackCaptureObserver = NotificationCenter.default.addObserver(", once)
        self.assertIn("forName: ClipboardMonitor.didCaptureItemNotification, object: nil, queue: nil", once)
        self.assertIn("[weak self]", once)
        self.assertIn("MainActor.assumeIsolated { self?.captureLatestItemIntoStack() }", once)
        self.assertEqual(self.ui.count("stackCaptureObserver = NotificationCenter.default.addObserver("), 1)
        deinit = body(self.ui, "deinit")
        self.assertIn("if let stackCaptureObserver { NotificationCenter.default.removeObserver(stackCaptureObserver) }", deinit)

    def test_stack_uses_latest_history_instead_of_current_panel_query_or_raw_storage_order(self):
        capture = body(self.ui, "private func captureLatestItemIntoStack()")
        self.assertIn("store.makeListCollection(pinboardID: nil)", capture)
        self.assertIn("snapshot.identifiers.first", capture)
        self.assertIn("reference.requiredRestoreItem(id: identifier)", capture)
        self.assertIn("state.addToStack(input.resolvedItem(), restoreItem: input)", capture)
        for wrong_scope in ["visibleItems", "selection", "store.items.first", "store.search", "state.pinboardID"]:
            self.assertNotIn(wrong_scope, capture)
        factory = body(self.store, "public func makeListCollection(pinboardID:")
        self.assertIn("pinboardID?.uuidString ?? Self.historyListIdentifier", factory)
        history_request = body((CORE / "ClipboardListPersistence.swift").read_text(), "func itemRequest(for list:")
        self.assertIn('NSSortDescriptor(key: "timestamp", ascending: false)', history_request)
        self.assertIn('NSPredicate(format: "timestamp != nil")', history_request)

    def test_empty_history_query_checks_scope_before_skipping_content_decoding(self):
        query = body(self.store, "public func search(query:")
        filtering = body(query, "let matches = items.filter")
        self.assertLess(filtering.index("else { return false }"), filtering.index("if terms.isEmpty { return true }"))
        self.assertLess(filtering.index("if terms.isEmpty { return true }"), filtering.index("item.recognizedText"))
        self.assertIn("return terms.allSatisfy { haystack.contains($0) }", filtering)
        original = self.original("0x100329088")
        self.assertNotIn("objc_stub::data(", original)
        self.assertNotIn("FUN_10037c9a8(", original)

    def test_original_stack_subscription_and_weak_callback_take_first_history_item(self):
        registration = self.original("0x100082f5c")
        self.assertIn("FUN_10037a75c()", registration)
        self.assertIn("_swift_unknownObjectWeakInit", registration)
        self.assertIn("local_70 = FUN_100086a30", registration)
        self.assertIn("uVar10,0,0,aBlock", registration)
        self.assertIn("FUN_10008333c()", self.original("0x100086a30"))
        self.assertIn("FUN_1000582d0(FUN_100086a40", self.original("0x10008333c"))
        self.assertIn("FUN_10008339c()", self.original("0x100086a40"))
        callback = self.original("0x10008339c")
        self.assertIn("FUN_100357f60(&local_a0,FUN_100083758", callback)
        self.assertIn("FUN_1001b8054(&local_58,0,", callback)
        self.assertIn("if (local_58 == 0)", callback)
        provider = self.original("0x100083758")
        self.assertIn("lStack_80 + 0x28", provider)
        self.assertIn("lStack_58 + 0x10", provider)

    def test_static_history_provider_slots_and_query_constants_match_bound_bytes(self):
        proof = json.loads((ROOT / "reports/replica/offline-migration-p0-round8.json").read_text())["static_bindings"]
        expected = {"0x100eccab0": "0x100363d58", "0x100eccd98": "0x100368230"}
        for row in proof["slots"]:
            raw = int.from_bytes(bytes.fromhex(row["bytes"]), "little")
            self.assertEqual(row["pointer_format"], 6)
            self.assertTrue(row["chain_reachability_confirmed"])
            self.assertFalse(raw >> 63)
            self.assertEqual(hex(0x100000000 + (raw & ((1 << 36) - 1))), expected[row["slot"]])
        self.assertEqual({r["slot"] for r in proof["slots"]}, set(expected))
        registers = {}
        def materialize_wide_constants(data):
            # Decode immediate constant materialization only, not program control
            # flow or runtime function execution.
            for word, in struct.iter_unpack("<I", data):
                opcode = word & 0x7f800000
                register, shift, immediate = word & 31, ((word >> 21) & 3) * 16, (word >> 5) & 0xffff
                if opcode == 0x52800000: registers[register] = immediate << shift
                elif opcode == 0x72800000:
                    registers[register] = (registers[register] & ~(0xffff << shift)) | (immediate << shift)
        rows = {r["address"]: bytes.fromhex(r["bytes"]) for r in proof["history_query_instructions"]}
        materialize_wide_constants(rows["0x10032910c"])
        small_string = struct.pack("<QQ", registers[20], registers[25])[:9].decode()
        self.assertEqual(small_string, "timestamp")
        materialize_wide_constants(rows["0x100329140"])
        self.assertEqual(registers[3], 0)
        predicate = rows["0x1003291fc"]
        self.assertEqual(struct.unpack_from("<I", predicate)[0], 0xd1001321)  # sub x1, x25, #4
        materialize_wide_constants(predicate)
        self.assertEqual(struct.pack("<QQ", registers[0], registers[25] - 4)[:9].decode(), "%K != nil")


if __name__ == "__main__":
    unittest.main()
