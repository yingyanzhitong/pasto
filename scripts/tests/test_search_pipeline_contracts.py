"""Source/byte contracts only; no Swift, Spotlight query, UI or network execution."""
import json
import re
import struct
import unittest

from test_offline_p0_contracts import ROOT, CORE, body


def bounded_query_consumer(text):
    """Reject a missing/late cap or a cap based on projected/deduplicated IDs."""
    try:
        query = body(text, "nonisolated private static func matchingIdentifiers(")
        delivery = body(text, "private func replaceQuery(with nodes:")
        loop = body(query, "for try await result in query.results")
        loop_end = query.index("{", query.index("for try await result in query.results")) + len(loop)
        return ("var resultCount = 0" in query
                and loop.index("resultCount += 1") < loop.index("result.item.uniqueIdentifier")
                < loop.index("if resultCount == limit { break }")
                and "found.count ==" not in loop and "limit: Self.maximumResultCount" in delivery
                and query.index("try Task.checkCancellation()", loop_end) < query.index("return found")
                and delivery.index("try Task.checkCancellation()") < delivery.index("identifiers = found"))
    except ValueError:
        return False


class SearchPipelineContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = (ROOT / "replica/Sources/Pasto/UI/ReplicaSearchIndex.swift").read_text()
        cls.query = (CORE / "OriginalSearchQuery.swift").read_text()
        cls.normalization = (CORE / "OriginalSearchQueryNormalization.swift").read_text()
        cls.history = (CORE / "OriginalSearchInputHistory.swift").read_text()
        cls.editor = (ROOT / "replica/Sources/Pasto/UI/SearchEditor.swift").read_text()
        cls.original_index = {r["address"]: r for r in json.loads((ROOT / "reports/Paste/function-index.json").read_text())}

    @classmethod
    def original(cls, address):
        text = (ROOT / cls.original_index[address]["file"]).read_text()
        start = text.index("/* Address: " + address + " |")
        end = text.find("/* Address:", start + 1)
        return text[start:end if end != -1 else None]

    def test_limit_is_bound_to_actual_factory_immediate_and_service_field(self):
        report = json.loads((ROOT / "reports/replica/offline-migration-p0-round10.json").read_text())
        proof = report["static_bindings"]
        word, call = struct.unpack("<II", bytes.fromhex(proof["factory_limit"]["bytes"]))
        self.assertEqual(word, 0x52800c82)  # mov w2, #100
        self.assertEqual((word >> 5) & 0xffff, 100)
        self.assertEqual(int(proof["factory_limit"]["address"], 16) + 4 + ((call & 0x3ffffff) << 2),
                         0x1002e19c8)
        self.assertIn("0x8000000100da0fc0,100)", self.original("0x1002d6274"))
        self.assertIn("*(undefined8 *)(unaff_x20 + 0x20) = param_3", self.original("0x1002e19c8"))
        self.assertIn("private static let maximumResultCount = 100", self.index)
        self.assertEqual(struct.unpack("<III", bytes.fromhex(proof["limit_comparison"]["bytes"])),
                         (0xf9401328, 0xeb0802ff, 0x540006a1))  # load limit; compare count; continue if unequal

    def test_result_cap_counts_raw_rows_before_identifier_projection(self):
        self.assertTrue(bounded_query_consumer(self.index))
        original = self.original("0x1002e2bf8")
        self.assertIn("if (lVar10 != *(long *)(lVar3 + 0x20))", original)
        self.assertLess(original.index("objc_stub::uniqueIdentifier"), original.index("if (lVar10 !="))
        loop = body(body(self.index, "nonisolated private static func matchingIdentifiers("), "for try await result in query.results")
        self.assertIn("found.insert(id)", loop)
        self.assertNotIn("continue", loop, "Malformed projected identifiers must not bypass the raw row limit")

    def test_source_guard_rejects_missing_cap_distinct_count_and_missing_cancellation(self):
        for changed in [
            self.index.replace("if resultCount == limit { break }", ""),
            self.index.replace("resultCount == limit", "found.count == limit"),
            self.index.replace("try Task.checkCancellation()", ""),
            self.index.replace("try Task.checkCancellation()\n        return found", "return found"),
        ]:
            with self.subTest(changed=changed != self.index): self.assertFalse(bounded_query_consumer(changed))

    def test_cancellation_check_binds_to_real_swift_import_and_precedes_publication(self):
        proof = json.loads((ROOT / "reports/replica/offline-migration-p0-round10.json").read_text())["static_bindings"]
        call, = struct.unpack("<I", bytes.fromhex(proof["cancellation_call"]["bytes"]))
        self.assertEqual(int(proof["cancellation_call"]["address"], 16) + ((call & 0x3ffffff) << 2),
                         int(proof["cancellation_stub"]["address"], 16))
        binding = proof["cancellation_stub"]["dyld_binding"]
        self.assertEqual(binding["symbol"], "_$sScTss5NeverORszABRs_rlE17checkCancellationyyKFZ")
        self.assertEqual(binding["dylib"]["install_name"], "/usr/lib/swift/libswift_Concurrency.dylib")
        self.assertEqual(binding["mechanism"], "LC_DYLD_CHAINED_FIXUPS")
        self.assertIn("Swift::Task::_checkCancellation()", self.original("0x1002e2bf8"))
        query = body(self.index, "nonisolated private static func matchingIdentifiers(")
        delivery = body(self.index, "private func replaceQuery(with nodes:")
        self.assertLess(query.index("try Task.checkCancellation()", query.index("for try await result in query.results")),query.index("return found"))
        self.assertLess(delivery.index("try Task.checkCancellation()"), delivery.index("identifiers = found"))

    def test_query_context_uses_no_attributes_and_keeps_own_store_scope(self):
        original = self.original("0x1002e2930")
        self.assertLess(original.index("setFetchAttributes_"), original.index("initWithQueryString_queryContext_"))
        query = body(self.index, "nonisolated private static func matchingIdentifiers(")
        self.assertIn("context.fetchAttributes = []", query)
        self.assertIn('context.filterQueries = ["pasteReplicaStore ==', query)
        self.assertIn("guard !predicate.isEmpty else { return [] }", query)
        self.assertIn("let predicate = OriginalSearchQuery.f_1002f45b0(nodes)",body(self.index,"private func replaceQuery(with nodes:"))

    def test_query_trims_text_escapes_in_order_and_combines_same_tag_or_other_tags_and(self):
        escaped = body(self.query, "private static func escaped(_ value: String)")
        replacements = re.findall(r'replacingOccurrences\(of: "((?:\\.|[^"\\])*)",', escaped)
        self.assertEqual(replacements, ['\\\\', '\\"', '*', '?'])
        query = body(self.query, "func f_1002f45b0(_ nodes:")
        self.assertIn("trimmingCharacters(in: .whitespaces)", query)
        self.assertIn('escaped(text.joined(separator: " "))', query)
        self.assertIn("groups[tag, default: []].append(predicate)", query)
        self.assertIn('group.joined(separator: " || ")', query)
        self.assertIn('predicates.joined(separator: " && ")', query)
        original = self.original("0x1002f45b0")
        self.assertIn("separator.str = (char *)0x207c7c20", original)
        self.assertIn("separator_00.str = (char *)0x20262620", original)

    def test_os_content_description_gate_and_character_limit_match_original(self):
        self.assertIn("_stdlib_isOSVersionAtLeast(0x1a,4,0)", self.original("0x1002f45b0"))
        attributes = self.original("0x1002e3ce8")
        self.assertIn("FUN_1002e3a8c(5000,", attributes)
        self.assertIn("setContentDescription_", attributes)
        gate = "majorVersion: 26, minorVersion: 4, patchVersion: 0"
        self.assertIn(gate, self.query)
        self.assertIn(gate, self.index)
        self.assertIn("String(indexedText.prefix(5000))", self.index)
        self.assertIn("item.expirationDate = .distantFuture", self.index)

    def test_filter_predicate_empty_and_date_parse_boundaries(self):
        predicate = body(self.query, "func f_1002f3d94(tag:")
        self.assertLess(predicate.index("trimmingCharacters(in: .whitespaces)"), predicate.index("guard !value.isEmpty"))
        self.assertIn('let parts = value.split(separator: " ")', predicate)
        self.assertIn("parts.count == 2", predicate)
        self.assertIn("Double(parts[0])", predicate)
        self.assertIn("Double(parts[1])", predicate)
        self.assertIn("let formatter = ISO8601DateFormatter()", predicate)
        self.assertIn("tag == 2 || tag == 4", predicate)
        original = self.original("0x1002f3d94")
        self.assertIn("if (*(long *)(lVar14 + 0x10) == 2)", original)
        self.assertIn("_OBJC_CLASS___NSISO8601DateFormatter", original)

    def test_normalization_preserves_raw_values_and_splits_at_last_original_filter(self):
        normalize = body(self.normalization, "func f_1002da16c(")
        self.assertIn("seen[tag, default: []].insert(value).inserted", normalize)
        self.assertIn("filters.append(node)", normalize)
        self.assertIn("let lastFilter = nodes.lastIndex", normalize)
        self.assertIn("index > lastFilter", normalize)
        self.assertIn("if flag & 1 != 0", normalize)
        self.assertLess(normalize.index("filters.append(contentsOf: after)"), normalize.index("filters.append(contentsOf: before)"))
        self.assertNotIn(".sorted", normalize)

    def test_tokenizer_keeps_whitespace_runs_and_clears_input_after_nonempty_parse(self):
        tokens = (CORE / "OriginalSearchTextTokens.swift").read_text()
        self.assertIn('replacingOccurrences(of: "\\u{FFFC}", with: " ")', tokens)
        self.assertIn("character.isWhitespace", tokens)
        self.assertIn("previousWhitespace != whitespace", tokens)
        self.assertIn("buffer.removeAll(keepingCapacity: true)", tokens)
        original = self.original("0x1002f8760")
        self.assertIn("local_88 = 0xbcbfef", original)
        self.assertIn("Character::get_isWhitespace", original)
        self.assertIn("String::removeAll(true", original)

    def test_history_equal_snapshot_is_noop_and_effective_change_clears_redo(self):
        record = body(self.history, "func f_1002f5e18(")
        self.assertLess(record.index("guard snapshot != current else { return }"), record.index("if immediate"))
        self.assertTrue(record.rstrip().endswith("redo.removeAll()\n    }"))
        original = self.original("0x1002f5e18")
        self.assertIn("FUN_1002de150(param_1,uVar5)", original)
        self.assertIn("param_2 != lVar4 || param_3 != lVar8", original)
        self.assertIn("unaff_x20 + 0x18) = PTR___swiftEmptyArrayStorage", original)

    def test_history_immediate_flushes_before_pushing_and_grouped_input_keeps_first_baseline(self):
        record = body(self.history, "func f_1002f5e18(")
        immediate = body(record, "if immediate")
        order = ["f_1002f5fe8()", "undo.append(current)", "current = snapshot"]
        self.assertEqual([immediate.index(t) for t in order], sorted(immediate.index(t) for t in order))
        self.assertIn("if pending == nil { pending = current }", record)
        self.assertLess(record.index("current = snapshot", record.index("} else {")), record.index("f_1002f60fc()"))

    def test_undo_flushes_but_redo_preserves_original_asymmetry(self):
        undo = body(self.history, "func f_1002f61f0()")
        redo = body(self.history, "func f_1002f63b8()")
        self.assertLess(undo.index("f_1002f5fe8()"), undo.index("undo.popLast()"))
        self.assertNotIn("f_1002f5fe8()", redo)
        self.assertIn("redo.append(current)", undo)
        self.assertIn("undo.append(current)", redo)
        self.assertIn("FUN_1002f5fe8()", self.original("0x1002f61f0"))
        self.assertNotIn("FUN_1002f5fe8()", self.original("0x1002f63b8"))

    def test_history_reset_clears_stacks_and_pending_without_resetting_current(self):
        reset = body(self.history, "func f_1002f6550()")
        for token in ["undo.removeAll()", "redo.removeAll()", "timer?.invalidate()", "timer = nil", "pending = nil"]:
            self.assertIn(token, reset)
        self.assertNotIn("current =", reset)
        self.assertNotIn("unaff_x20 + 0x20) =", self.original("0x1002f6550"))

    def test_history_real_consumers_keep_snapshots_selection_and_point_four_interval(self):
        self.assertIn("OriginalSearchInputHistory(interval: 0.4)", self.editor)
        self.assertIn("self.history.f_1002f61f0()", self.editor)
        self.assertIn("self.history.f_1002f63b8()", self.editor)
        restore = body(self.editor, "private func restore(_ snapshot:")
        self.assertIn("selection: snapshot.selection", restore)
        self.assertIn("parent.onInputChange(value.text, value.filters, snapshot.nodes)", restore)
        self.assertIn("if !preserveHistory { history.f_1002f6550() }", self.editor)


if __name__ == "__main__":
    unittest.main()
