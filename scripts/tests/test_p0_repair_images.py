from native_restore_writer_scope_contract import pre_native_restore_writer
import json
import hashlib
from pathlib import Path
import struct
import unittest


ROOT = Path(__file__).resolve().parents[2]
RESTORE = ROOT / "replica/Sources/PastoCore/OriginalPasteboardImageRestore.swift"
PASTEBOARD = ROOT / "replica/Sources/PastoCore/Pasteboard.swift"
RESULT = ROOT / ".local/p0-repair/phase-1/images-result.json"
STATIC_BINARY = ROOT / ".local/paste-arm64-static.bin"
SEGMENT_PROOF = ROOT / "reports/replica/p0-p1-review-round26-static-proof.json"


def static_segments():
    return json.loads(SEGMENT_PROOF.read_text())["file_backed_segments"]


def file_offset(vmaddr: int) -> int:
    segment = next(
        segment for segment in static_segments()
        if segment["vmaddr"] <= vmaddr < segment["vmaddr"] + segment["filesize"]
    )
    return segment["fileoff"] + vmaddr - segment["vmaddr"]


def arm64_word(image: bytes, vmaddr: int) -> int:
    return struct.unpack_from("<I", image, file_offset(vmaddr))[0]


def arm64_bl_target(image: bytes, vmaddr: int) -> int:
    word = arm64_word(image, vmaddr)
    if word & 0xFC000000 != 0x94000000:
        raise AssertionError(f"not BL at {vmaddr:#x}: {word:#010x}")
    immediate = word & 0x03FFFFFF
    if immediate & (1 << 25):
        immediate -= 1 << 26
    return vmaddr + immediate * 4


def arm64_cbnz_target(image: bytes, vmaddr: int) -> int:
    word = arm64_word(image, vmaddr)
    if word & 0x7F000000 != 0x35000000:
        raise AssertionError(f"not CBNZ at {vmaddr:#x}: {word:#010x}")
    immediate = (word >> 5) & 0x7FFFF
    if immediate & (1 << 18):
        immediate -= 1 << 19
    return vmaddr + immediate * 4


def arm64_b_cond_target(image: bytes, vmaddr: int) -> int:
    word = arm64_word(image, vmaddr)
    if word & 0xFF000010 != 0x54000000:
        raise AssertionError(f"not B.cond at {vmaddr:#x}: {word:#010x}")
    immediate = (word >> 5) & 0x7FFFF
    if immediate & (1 << 18):
        immediate -= 1 << 19
    return vmaddr + immediate * 4


def method_body(source: str, signature: str) -> str:
    start = source.index(signature)
    opening = source.index("{", start)
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[opening + 1:index]
    raise AssertionError(f"unterminated method: {signature}")


class ImageRestoreSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.restore = pre_native_restore_writer(RESTORE.read_text())
        cls.pasteboard = PASTEBOARD.read_text()

    def test_loader_prepares_product_root_and_image_directory_before_loading(self):
        prepare = method_body(
            self.restore,
            "public func prepare(sourceName: String?, timestamp: Date?,",
        )
        self.assertLess(prepare.index("createDirectory(at: temporaryRoot"), prepare.index("f_100383df4(sourceName:"))
        projection = method_body(
            self.restore,
            "public func f_100383df4(sourceName: String?, timestamp: Date?,",
        )
        self.assertLess(projection.index("let directory = f_100384824()"), projection.index("let items = try loadItems()"))
        self.assertLess(projection.index("let items = try loadItems()"), projection.index("guard let directory else { return items }"))

    def test_array_apis_remain_compatibility_wrappers(self):
        prepare = method_body(self.restore, "public func prepare(_ items: [OriginalPasteboardItem]")
        image = method_body(self.restore, "public func f_100383df4(_ items: [OriginalPasteboardItem]")
        self.assertIn("prepare(sourceName: sourceName, timestamp: timestamp) { items }", prepare)
        self.assertIn("f_100383df4(sourceName: sourceName, timestamp: timestamp) { items }", image)
        projection = method_body(
            self.restore,
            "private func f_100383df4(_ items: [OriginalPasteboardItem], sourceName: String?, timestamp: Date?,",
        )
        self.assertIn("f_100384aac()", projection)
        cleanup_schedule = method_body(self.restore, "public func f_100384aac()")
        self.assertIn("guard let directory = f_100384824() else { return }", cleanup_schedule)

    def test_drag_and_ordinary_image_restore_decode_lazily(self):
        drag = method_body(self.pasteboard, "public func dragPasteboardGroups(for selected: [ClipboardItem],")
        self.assertIn("if !OriginalPasteboardRestore.usesPlainProjection(kind: kind, options: options), kind == .image", drag)
        self.assertIn("Self.imageRestore.prepare(sourceName: application?.name", drag)
        self.assertLess(drag.index("Self.imageRestore.prepare(sourceName:"), drag.index("try Self.originalPasteboardItems(from: item.payloads)"))
        self.assertIn("} else {\n                representations = try Self.originalPasteboardItems(from: item.payloads)", drag)

        writer = method_body(self.pasteboard, "private func writeToPasteboard(ids: [UUID], pasteboard: NSPasteboard,")
        self.assertIn("} else if !plain, kind == .image {", writer)
        self.assertIn("Self.imageRestore.prepare(sourceName: application?.name", writer)
        self.assertIn("try Self.ordinaryRestoreRepresentations(for: item, plainTextProjection: plain)", writer)
        self.assertIn("if let recognizedImageData {", writer)
        self.assertLess(writer.index("if let recognizedImageData {"), writer.index("} else if !plain, kind == .image {"))

    def test_cleanup_skips_resource_value_failures_but_keeps_remove_errors_throwing(self):
        cleanup = method_body(self.restore, "public static func f_100384e6c(directory: URL,")
        self.assertIn("guard let values = try? file.resourceValues(forKeys: [.creationDateKey]) else { continue }", cleanup)
        self.assertIn("try FileManager.default.removeItem(at: file)", cleanup)
        self.assertIn("} catch {", cleanup)

    def test_native_error_branch_evidence_is_recorded(self):
        result = json.loads(RESULT.read_text())
        proof = result["native_cleanup_proof"]
        image = STATIC_BINARY.read_bytes()
        self.assertEqual(hashlib.sha256(image).hexdigest(), "871f00354fbb1c165d858a98e6d19d6f43cb9d3f9f958b3e07c7f07eb5c19afb")
        self.assertEqual(hashlib.sha256(SEGMENT_PROOF.read_bytes()).hexdigest(), proof["segment_map_sha256"])

        resource_call = 0x100385258
        error_branch = 0x10038525C
        error_block = 0x100385130
        self.assertEqual(image[file_offset(resource_call):file_offset(resource_call) + 4].hex(), "55bd2194")
        self.assertEqual(arm64_bl_target(image, resource_call), 0x100BF47AC)
        self.assertEqual(image[file_offset(error_branch):file_offset(error_branch) + 4].hex(), "b5f6ffb5")
        self.assertEqual(arm64_cbnz_target(image, error_branch), error_block)
        self.assertEqual(image[file_offset(error_block):file_offset(error_block) + 4].hex(), "e00315aa")  # mov x0,x21
        self.assertEqual(arm64_bl_target(image, error_block + 4), 0x100BFC708)  # swift_errorRelease
        self.assertEqual(image[file_offset(error_block + 0x60):file_offset(error_block + 0x64)].hex(), "d6060091")  # add x22,x22,#1
        self.assertEqual(arm64_word(image, error_block + 0x6C), 0xEB16011F)  # cmp x8 (count),x22 (index)
        self.assertEqual(arm64_b_cond_target(image, error_block + 0x70), 0x10038538C)  # only equal exits loop

    def test_original_image_directory_setup_precedes_both_decode_branches(self):
        result = json.loads(RESULT.read_text())
        proof = result["original_stage_order_proof"]
        image = STATIC_BINARY.read_bytes()
        self.assertEqual(hashlib.sha256(image).hexdigest(), "871f00354fbb1c165d858a98e6d19d6f43cb9d3f9f958b3e07c7f07eb5c19afb")
        self.assertEqual(hashlib.sha256(SEGMENT_PROOF.read_bytes()).hexdigest(), proof["segment_map_sha256"])
        directory = 0x100383FE0
        self.assertEqual(arm64_bl_target(image, directory), 0x100384824)
        self.assertEqual(arm64_bl_target(image, 0x10038401C), 0x100C00860)
        self.assertEqual(arm64_bl_target(image, 0x10038402C), 0x10031B218)
        self.assertEqual(arm64_bl_target(image, 0x1003840D4), 0x100C00860)
        self.assertEqual(arm64_bl_target(image, 0x1003840E4), 0x10031B218)
        self.assertLess(directory, 0x10038402C)
        self.assertLess(0x10038402C, 0x1003840E4)


if __name__ == "__main__":
    unittest.main()
