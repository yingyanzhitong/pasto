"""Check localized-error source/data contracts without loading a Swift framework."""
import hashlib
import json
from pathlib import Path
import plistlib
import re
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts/tests")]
from function_ledger import source_fragments
from macho_imports import _chained_bindings, _cstring
from test_offline_p0_contracts import body

PHASE = ROOT / ".local/p0-repair/phase-2"
CORE = ROOT / "replica/Sources/PastoCore"


def strings(text):
    quoted = r'"(?:\\.|[^"\\])*"'
    return {json.loads(k): json.loads(v) for k, v in re.findall(
        rf'^\s*({quoted})\s*=\s*({quoted})\s*;', text, re.M)}


class ShortcutLocalizedError(unittest.TestCase):
    def test_native_fragments_and_error_description_shape(self):
        report = json.loads((PHASE / "shortcut-localization-result.json").read_text())
        for row in report["original_fragments"]:
            self.assertEqual(source_fragments(ROOT / row["path"])[row["function_id"].split(":")[1]]["sha256"], row["sha256"])
        data = (ROOT / ".local/paste-arm64-static.bin").read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), report["original_binary_sha256"])
        position = 32
        segments, dylibs, fixups = [], [], None
        for _ in range(struct.unpack_from("<I", data, 16)[0]):
            command, length = struct.unpack_from("<II", data, position)
            if command == 0x19:
                address, memory, offset, size = struct.unpack_from("<4Q", data, position + 24)
                segments.append(dict(address=address, memory_size=memory, offset=offset, file_size=size))
            elif command in (0xc, 0x80000018, 0x8000001f, 0x20, 0x80000023):
                offset = struct.unpack_from("<I", data, position + 8)[0]
                dylibs.append(dict(install_name=_cstring(data, position + offset, position + length)))
            elif command == 0x80000034:
                fixups = struct.unpack_from("<II", data, position + 8)
            position += length
        def offset(address):
            segment = next(s for s in segments if s["address"] <= address < s["address"] + s["file_size"])
            return segment["offset"] + address - segment["address"]
        def relative(address):
            return address + struct.unpack_from("<i", data, offset(address))[0]
        def text(address):
            start = offset(address)
            return data[start:data.index(b"\0", start)].decode()
        descriptor = 0x100ca73ec
        self.assertEqual(text(relative(descriptor + 8)), "ShortcutValidatorError")
        self.assertEqual(struct.unpack_from("<I", data, offset(descriptor + 20))[0], 1)
        field = relative(descriptor + 16)
        self.assertEqual(text(relative(field + 24)), "errorDescription")
        self.assertEqual(text(relative(field + 20)), "SSSg")  # Optional<String>
        bindings, _ = _chained_bindings(data, fixups, segments, dylibs)
        for conformance, symbol in [(0x100c337a8, "_$s10Foundation14LocalizedErrorMp"),
                                    (0x100c337f0, "_$ss5ErrorMp")]:
            self.assertEqual(relative(conformance + 4), descriptor)
            protocol = relative(conformance)
            self.assertEqual(protocol & 1, 1)
            self.assertEqual(bindings[protocol & ~1]["symbol"], symbol)

    def test_current_error_has_the_same_single_optional_storage(self):
        source = (CORE / "OriginalShortcutRecorder.swift").read_text()
        error = body(source, "public struct OriginalShortcutRecorderError: LocalizedError")
        self.assertEqual(re.findall(r"public let (\w+): ([^\n]+)", error), [("errorDescription", "String?")])
        self.assertIn("public init(_ message: String?) { errorDescription = message }", error)
        self.assertIn('public var message: String { errorDescription ?? "" }', error)

    def test_resource_lookup_uses_current_locale_and_bundle(self):
        source = (CORE / "OriginalShortcutMessages.swift").read_text()
        value = body(source, "static func value(_ key: String)")
        for token in ["String(localized: LocalizedStringResource(", "String.LocalizationValue(key)",
                      'table: "Localizable"', "locale: .current", ".atURL(bundle.bundleURL)"]:
            self.assertIn(token, value)
        self.assertNotIn("preferredLanguages", source)
        self.assertNotIn("private static let messages", source)
        self.assertIn('appendingPathComponent("Pasto_PastoCore.bundle")', source)

    def test_menu_title_is_one_typed_interpolation_and_recursion_preserves_error(self):
        source = (CORE / "OriginalShortcutMessages.swift").read_text()
        menu = body(source, "static func menuConflict(_ title: String)")
        self.assertIn('LocalizedStringResource("shortcut-recorder.error.used-in-menu"', menu)
        self.assertIn('defaultValue: "\\(title)"', menu)
        validation = body((CORE / "OriginalShortcutValidation.swift").read_text(),
                          "func f_1001ec200(shortcut: OriginalShortcutValue,")
        self.assertIn("return OriginalShortcutRecorderError(OriginalShortcutMessages.menuConflict(item.title))", validation)
        self.assertIn("if let failure = f_1001ec200(shortcut: shortcut, menu: item.submenu) { return failure }", validation)
        self.assertNotIn("String(format:", validation)

    def test_all_resource_values_match_installed_reference_and_other_keys_are_preserved(self):
        evidence = json.loads((PHASE / "shortcut-localizations.json").read_text())
        self.assertEqual(len(evidence["locales"]), 17)
        for row in evidence["locales"]:
            raw = Path(row["source"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row["source_sha256"])
            reference = plistlib.loads(raw.decode("utf-16").encode("utf-8"))
            destination = ROOT / row["destination"]
            current = strings(destination.read_text())
            before = (PHASE / "before" / row["destination"]).read_text()
            self.assertTrue(all(current[key] == reference[key] == row["values"][key] for key in evidence["keys"]), row["language"])
            restored = destination.read_text()
            for key in row["added_keys"]:
                line = json.dumps(key, ensure_ascii=False) + " = " + json.dumps(row["values"][key], ensure_ascii=False) + ";\n"
                self.assertEqual(restored.count(line), 1)
                restored = restored.replace(line, "", 1)
            self.assertEqual(restored, before, row["language"])


if __name__ == "__main__":
    unittest.main()
