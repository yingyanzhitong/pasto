from capture_lifecycle_scope_contract import pre_capture_lifecycle
from shared_pasteboard_state_scope_contract import pre_shared_pasteboard_state
from native_restore_writer_scope_contract import pre_native_restore_writer
"""Source-contract guards only: no compiler, application, network or Swift execution."""
from native_title_scope_contract import pre_native_title
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "replica/Sources/PastoCore"


def body(text, signature):
    if text.count(signature) != 1:
        raise ValueError("Signature must identify exactly one method: " + signature)
    start = text.index("{", text.index(signature) + len(signature))
    # Retain offsets while masking ordinary strings and comments. Multiline
    # strings are intentionally unsupported rather than silently misparsed.
    if '"""' in text[start:]:
        raise ValueError("Multiline strings require a separate source review")
    token = r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*[\s\S]*?\*/'
    masked = re.sub(token, lambda m: " " * len(m.group()), text)
    depth = 0
    for index in range(start, len(masked)):
        depth += (masked[index] == "{") - (masked[index] == "}")
        if depth == 0:
            return text[start:index + 1]
    raise ValueError("Unclosed method")


def trace(text, pattern):
    return re.findall(pattern, text)


def valid_event_read_order(text):
    return trace(text, r"event\.(modifierFlags|keyCode)") == ["modifierFlags", "keyCode"]


def valid_menu_read_order(text):
    return trace(text, r"item\.(submenu|keyEquivalentModifierMask|keyEquivalent)\b|"
                 r"OriginalShortcutFunctions\.(f_1001e8098)\b") == [
        ("submenu", ""), ("keyEquivalentModifierMask", ""),
        ("keyEquivalent", ""), ("", "f_1001e8098"),
        ("keyEquivalent", ""), ("", "f_1001e8098")]


class OfflineP0Contracts(unittest.TestCase):
    def test_modifier_table_matches_bound_original_bytes(self):
        evidence = json.loads((ROOT / "reports/replica/offline-migration-p0-round1.json").read_text())["original_static_constants"]
        text = body((CORE / "OriginalShortcutFunctions.swift").read_text(),
                    "func f_1001e7d58(modifierRawValue: UInt) -> UInt32")
        pairs = [[int(a, 16), int(b, 16)] for a, b in re.findall(r"\((0x[0-9a-f]+), (0x[0-9a-f]+)\)", text)]
        self.assertEqual(pairs, evidence["modifier_pairs"])
        self.assertIn("modifierRawValue & appKit == appKit", text)
        self.assertIn("result |= carbon", text)

    def test_function_key_set_matches_bound_original_bytes(self):
        evidence = json.loads((ROOT / "reports/replica/offline-migration-p0-round1.json").read_text())["original_static_constants"]
        text = (CORE / "OriginalShortcutFunctions.swift").read_text()
        values = re.search(r"functionKeyCodes: \[UInt32\] = \[([^]]+)\]", text).group(1)
        actual = [int(value.strip()) for value in values.split(",") if value.strip()]
        contract = body(text, "func f_1001ebc2c(keyCode: Int, modifierRawValue: UInt) -> Bool")
        self.assertIn("keyCode == 90", contract)
        self.assertIn("modifierRawValue & 0x1c0000 != 0", contract)
        self.assertEqual(actual + [90], evidence["function_key_codes"])

    def test_leaf_keycodes_match_original_exports(self):
        index = {row["address"]: row for row in json.loads((ROOT / "reports/Paste/function-index.json").read_text())}
        source = (CORE / "OriginalShortcutFunctions.swift").read_text()
        for address in ["0x1001e95fc", "0x1001e9610", "0x1001e9624", "0x1001e9638", "0x1001e964c"]:
            with self.subTest(address=address):
                original = (ROOT / index[address]["file"]).read_text()
                start = original.index("/* Address: " + address + " |")
                end = original.find("/* Address:", start + 1)
                fragment = original[start:end if end != -1 else None]
                original_value = re.search(r"return (0x[0-9a-f]+|[0-9]+);", fragment).group(1)
                actual = body(source, "func f_" + address[2:] + "() -> Int")
                actual_value = re.fullmatch(r"\{\s*(?:return\s+)?(0x[0-9a-f]+|[0-9]+)\s*\}", actual).group(1)
                self.assertEqual(int(actual_value, 0), int(original_value, 0))

    def test_event_getters_follow_original_order(self):
        text = body((CORE / "OriginalShortcutFunctions.swift").read_text(),
                    "func f_1001e7d18(_ event: NSEvent) -> KeyboardShortcut")
        self.assertTrue(valid_event_read_order(text))
        self.assertIn("modifierRawValue: modifiers & eventModifierMask", text)
        self.assertIn("eventModifierMask: UInt = 0xff5f0000",
                      (CORE / "OriginalShortcutFunctions.swift").read_text())

    def test_event_guard_rejects_old_eager_argument_order(self):
        self.assertFalse(valid_event_read_order("keyCode: event.keyCode, flags: event.modifierFlags"))

    def test_system_conflict_precedes_lazy_menu_evaluation(self):
        text = (CORE / "OriginalShortcutValidation.swift").read_text()
        signatures = ["func f_1001ebce4(shortcut: " + kind + ", menu: @autoclosure () -> NSMenu?) -> OriginalShortcutRecorderError?"
                      for kind in ["KeyboardShortcut", "OriginalShortcutValue"]]
        wrapper, implementation = [body(text, signature) for signature in signatures]
        self.assertEqual(wrapper.count("menu()"), 1)
        self.assertEqual(implementation.count("menu()"), 1)
        self.assertLess(implementation.index("CopySymbolicHotKeys"), implementation.index("menu()"))
        self.assertLess(implementation.index('return OriginalShortcutRecorderError(OriginalShortcutMessages.value("shortcut-recorder.error.used-in-system"))'),
                        implementation.index("menu()"))
        service = (CORE / "OriginalShortcutDependencies.swift").read_text()
        self.assertIn("f_1001ebce4(shortcut: shortcut, menu: NSApp.mainMenu)", service)

    def test_menu_traversal_preserves_reads_and_repeated_layout_lookup(self):
        text = body((CORE / "OriginalShortcutValidation.swift").read_text(),
                    "func f_1001ec200(shortcut: OriginalShortcutValue, menu: NSMenu?) -> OriginalShortcutRecorderError?")
        self.assertTrue(valid_menu_read_order(text))
        self.assertLess(text.index("guard equivalent == candidate"), text.index("let exactEquivalent"))
        self.assertIn("rawModifiers & 0x1e0000", text)
        self.assertIn("(rawModifiers & 0x1c0000) | 0x20000", text)

    def test_menu_guard_rejects_coalesced_and_reordered_getters(self):
        self.assertFalse(valid_menu_read_order("item.submenu; OriginalShortcutFunctions.f_1001e8098(); "
                                              "item.keyEquivalent; item.keyEquivalentModifierMask; item.keyEquivalent"))

    def test_conflict_producers_return_errors_without_outer_reboxing(self):
        text = (CORE / "OriginalShortcutValidation.swift").read_text()
        system = body(text, "func f_1001ebce4(shortcut: OriginalShortcutValue,")
        menu = body(text, "func f_1001ec200(shortcut: OriginalShortcutValue,")
        self.assertIn('return OriginalShortcutRecorderError(OriginalShortcutMessages.value("shortcut-recorder.error.used-in-system"))', system)
        self.assertIn('return OriginalShortcutRecorderError(OriginalShortcutMessages.menuConflict(item.title))', menu)
        self.assertIn('if let failure = f_1001ec200(shortcut: shortcut, menu: item.submenu) { return failure }', menu)
        service = body((CORE / "OriginalShortcutDependencies.swift").read_text(),
                       "func validate(_ shortcut: OriginalShortcutValue) -> Error?")
        self.assertNotIn("OriginalShortcutRecorderError(", service)
        self.assertNotIn("let message", service)
        self.assertIn("OriginalShortcutValidation.f_1001ebce4", service)

    def test_recording_passes_through_only_close_quit_and_invalid_plain_keys(self):
        text = body((CORE / "OriginalShortcutRecorder.swift").read_text(),
                    "func f_1001f132c(_ event: NSEvent) -> NSEvent?")
        self.assertEqual(text.count("return event"), 2)
        order = ["f_1001e9610()", "f_1001e95fc()", 'f_1001e94d4("w")',
                 "if key.isEmpty", "guard OriginalShortcutFunctions.f_1001ebc2c", "if let failure", "onDetect(shortcut)"]
        positions = [text.index(token) for token in order]
        self.assertEqual(positions, sorted(positions))
        failure = body(text, "if let failure = validate.validate(shortcut)")
        self.assertLess(failure.index("f_1001eff84()"), failure.index("validationError = failure"))
        self.assertLess(text.index("onDetect(shortcut)"), text.index("f_1001f1150(newState: .assigned(shortcut))"))

    def test_recording_monitor_is_replaced_and_removed_after_state_update(self):
        text = (CORE / "OriginalShortcutRecorder.swift").read_text()
        start = body(text, "func f_1001eff84()")
        self.assertLess(start.index("state = .recording"), start.index("NSEvent.removeMonitor"))
        self.assertLess(start.index("NSEvent.removeMonitor"), start.index("NSEvent.addLocalMonitorForEvents"))
        self.assertIn("matching: [.keyDown, .flagsChanged]", start)
        stop = body(text, "func f_1001f1150(newState: OriginalShortcutRecorderState?)")
        self.assertLess(stop.index("if let newState"), stop.index("NSEvent.removeMonitor"))
        self.assertLess(stop.index("NSEvent.removeMonitor"), stop.index("self.eventMonitor = nil"))

    def test_hotkey_replacement_keeps_failed_registration_out_of_dictionary(self):
        text = body((CORE / "OriginalGlobalShortcutMonitor.swift").read_text(),
                    "func registerShortcut(shortcut: OriginalShortcutValue, action: @escaping () -> Void) -> OSStatus")
        self.assertLess(text.index("f_1001eae90(shortcut:"), text.index("OriginalShortcutRegistration("))
        success = body(text, "if registration.status == noErr")
        self.assertLess(success.index("lock.lock()"), success.index("f_1001eb1e4("))
        self.assertLess(success.index("f_1001eb1e4("), success.index("lock.unlock()"))
        self.assertEqual(text.count("f_1001eb1e4("), 1)

    def test_carbon_delivery_ignores_parameter_status_and_signature(self):
        text = body((CORE / "OriginalGlobalShortcutMonitor.swift").read_text(),
                    "func f_1001ea338(_ event: EventRef)")
        self.assertIn("guard GetEventClass(event) == OSType(kEventClassKeyboard)", text)
        self.assertIn("var identifier = EventHotKeyID()", text)
        self.assertIn("_ = GetEventParameter(", text)
        self.assertIn("$0.identifier == identifier.id", text)
        self.assertNotIn("identifier.signature", text)
        self.assertLess(text.index("lock.unlock()"), text.index("guard let action"))
        self.assertIn("DispatchQueue.main.async(execute: action)", text)

    def test_restore_saves_before_undo_and_notification(self):
        text = body(pre_native_restore_writer((CORE / "Pasteboard.swift").read_text()),
                    "private func writeToPasteboard(ids: [UUID], pasteboard: NSPasteboard,")
        tokens = ["writer.f_10037875c(objects)", "try recordRestoredSelection(restoration)",
                  "removeAllActions()", "didRestoreItem.send()"]
        positions = [text.index(token) for token in tokens]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("asyncAfter", text)

    def test_restore_uses_reverse_order_and_commit_before_publish(self):
        text = (CORE / "ClipboardStore.swift").read_text()
        restore = body(text, "func recordRestoredItems(_ ids: [UUID]) throws")
        self.assertIn("try mutate(historyAction: true, restoringItemIDs: ids)", restore)
        native_restore = body((CORE / 'ClipboardPersistence.swift').read_text(), 'func restoreHistoryItems(')
        self.assertIn('for (id, object) in targets.reversed()', native_restore)
        self.assertLess(native_restore.index('let timestamp = Date()'),
                        native_restore.index('object.setValue(timestamp, forKey: "timestamp")'))
        mutate = body(text, "private func mutateInTransaction<T>(historyAction: Bool = false,")
        self.assertLess(mutate.index("try persistence.commit(previous: remote, deletingItemIDs: deletingItemIDs,"), mutate.index("publish(state)"))

    def test_copy_feedback_and_panel_close_follow_successful_write(self):
        text = (ROOT / "replica/Sources/Pasto/UI/ReplicaUIController.swift").read_text()
        action = body(text, "private func performCopy(_ write: () throws -> Void)")
        positions = [action.index(token) for token in ["try write()", "copiedItemsHandler?()", "hidePanel()"]]
        self.assertEqual(positions, sorted(positions))

    def test_plain_projection_source_truth_table_matches_original_two_bits(self):
        source = (CORE / "OriginalPasteboardRestore.swift").read_text()
        flags = {name: 1 << int(bit) for name, bit in re.findall(
            r"static let (\w+) = Options\(rawValue: 1 << (\d+)\)", source)}
        gate = body(source, "func usesPlainProjection(kind: OriginalPasteboardContentKind, options: Options) -> Bool")
        parsed = re.fullmatch(r"\{\s*options.contains\(kind == \.(\w+) \|\| kind == \.(\w+)"
                              r" \? \.(\w+) : \.(\w+)\)\s*\}", gate)
        self.assertIsNotNone(parsed, "Unsupported gate shape needs renewed original-code review")
        a, b, yes, no = parsed.groups()
        # Original 0x10038222c: rawType 5/4 uses bit 1; all other types use bit 0.
        for kind, raw_type in [("text", 5), ("link", 4), ("image", 1),
                               ("files", 3), ("color", 2), ("unknown", 0)]:
            for mask in range(4):
                with self.subTest(kind=kind, mask=mask):
                    source_result = bool(mask & flags[yes if kind in [a, b] else no])
                    original_result = bool(mask & (2 if raw_type in [5, 4] else 1))
                    self.assertEqual(source_result, original_result)

    def test_aggregate_keeps_attributed_input_and_uses_utf16_export_range(self):
        source = (CORE / "OriginalPasteboardRestore.swift").read_text()
        join = body(source, "func f_100383a0c(separator: String, contents: [NSAttributedString]) -> NSMutableAttributedString")
        self.assertIn('if !result.string.isEmpty { result.append(NSAttributedString(string: separator)) }', join)
        self.assertIn("result.append(content)", join)
        self.assertNotIn("content.string", join, "Joining must not replace source attributes with plain strings")
        export = body(source, "func f_100381fdc(_ content: NSAttributedString) -> Data?")
        self.assertIn("try? content.data", export)
        self.assertIn("NSRange(location: 0, length: content.length)", export)
        self.assertIn(".documentType: NSAttributedString.DocumentType.rtf", export)
        self.assertIn(".characterEncoding: String.Encoding.utf8", export)

    def test_writer_preserves_ordered_types_empty_data_and_empty_write(self):
        source = body(pre_shared_pasteboard_state((CORE / "OriginalPasteboard.swift").read_text()),
                      "func f_10037875c(_ items: [OriginalPasteboardItem])")
        self.assertIn("for type in item.f_10037da6c()", source)
        self.assertIn("if let data = item.f_10037e5e0(forType: type)", source)
        self.assertNotIn("isEmpty", source, "The original clears/writes even zero items and does not discard empty data")
        positions = [source.index(x) for x in ["pasteboard.clearContents()", "pasteboard.writeObjects(objects)",
                                              "lastChangeCount = pasteboard.changeCount"]]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("guard lastWriteSucceeded", source)

    def test_explicit_representation_containers_block_display_text_fallback(self):
        source = body((CORE / "Pasteboard.swift").read_text(),
                      "func ordinaryRestoreRepresentations(for item: ClipboardItem,")
        boundary = source[source.index("let allowsLegacyText"):source.index("for object in representations")]
        for key in ["originalItemDataPayloadKey", "orderedTypesPayloadKey", "multiItemPayloadKey"]:
            self.assertIn("item.payloads[" + key + "] == nil", boundary)
        self.assertEqual(source.count("if allowsLegacyText,"), 2)
        self.assertNotIn("recognizedText", source)
        write = body((CORE / "Pasteboard.swift").read_text(),
                     "private func writeToPasteboard(ids: [UUID], pasteboard: NSPasteboard,")
        self.assertIn("guard kind == .image, item.imageData == recognizedImageData", write)
        self.assertIn("let application = sourceApplication(for: item)", write)
        self.assertIn("sourceBundleID: application?.bundleIdentifier", write)
        self.assertNotIn("item.sourceBundleID", write)
        self.assertNotIn("NSWorkspace", write)

    def test_incremental_commit_does_not_encode_binary_content_for_timestamp_only_change(self):
        source = pre_native_title((CORE / "ClipboardPersistence.swift").read_text())
        normalized = body(source, "private func content(_ item: ClipboardItem) -> ClipboardItem")
        self.assertIn("value.createdAt = Date(timeIntervalSinceReferenceDate: 0)", normalized)
        self.assertIn("value.updatedAt = value.createdAt; value.isInHistory = false", normalized)
        commit = body(source, "func commit<T>(previous: StoreState?, deletingItemIDs: [UUID] = [],")
        encoded = body(commit, "if old.map(content) != content(item)")
        self.assertIn('object.setValue(try encode(content(item)), forKey: "content")', encoded)
        save = body(commit, "if context.hasChanges")
        self.assertIn("try context.save()", save)
        self.assertEqual(commit.count("try context.save()"), 1)
        self.assertIn("try context.performAndWait", commit)
        self.assertIn("try OriginalObjCExceptionBridge.f_1002ff9c8 { try context.save() }", commit)
        self.assertNotIn("rollback", commit)

    def test_character_sender_preserves_nullable_source_and_independent_events(self):
        source = body((CORE / "OriginalPasteKeyTranslation.swift").read_text(),
                      "func f_100ae6428(_ character: Character)")
        order = ["let source = CGEventSource(", "let down = CGEvent(", "down?.flags = .maskCommand",
                 "let up = CGEvent(", "down?.post(tap: .cgAnnotatedSessionEventTap)",
                 "up?.post(tap: .cgAnnotatedSessionEventTap)"]
        positions = [source.index(token) for token in order]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("guard let source", source)
        self.assertNotIn("guard let down", source)
        self.assertNotIn("guard let up", source)
        self.assertEqual(source.count("keyboardEventSource: source"), 2)
        # The original posts whichever events exist, even when the source or
        # the other event could not be allocated. This is a source-branch table.
        optional_posts = re.findall(r"\b(down|up)\?\.post\(", source)
        for has_source in [False, True]:
            for has_down in [False, True]:
                for has_up in [False, True]:
                    with self.subTest(source=has_source, down=has_down, up=has_up):
                        present = {"down": has_down, "up": has_up}
                        actual = [event for event in optional_posts if present[event]]
                        expected = (["down"] if has_down else []) + (["up"] if has_up else [])
                        self.assertEqual(actual, expected)

    def test_character_lookup_is_generic_and_main_actor_sender_uses_paste_wrapper(self):
        text = (CORE / "OriginalPasteKeyTranslation.swift").read_text()
        lookup = body(text, "func keyCode(for character: Character) -> CGKeyCode?")
        self.assertIn("for code in UInt16(0)..<UInt16(128)", lookup)
        self.assertIn("f_100ae6678(keyCode: code) == String(character)", lookup)
        self.assertNotIn('== "v"', lookup)
        self.assertNotIn("return 9", lookup)
        wrapper = body(text, "func f_100ae641c()")
        self.assertRegex(wrapper, r'^\{\s*f_100ae6428\("v"\)\s*\}$')
        app = (ROOT / "replica/Sources/Pasto/AppMain.swift").read_text()
        self.assertIn("@MainActor\nfinal class ReplicaAppDelegate", app)
        sender = body(app, "private func f_100053988() async")
        self.assertIn("OriginalPasteKeyTranslation.f_100ae641c()", sender)
        self.assertNotIn("CGEvent(", sender)

    def test_direct_paste_schedules_after_restore_before_deactivation_without_polling(self):
        from modal_restore_scope_contract import pre_modal_restore
        source = pre_modal_restore((ROOT / "replica/Sources/Pasto/AppMain.swift").read_text())
        action = body(source, "private func paste(ids: [UUID], plain: Bool, forceDirect: Bool = false) -> Bool")
        self.assertLess(action.index("try store.writeToPasteboard"), action.index("Task { @MainActor [self] in"))
        task = action.index("Task { @MainActor [self] in")
        deactivation = action.index("NSApp.deactivate()", task)
        self.assertLess(task, deactivation)
        self.assertIn("await self.f_100053988()", action[task:deactivation])
        self.assertLess(action.index("guard pasteboard.name == NSPasteboard.general.name"), task)
        self.assertLess(action.index("guard !copyInsteadOfPaste"), task)
        for removed in ["waitForTarget(", "pasteGeneration", "yieldActivation", "activation_timeout"]:
            self.assertNotIn(removed, source)
        self.assertNotIn("asyncAfter", action)
        self.assertNotIn("target.activate", action)

    def test_permission_setup_exit_cannot_schedule_the_same_paste(self):
        from modal_restore_scope_contract import pre_modal_restore
        source = pre_modal_restore((ROOT / "replica/Sources/Pasto/AppMain.swift").read_text())
        action = body(source, "private func paste(ids: [UUID], plain: Bool, forceDirect: Bool = false) -> Bool")
        setup = body(action, "if result == 2")
        self.assertIn("OriginalEnableAccessibilityModal.run(requestOnShow: true)", setup)
        self.assertIn("return false", setup)
        self.assertNotIn("Task", setup)
        self.assertNotIn("writeToPasteboard", setup)
        self.assertLess(action.index("if result == 2"), action.index("try store.writeToPasteboard"))

    def test_focus_handoff_remains_before_animation_and_clears_saved_application(self):
        panel = (ROOT / "replica/Sources/Pasto/UI/ReplicaUIController.swift").read_text()
        close = body(panel, "func hidePanel()")
        self.assertLess(close.index("panelWillClose?(previewRegistry.windows.isEmpty)"),
                        close.index("OriginalViewAnimation.f_10021cadc"))
        app = (ROOT / "replica/Sources/Pasto/AppMain.swift").read_text()
        restore = body(app, "private func restorePanelApplication(restore: Bool)")
        self.assertIn("defer { handoffPreviousApplication = nil }", restore)
        self.assertIn("guard restore", restore)
        self.assertIn("previous.activate(options: .activateIgnoringOtherApps)", restore)

    def test_original_task_descriptor_and_resume_chain_match_static_binding(self):
        evidence = json.loads((ROOT / "reports/replica/offline-migration-p0-round4.json").read_text())["async_descriptor_binding"]
        import struct
        for row in evidence["descriptors"]:
            relative, frame = struct.unpack("<iI", bytes.fromhex(row["bytes"]))
            self.assertEqual(int(row["descriptor_address"], 16) + relative, int(row["target"], 16))
            self.assertEqual(frame, row["async_frame_size"])
        index = {r["address"]: r for r in json.loads((ROOT / "reports/Paste/function-index.json").read_text())}
        for address, expected in [("0x100076018", "FUN_100053988"),
                                  ("0x100053988", "_swift_task_switch(FUN_100053a18"),
                                  ("0x100053a18", "FUN_100ae641c()"),
                                  ("0x100ae641c", "FUN_100ae6428(0x76,0xe100000000000000)")]:
            text = (ROOT / index[address]["file"]).read_text()
            start = text.index("/* Address: " + address + " |")
            end = text.find("/* Address:", start + 1)
            self.assertIn(expected, text[start:end if end != -1 else None])

    def test_delete_requires_live_selection_and_never_falls_back_to_first_item(self):
        source = (ROOT / "replica/Sources/Pasto/UI/ReplicaUIController.swift").read_text()
        action = body(source, "func deleteSelection()")
        self.assertIn("orderedSelectionIDs.filter { selection.contains($0) && visibleIDs.contains($0) }", action)
        self.assertLess(action.index("guard !orderedIDs.isEmpty"), action.index("pendingItemDeletion ="))
        for fallback in ["primaryItem", "visibleItems.first", "selection.isEmpty ?"]:
            self.assertNotIn(fallback, action)
        self.assertIn("guard !hasPendingDeletion else { return }", action)

    def test_multi_delete_is_snapshot_then_confirm_not_immediate_mutation(self):
        source = (ROOT / "replica/Sources/Pasto/UI/ReplicaUIController.swift").read_text()
        action = body(source, "func deleteSelection()")
        self.assertNotIn("try store.", action)
        self.assertIn("if ids.count < 2 { confirmItemDeletion() }", action)
        self.assertLess(action.index("neighborID ="), action.index("pendingItemDeletion ="))
        self.assertLess(action.index("pendingItemDeletion ="), action.index("if ids.count < 2"))
        request = body(source, "struct ItemDeletionRequest")
        self.assertNotIn("var ", request)
        for field in ["ids: Set<UUID>", "contextPinboardID: UUID?", "permanently: Bool",
                      "beforeIDs: [UUID]", "neighborID: UUID?"]:
            self.assertIn("let " + field, request)

    def test_confirm_uses_ordered_ids_captured_kind_and_current_context_without_hiding_panel(self):
        source = (ROOT / "replica/Sources/Pasto/UI/ReplicaUIController.swift").read_text()
        confirm = body(source, "func confirmItemDeletion()")
        self.assertIn("executeItemDeletion(request)", confirm)
        action = body(source, "private func executeItemDeletion(")
        complete = body(source, "private func completeItemDeletion(")
        self.assertIn("if request.permanently { try store.permanentlyDelete(orderedIDs: request.orderedIDs) }", action)
        self.assertIn("currentPinboardID: { [self] in pinboardID }", action)
        self.assertIn("let neighborID = request.neighborID", complete)
        self.assertIn("items.map(\\.id) != request.beforeIDs", complete)
        for dynamic_scope in ["isSearchQueryEmpty", "isCollectionSearchQueryEmpty", "showDeleted"]:
            self.assertNotIn(dynamic_scope, action)
        for jump_out in ["presentError(", "hidePanel(", "runModal("]:
            self.assertNotIn(jump_out, action + complete)
        failure = body(action, "catch")
        self.assertIn("itemDeletionError = error.localizedDescription", failure)
        self.assertNotIn("return", failure)
        self.assertNotIn("applyOrderedSelection", failure)
        self.assertLess(action.index("} catch {"), action.index("completion?()"))

    def test_cancel_never_writes_store_or_selection_and_context_changes_invalidate_request(self):
        source = (ROOT / "replica/Sources/Pasto/UI/ReplicaUIController.swift").read_text()
        cancel = body(source, "func cancelItemDeletion()")
        for forbidden in ["store.", "selection =", "primaryID =", "hidePanel("]:
            self.assertNotIn(forbidden, cancel)
        for signature in ["func applySearchInput(nodes:", "private func applySelectedList(_ id:",
                          "@Published var query =", "@Published var searchFilters:",
                          "@Published var pinboardID:", "@Published var showDeleted ="]:
            with self.subTest(signature=signature):
                self.assertIn("cancelItemDeletion()", body(source, signature))
        normalize = body(source, "func normalizeSelection()")
        self.assertIn("!request.ids.isSubset(of: Set(visibleItems.map(\\.id)))", normalize)
        self.assertIn("cancelItemDeletion()", normalize)
        self.assertLess(normalize.index("cancelItemDeletion()"), normalize.index("guard collectionOwner == nil"))

    def test_pending_confirmation_blocks_background_keys_and_copy_then_esc_cancels_only_request(self):
        source = (ROOT / "replica/Sources/Pasto/UI/ReplicaUIController.swift").read_text()
        keys = body(body(source, "private func handleKey(_ event:"), "if state.hasPendingDeletion")
        self.assertIn("event.keyCode == 53 { cancelPendingDeletion(); return true }", keys)
        self.assertIn("state.confirmItemDeletion()", keys)
        self.assertIn("else { confirmPinboardRemoval() }", keys)
        self.assertNotIn("hidePanel()", keys)
        copy = body(source, "panel.copyRequested =")
        self.assertLess(copy.index("!self.state.hasPendingDeletion"), copy.index("self.copySelection"))
        close = body(source, "func hidePanel()")
        self.assertIn("cancelPendingDeletion()", close)
        self.assertIn("state.cancelItemDeletion()", body(source, "func removePinboard(_ target:"))
        escape = body(source, "func cancelSearchOrPanel()")
        self.assertIn("if state.hasPendingDeletion { cancelPendingDeletion(); return }", escape)

    def test_deletion_confirmation_remains_in_card_panel_with_scoped_explanation(self):
        source = (ROOT / "replica/Sources/Pasto/UI/PanelViews.swift").read_text()
        items = body(source, "private func itemDeletionConfirmation(")
        self.assertIn("if request.permanently", items)
        self.assertIn("else if request.contextPinboardID != nil", items)
        self.assertIn("state.cancelItemDeletion()", items)
        self.assertIn("state.confirmItemDeletion()", items)
        overlay = body(source, "if state.hasPendingDeletion")
        self.assertIn("state.controller?.cancelPendingDeletion()", overlay)
        self.assertIn("itemDeletionConfirmation(request)", overlay)
        self.assertIn("pinboardDeletionConfirmation(target)", overlay)
        presentation = body(source, "private func deletionConfirmation(title:")
        self.assertNotIn("NSAlert", presentation)
        self.assertIn('"cancel-\\(kind)-deletion"', presentation)
        self.assertIn('"confirm-\\(kind)-deletion"', presentation)

    def test_local_delete_keeps_history_group_and_global_scopes_distinct(self):
        ui = (ROOT / "replica/Sources/Pasto/UI/ReplicaUIController.swift").read_text()
        self.assertIn("permanently: showDeleted || !isCollectionSearchQueryEmpty", body(ui, "func deleteSelection()"))
        store = (CORE / "ClipboardStore.swift").read_text()
        scoped = body(store, "func delete(orderedIDs: [UUID], currentPinboardID:")
        group = body(scoped, "if let contextPinboardID")
        self.assertIn("pinboardIDs.remove(contextPinboardID)", group)
        self.assertNotIn("isInHistory =", group)
        self.assertIn("else { state.items[i].isInHistory = false }", scoped)
        self.assertIn("!$0.isInHistory && $0.pinboardIDs.isEmpty", scoped)
        global_delete = body(store, "func permanentlyDelete(orderedIDs: [UUID]) throws")
        self.assertIn("state.items.removeAll { ids.contains($0.id) }", global_delete)

    def test_original_local_multi_confirmation_and_repository_scope_are_bound(self):
        index = {r["address"]: r for r in json.loads((ROOT / "reports/Paste/function-index.json").read_text())}
        def original(address):
            text = (ROOT / index[address]["file"]).read_text()
            start = text.index("/* Address: " + address + " |")
            end = text.find("/* Address:", start + 1)
            return text[start:end if end != -1 else None]
        policy = original("0x1003ba5c4")
        self.assertIn("if (param_2 == (code *)0x0)", policy)
        self.assertIn("if (_Var5 < 2)", policy)
        self.assertIn("if (!bVar2)", policy)
        self.assertIn("FUN_1001bc108(", policy)
        repository = original("0x1003636b4")
        self.assertIn("if ((uint)(param_2 >> 0x3e) != 0)", repository)
        self.assertIn("FUN_100363004(param_1,param_2 & 0x3fffffffffffffff)", repository)
        scoped = original("0x100363004")
        for branch in ["if (IVar6 == 1)", "setTimestamp_", "IVar6 == 2", "setList_", "FUN_1003646ec("]:
            self.assertIn(branch, scoped)
        self.assertIn("deleteObject_(self,self_00)", original("0x1003637c0"))

    def test_retention_removes_only_expired_ungrouped_history_and_zero_is_unlimited(self):
        source = (CORE / "ClipboardStore.swift").read_text()
        expire = body(source, "private func expireHistory(_ state:")
        self.assertIn("guard capacity > 0 else { return }", expire)
        self.assertIn("let interval = -capacity * 24 * 60 * 60", expire)
        self.assertIn("Date(timeIntervalSinceNow: Double(interval))", expire)
        mutation = body(source, "private func mutateInTransaction<T>(historyAction:")
        self.assertIn("if let capacity = lists.historyCapacity(of: history)", mutation)
        self.assertIn("$0.isInHistory && $0.pinboardIDs.isEmpty && $0.createdAt < cutoff", expire)
        self.assertNotIn("isInHistory = false", expire, "The original preserves grouped history timestamps")
        index = {r["address"]: r for r in json.loads((ROOT / "reports/Paste/function-index.json").read_text())}
        address = "0x100363810"
        original = (ROOT / index[address]["file"]).read_text()
        start = original.index("/* Address: " + address + " |")
        end = original.find("/* Address:", start + 1)
        original = original[start:end if end != -1 else None]
        for predicate in ["if (0 < param_1)", "param_1 * -0x15180", '"%K == nil && %K < %@"',
                          "0x7473696c", "6d617473656d6974"]:
            self.assertIn(predicate, original)

    def test_transaction_failure_propagates_without_save_or_value_state_publication(self):
        persistence = (CORE / "ClipboardPersistence.swift").read_text()
        commit = body(persistence, "func commit<T>(previous:")
        operation = body(commit, "try context.performAndWait")
        self.assertEqual(commit.count("try context.performAndWait"), 1)
        self.assertIn("OriginalObjCExceptionBridge.f_1002ff9c8", operation)
        outside_save = operation.replace(body(operation, "if context.hasChanges"), "")
        self.assertNotIn("rollback", outside_save)
        self.assertNotIn("catch", outside_save)
        self.assertIn("context.rollback()", operation)
        self.assertEqual(commit.count("try context.save()"), 1)
        self.assertIn("try context.save()", body(commit, "if context.hasChanges"))
        store = (CORE / "ClipboardStore.swift").read_text()
        transaction = body(store, "private func mutateInTransaction<T>(historyAction:")
        order = ["try persistence.commit(previous: remote, deletingItemIDs: deletingItemIDs,",
                 "let result = try change(&state, transaction)", "try validate(state)",
                 "return (state: state, result: result)", "diskRevision = try revision()", "publish(state)"]
        positions = [transaction.index(token) for token in order]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("try?", transaction)

    def test_capture_policy_refresh_does_not_commit_before_accepting_content(self):
        source = (CORE / "Pasteboard.swift").read_text()
        delegate = body(source, "func originalPasteboardShouldRead(_ types:")
        self.assertNotIn("reload()", delegate)
        self.assertNotIn("store.save()", delegate)
        self.assertIn("f_10037ba14(", delegate)
        capture = body(source, "fileprivate func allowsPasteboardCapture(")
        self.assertNotIn("reload()", capture)
        self.assertLess(capture.index("types.contains(replicaGeneratedType.rawValue)"), capture.index("preferences.ignoreTransientContent"))
        expiry = body(capture, "if let until = preferences.pauseUntil")
        self.assertIn("if until > Date() { return false }", expiry)
        self.assertIn("preferences.isMonitoringPaused = false", expiry)
        self.assertEqual(capture.count("try save()"), 1)
        self.assertIn("try save()", expiry, "Persisting an actual pause expiry remains necessary")
        reload = body((CORE / "ClipboardStore.swift").read_text(), "func reload() throws")
        self.assertNotIn("commit(", reload)
        self.assertNotIn("save(", re.sub(r"//[^\n]*", "", reload))
        self.assertIn("merge(local, onto: remote)", reload, "Read refresh must retain unsaved local edits")

    def test_capture_timer_constants_and_replacement_match_original_exports(self):
        import struct
        source = (CORE / "Pasteboard.swift").read_text()
        start = body(source, "func f_100378ac0()")
        poll = body(source, "func f_10037a028()")
        index = {r["address"]: r for r in json.loads((ROOT / "reports/Paste/function-index.json").read_text())}
        for address, actual, literals in [
            ("0x100378ac0", start, ["0x3fd0000000000000", "0x3f9999999999999a"]),
            ("0x10037a028", poll, ["0x3fd3333333333333"])]:
            text = (ROOT / index[address]["file"]).read_text()
            begin = text.index("/* Address: " + address + " |")
            end = text.find("/* Address:", begin + 1)
            fragment = text[begin:end if end != -1 else None]
            for literal in literals:
                self.assertIn(literal, fragment)
                value = struct.unpack("<d", int(literal, 16).to_bytes(8, "little"))[0]
                self.assertIn(str(value), actual)
        self.assertIn("guard timer == nil", start)
        self.assertIn("userInfo: nil, repeats: true", start)
        self.assertLess(poll.index("guard count != lastChangeCount"), poll.index("recordMonitoring("))
        self.assertLess(poll.index("syncTimer?.invalidate()"), poll.index("syncTimer = Timer.scheduledTimer"))
        self.assertIn("userInfo: nil, repeats: false", poll)

    def test_capture_checks_permission_and_delegate_before_reading_promised_data(self):
        source = (CORE / "Pasteboard.swift").read_text()
        sync = body(source, "private func synchronizePasteboard()")
        order = ["lastChangeCount = pasteboard.changeCount", "captureState.items = []", "_ = pasteboard.types",
                 "permitsBackgroundRead(pasteboard)", "pasteboard.pasteboardItems", "originalPasteboardShouldRead(allTypes)",
                 "for rawItem in rawItems", "permitsRemoteType(", "f_10037c22c(", "rawItem.data(forType: type)"]
        self.assertEqual([sync.index(x) for x in order], sorted(sync.index(x) for x in order))
        denied = body(sync, "guard OriginalPasteboardPolicies.permitsBackgroundRead(pasteboard) else")
        self.assertIn("if let delegate = captureState.delegate", denied)
        self.assertIn("object: delegate", denied)
        self.assertNotIn("data(forType:", denied)
        self.assertIn("if let delegate = captureState.delegate, try !delegate.originalPasteboardShouldRead(allTypes)", sync)

    def test_capture_size_limit_is_cumulative_and_skipped_data_is_not_counted(self):
        sync = body(pre_capture_lifecycle((CORE / "Pasteboard.swift").read_text()), "private func synchronizePasteboard()")
        self.assertEqual(sync.count("var totalBytes = 0"), 1)
        self.assertLess(sync.index("var totalBytes = 0"), sync.index("for rawItem in rawItems"))
        self.assertIn("totalBytes.addingReportingOverflow(data.count)", sync)
        self.assertIn("precondition(!size.overflow", sync)
        oversized = body(sync, "guard size.partialValue <= 0x40000000 else")
        self.assertIn("continue", oversized)
        self.assertNotIn("totalBytes =", oversized)
        self.assertLess(sync.index("guard let data = rawItem.data"), sync.index("let size ="))
        self.assertLess(sync.index("guard size.partialValue <="), sync.index("totalBytes = size.partialValue"))
        self.assertLess(sync.index("totalBytes = size.partialValue"), sync.index("item.f_10037e6b0("))
        self.assertIn("if !item.f_10037da6c().isEmpty { snapshot.append(item) }", sync)
        self.assertIn("defer { captureState.items = [] }", sync)

    def test_capture_notifications_follow_count_and_successful_creation(self):
        source = (CORE / "Pasteboard.swift").read_text()
        did_read = body(source, "func f_10037b428(_ state:")
        order = ['forKey: "pasteboard-change-token"', "addingReportingOverflow(1)",
                 'forKey: "pasteboardSyncCount"', "Self.didSynchronizeNotification", "guard !state.items.isEmpty", "f_10037ae9c("]
        self.assertEqual([did_read.index(x) for x in order], sorted(did_read.index(x) for x in order))
        create = body(source, "func f_10037ae9c(_ items:")
        self.assertLess(create.index("created = try f_10037b034"), create.index("removeAllActions()"))
        self.assertLess(create.index("removeAllActions()"), create.index("if created"))
        self.assertLess(create.index("Self.didCreateItemNotification"), create.index("Self.didCaptureItemNotification"))
        failure = create[create.index("} catch {"):create.index("undoManagerDependency")]
        self.assertIn("return", failure)
        self.assertNotIn("NotificationCenter", failure)

    def test_capture_snapshot_and_representation_order_survive_storage_adapter(self):
        source = (CORE / "Pasteboard.swift").read_text()
        capture = body(source, "func captureWithInsertionResult(")
        self.assertIn("let rawItems = snapshot == nil ? pasteboard.pasteboardItems ?? [] : []", capture)
        self.assertIn("for type in item.types", capture)
        self.assertIn("first.f_10037da6c()", capture)
        self.assertIn("if capturedItems.count > 1", capture)
        self.assertIn("OriginalPasteboardDataCodec.f_10031a8e8(capturedItems", capture)
        fallback = body(capture, "if snapshot == nil")
        self.assertIn("pasteboard.string(forType: .string)", fallback)
        self.assertEqual(capture.count("pasteboard.string("), fallback.count("pasteboard.string("))

    def test_classifier_uses_ordered_priority_then_first_item_and_full_utf16_link_match(self):
        source = (CORE / "OriginalPasteboardClassification.swift").read_text()
        classify = body(source, "func f_10032362c(_ items:")
        self.assertIn("priorityTypes.first(where:", classify)
        self.assertIn("items.flatMap { $0.f_10037da6c() }", classify)
        self.assertNotIn("items.first(where:", classify)
        self.assertLess(classify.index("items.first?.f_10037ce0c()"), classify.index("f_100321f48(text)"))
        self.assertIn("NSRange(location: 0, length: trimmed.utf16.count)", classify)
        self.assertIn("match.range.location == 0 && match.range.length == trimmed.utf16.count", classify)
        self.assertIn("else { return .link }", classify)

    def test_type_priority_and_raw_kind_map_match_original_initializers(self):
        index = {r["address"]: r for r in json.loads((ROOT / "reports/Paste/function-index.json").read_text())}
        def original(address):
            text = (ROOT / index[address]["file"]).read_text()
            start = text.index("/* Address: " + address + " |")
            end = text.find("/* Address:", start + 1)
            return text[start:end if end != -1 else None]
        source = (CORE / "OriginalPasteboardClassification.swift").read_text()
        priority = re.search(r"priorityTypes: \[UTType\] = \[([^]]+)\]", source).group(1)
        current_priority = re.findall(r"\.(\w+)", priority)
        original_priority = re.findall(r"UTType::get_(\w+)\(", original("0x100322124"))
        self.assertEqual(current_priority, original_priority)
        kind_values = {name: int(value) for name, value in re.findall(r"(\w+) = (\d+)", source)}
        current_map = {name: kind_values[kind] for name, kind in re.findall(r"\(\.(\w+), \.(\w+)\)", source)}
        original_map = {name: int(value) for name, value in re.findall(
            r"UTType::get_(\w+)\(UVar6\);\s+puVar14\[[^\n]+?\] = (\d+);", original("0x100322224"))}
        self.assertEqual(len(original_map), 11)
        self.assertEqual(current_map, original_map)
        item_source = body((CORE / "OriginalPasteboard.swift").read_text(), "func f_10037c9a8()")
        current_text_order = re.findall(r"\.(\w+)", re.search(r"for type in \[([^]]+)\]", item_source).group(1))
        original_text_order = re.findall(r"UTType::get_(\w+)\(", original("0x10037c9a8"))
        self.assertEqual(original_text_order[-1], "identifier")
        self.assertEqual(current_text_order, original_text_order[:-1])

    def test_order_preserving_initializer_remains_unchanged_across_independent_archive_repairs(self):
        source = (CORE / "OriginalPasteboard.swift").read_text()
        signature = "    init(types: [String], dataByType: [String: Data]) "
        initializer = body(source, signature)
        self.assertRegex(initializer, r"^\{\s*orderedTypes = types\s+self.dataByType = dataByType\s+super.init\(\)\s*\}$")
        addition = "\n" + signature + initializer + "\n"
        self.assertEqual(source.count(addition), 1)
        baseline = (ROOT / ".local/p0-repair/phase-2/before/replica/Sources/PastoCore/OriginalPasteboard.swift").read_text()
        self.assertEqual(initializer, body(baseline, signature))


if __name__ == "__main__":
    unittest.main()
