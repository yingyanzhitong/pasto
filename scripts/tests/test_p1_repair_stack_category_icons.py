from frc_result_scope_contract import assert_factory_addition_only
"""Static original-code/asset linkage checks. No AppKit/CoreUI/native image loading."""
import hashlib
import json
import plistlib
import re
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from native_stack_rendering_scope_contract import pre_native_stack_rendering
from test_offline_p0_contracts import body
from stack_occurrence_scope_contract import pre_stack_occurrences_bytes
from extract_stack_icon_catalog import Catalog, extract, NAMES


class StackCategoryIconContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-66'
        cls.proof = json.loads((cls.phase / 'stack-category-icon-contract.json').read_text())
        cls.manifest = json.loads((cls.phase / 'catalog-extraction.json').read_text())
        cls.paths = {'icons': 'replica/Sources/PastoCore/OriginalStackCategoryIcons.swift',
                     'car': 'replica/Sources/PastoCore/OriginalStackIcons.bundle/Contents/Resources/Assets.car',
                     'plist': 'replica/Sources/PastoCore/OriginalStackIcons.bundle/Contents/Info.plist',
                     'persistence': 'replica/Sources/PastoCore/ClipboardPersistence.swift',
                     'store': 'replica/Sources/PastoCore/ClipboardStore.swift',
                     'ui': 'replica/Sources/Pasto/UI/AuxiliaryViews.swift'}
        cls.source_bytes = (cls.phase / 'original-Assets.car').read_bytes()
        cls.output_bytes = (ROOT / cls.paths['car']).read_bytes()
        cls.original = Catalog(cls.source_bytes)
        cls.catalog = Catalog(cls.output_bytes)
        cls.icons = (ROOT / cls.paths['icons']).read_text()
        cls.persistence = (ROOT / cls.paths['persistence']).read_text()
        cls.store = (ROOT / cls.paths['store']).read_text()
        cls.ui = pre_native_stack_rendering((ROOT / cls.paths['ui']).read_text())

    def test_original_fragments_binary_strings_selectors_and_current_sources_are_hash_bound(self):
        self.assertEqual(len(self.proof['original_fragments']), 4)
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        for row in [self.proof['binary'], self.proof['original_catalog'], self.proof['original_catalog']['rea_evidence'],
                    self.proof['catalog_extraction'], self.proof['original_asset_metadata'], self.proof['sdk']] + self.proof['arm_disassemblies']:
            self.assertEqual(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest(), row['sha256'])
        for path, digest in self.proof['current_sources'].items():
            frozen = (self.phase / 'after' / path).read_bytes()
            self.assertEqual(hashlib.sha256(frozen).hexdigest(), digest)
            if path == self.paths['persistence']:
                self.assertEqual(body((ROOT / path).read_text(), 'func itemContentKind('), body(frozen.decode(), 'func itemContentKind('))
            elif path == self.paths['store']:
                assert_factory_addition_only(self, (ROOT / path).read_text(), frozen.decode(), public=True)
            else:
                self.assertEqual(pre_stack_occurrences_bytes(ROOT / path), frozen)
        self.assertEqual({r['decoded'] for r in self.proof['native_small_strings']}, set(NAMES))
        for row in self.proof['native_selectors']:
            self.assertTrue(row['chain']['declared_chain_reachable'])
            self.assertEqual(bytes.fromhex(row['selector_bytes']), row['selector'].encode() + b'\0')

    def test_real_category_switch_matches_native_six_values_including_color_text_and_image_unknown(self):
        mapper = body(self.icons, 'public static func name(')
        pairs = re.findall(r'case (.+?): return "([^"]+)"', mapper)
        actual = {case.strip().lstrip('.'): name for cases, name in pairs for case in cases.split(',')}
        self.assertEqual(actual, dict(files='icon.file', color='icon.text', text='icon.text',
                                      link='icon.link', unknown='icon.unknown', image='icon.unknown'))
        self.assertNotIn('systemSymbol', mapper)
        words = {r['address']: struct.unpack('<I', bytes.fromhex(r['bytes']))[0] for r in self.proof['ARM_words']}
        self.assertEqual(words['0x10031ebb8'], 0xf100181f)
        self.assertEqual(words['0x10031ebbc'], 0x1a9f3000)

    def test_subset_has_only_four_public_facets_eight_scale_records_and_three_required_atlases(self):
        facets = {self.catalog.block(key).decode() for _, key in self.catalog.tree('FACETKEYS')[2]}
        self.assertEqual(facets, set(NAMES))
        self.assertEqual(len(self.manifest['renditions']), 8)
        self.assertEqual(len(self.catalog.renditions()), 11)
        self.assertEqual(self.manifest['atlas_blocks'], [146, 156, 158])
        self.assertEqual(len(self.output_bytes), 43032)
        self.assertLess(len(self.output_bytes), len(self.source_bytes) // 50)

    def test_BOM_block_ranges_counts_and_leaf_nodes_are_self_consistent(self):
        _, live, index, size, variables, var_size = struct.unpack_from('>6I', self.output_bytes, 8)
        self.assertEqual(live, len(self.manifest['kept_blocks']))
        self.assertEqual(index + size, len(self.output_bytes))
        self.assertLessEqual(variables + var_size, index)
        ranges = sorted((offset, offset + length) for offset, length in self.catalog.locations if length)
        self.assertTrue(all(begin >= 512 and begin % 16 == 0 and end <= variables for begin, end in ranges))
        self.assertTrue(all(left[1] <= right[0] for left, right in zip(ranges, ranges[1:])))
        self.assertEqual(struct.unpack_from('<I', self.catalog.block(self.catalog.variables['CARHEADER']), 16)[0], 11)
        for name in ['RENDITIONS', 'FACETKEYS', 'APPEARANCEKEYS', 'BITMAPKEYS']:
            self.catalog.tree(name)

    def test_all_kept_rendition_keys_records_and_atlas_compressed_bytes_are_identical_to_original(self):
        originals = self.original.renditions()
        for key, pair in self.catalog.renditions().items():
            self.assertEqual(pair, originals[key])
            for index in pair:
                self.assertEqual(self.catalog.block(index), self.original.block(index))
        for row in self.manifest['renditions']:
            self.assertEqual(hashlib.sha256(self.catalog.block(row['rendition_block'])).hexdigest(), row['rendition_sha256'])
            self.assertEqual(hashlib.sha256(self.catalog.block(row['atlas_block'])).hexdigest(), row['atlas_sha256'])
        self.assertFalse(self.manifest['pixel_data_decoded'])
        self.assertFalse(self.manifest['pixel_data_reencoded'])
        self.assertFalse(self.manifest['native_framework_executed'])

    def test_every_INLK_target_key_and_crop_resolves_inside_the_subset_without_external_resources(self):
        references = set()
        for row in self.manifest['renditions']:
            pair, crop = self.catalog.linked_atlas(self.catalog.block(row['rendition_block']))
            self.assertEqual(pair[0], row['atlas_block'])
            self.assertEqual(crop, row['crop'])
            self.assertGreaterEqual(crop['x'], 0)
            self.assertGreaterEqual(crop['y'], 0)
            self.assertLessEqual(crop['x'] + crop['width'], crop['atlas_width'])
            self.assertLessEqual(crop['y'] + crop['height'], crop['atlas_height'])
            references.add(pair[0])
        self.assertEqual(references, set(self.manifest['atlas_blocks']))

    def test_one_and_two_scale_template_metadata_matches_original_asset_info(self):
        metadata = json.loads((ROOT / self.proof['original_asset_metadata']['path']).read_text())
        rows = {r['RenditionName']: r for r in metadata if r.get('Name') in NAMES}
        self.assertEqual(len(rows), 8)
        for row in self.manifest['renditions']:
            data = self.catalog.block(row['rendition_block'])
            info = rows[row['name']]
            width, height, scale = struct.unpack_from('<III', data, 12)
            self.assertEqual((width, height, scale), (info['PixelWidth'], info['PixelHeight'], info['Scale'] * 100))
            self.assertEqual((width, height), (20 * info['Scale'], 20 * info['Scale']))
            self.assertEqual(struct.unpack_from('<I', data, 8)[0], 8)
            self.assertEqual(data[24:28], b' 8AG')
            self.assertEqual(info['Template Mode'], 'template')
            self.assertEqual(info['ColorModel'], 'Monochrome')

    def test_pure_Python_extraction_reproduces_resource_and_manifest_without_native_decode(self):
        output, manifest = extract(self.source_bytes)
        self.assertEqual(output, self.output_bytes)
        self.assertEqual(manifest, self.manifest)
        self.assertEqual(hashlib.sha256(output).hexdigest(), manifest['output_sha256'])
        self.assertEqual(hashlib.sha256(self.source_bytes).hexdigest(), manifest['source_sha256'])

    def test_bitmap_inline_hash_metadata_and_appearance_keys_are_not_misread_as_offsets(self):
        for name in ['BITMAPKEYS', 'APPEARANCEKEYS']:
            old_header, old_node, old_pairs = self.original.tree(name)
            header, node, pairs = self.catalog.tree(name)
            self.assertEqual((header, node, pairs), (old_header, old_node, old_pairs))
            self.assertEqual(self.catalog.block(header), self.original.block(header))
            self.assertEqual(self.catalog.block(node), self.original.block(node))
            for value, key in pairs:
                self.assertEqual(self.catalog.block(value), self.original.block(value))
                if name != 'BITMAPKEYS': self.assertEqual(self.catalog.block(key), self.original.block(key))
        self.assertTrue(any(key >= self.catalog.index_count for _, key in self.catalog.tree('BITMAPKEYS')[2]))

    def test_missing_required_atlas_reference_is_detected_without_loading_CoreUI(self):
        data = bytearray(self.source_bytes)
        header, node, pairs = self.original.tree('RENDITIONS')
        atlas = self.manifest['atlas_blocks'][0]
        kept = [pair for pair in pairs if pair[0] != atlas]
        self.assertEqual(len(pairs) - len(kept), 1)
        header_offset, _ = self.original.locations[header]
        node_offset, _ = self.original.locations[node]
        struct.pack_into('>I', data, header_offset + 16, len(kept))
        struct.pack_into('>H', data, node_offset + 2, len(kept))
        for i, pair in enumerate(kept): struct.pack_into('>II', data, node_offset + 12 + i * 8, *pair)
        with self.assertRaises(KeyError): extract(bytes(data))

    def test_SwiftPM_and_existing_packager_include_private_BNDL_inside_core_resources(self):
        package = (ROOT / 'replica/Package.swift').read_text()
        self.assertIn('.copy("OriginalStackIcons.bundle")', package)
        info = plistlib.loads((ROOT / self.paths['plist']).read_bytes())
        self.assertEqual(info['CFBundlePackageType'], 'BNDL')
        self.assertEqual(info['CFBundleIdentifier'], 'com.yingyanzhitong.pasto.stack-icons')
        self.assertNotIn('CFBundleExecutable', info)
        self.assertIn('ditto "$binary_root/Pasto_PastoCore.bundle" "$bundle/Contents/Resources/Pasto_PastoCore.bundle"',
                      (ROOT / 'replica/scripts/build-app.sh').read_text())
        self.assertIn('Bundle.module.url(forResource: "OriginalStackIcons", withExtension: "bundle")', self.icons)
        self.assertIn('let bundle = Bundle(url: url)', self.icons)

    def test_named_lookup_has_missing_resource_traps_and_no_source_app_or_system_symbol_fallback(self):
        image = body(self.icons, 'public static func image(')
        self.assertIn('resources.image(forResource: NSImage.Name(assetName))', image)
        self.assertIn('preconditionFailure("Missing Stack category image:', image)
        self.assertIn('preconditionFailure("Missing Stack icon resource bundle")', self.icons)
        for forbidden in ['/Applications/', '.local/', 'systemSymbolName', 'rawIcon', 'sourceApplication', 'NSImage()']:
            self.assertNotIn(forbidden, self.icons)
        self.assertIn('imageForResource:(NSImageName)name', Path(self.proof['sdk']['path']).read_text())

    def test_real_Stack_provider_uses_managed_rawType_and_exact_nontruncating_kind_domain(self):
        method = body(self.persistence, 'func itemContentKind(')
        for token in ['context.performAndWait', 'PastoItemEntity.defaultFetchRequest()', 'NSPredicate(format: "key == %@", identifier)',
                      'request.fetchLimit = 1', '(try? context.fetch(request))?.first',
                      '(object.value(forKey: "rawType") as? NSNumber)?.int64Value ?? 0',
                      'UInt8(exactly: raw)', 'OriginalPasteboardContentKind(rawValue: value) ?? .unknown']:
            self.assertIn(token, method)
        self.assertNotIn('uint8Value', method)
        self.assertNotIn('reset(', method)
        store = body(self.store, 'public func originalContentKind(')
        self.assertIn('persistence.itemContentKind(identifier: item.id.uuidString)', store)
        self.assertIn('OriginalStackCategoryIcons.image(for: state.store.originalContentKind(of: item))', self.ui)
        provider = self.ui.split('OriginalStackSnippetCellView(item: item, imageProvider:', 1)[1].split('}).frame', 1)[0]
        for forbidden in ['sourceApplication', 'rawIcon', 'systemSymbolName', 'NSImage()']:
            self.assertNotIn(forbidden, provider)

    def test_existing_cell_outlet_text_order_and_all_other_real_sources_are_preserved(self):
        cell_path = 'replica/Sources/Pasto/UI/OriginalStackSnippetCell.swift'
        self.assertEqual(pre_native_stack_rendering((ROOT / cell_path).read_text()).encode(), (self.phase / 'before' / cell_path).read_bytes())
        cell = body(pre_native_stack_rendering((ROOT / cell_path).read_text()), 'func f_1000519f8(')
        ordered = ['if let imageView { imageView.image = imageProvider(item) }',
                   'textField?.maximumNumberOfLines = 2', 'OriginalStackSnippetText.f_100051ec8(item)']
        self.assertEqual([cell.index(t) for t in ordered], sorted(cell.index(t) for t in ordered))
        for key, marker in [('persistence', 'func itemContentKind('), ('store', 'public func originalContentKind(')]:
            current = (self.phase / 'after' / self.paths[key]).read_text()
            previous = (self.phase / 'before' / self.paths[key]).read_text()
            start = current.index('    ' + marker)
            method = body(current, marker)
            end = current.index(method, start) + len(method) + (2 if key == 'persistence' else 1)
            self.assertEqual((current[:start], current[end:]), (previous[:start], previous[start:]))

    def test_only_three_existing_production_files_and_three_bundle_loader_files_change(self):
        base = json.loads((self.phase / 'baseline.json').read_text())
        frozen_root = ROOT / '.local/p0-repair/phase-67/before'
        current = {str(p.relative_to(frozen_root)) for p in (frozen_root / 'replica/Sources').rglob('*') if p.is_file()}
        changed = {p for p, h in base['production'].items() if hashlib.sha256((frozen_root / p).read_bytes()).hexdigest() != h}
        self.assertEqual(changed, {self.paths[k] for k in ['persistence', 'store', 'ui']})
        self.assertEqual(current - set(base['production']), {self.paths[k] for k in ['icons', 'car', 'plist']})
        row, = self.proof['contracts']
        self.assertEqual(row['function_id'], 'Paste:0x1000519f8')
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['function_map_markers_upgraded'], 0)
        self.assertTrue(any('365e18 FRC' in text for text in self.proof['retained_partial_contracts']))

    def test_vendor_resource_attribution_and_full_catalog_are_kept_separate(self):
        notice = (ROOT / 'NOTICE.md').read_text()
        self.assertIn(self.paths['car'], notice)
        self.assertIn('不适用本项目 MIT 授权', notice)
        self.assertEqual(len(self.source_bytes), 2850696)
        self.assertEqual(len(self.output_bytes), 43032)
        names = {self.catalog.block(key).decode() for _, key in self.catalog.tree('FACETKEYS')[2]}
        self.assertEqual(names, set(NAMES))
        self.assertNotIn('AppIcon', names)


if __name__ == '__main__': unittest.main()
