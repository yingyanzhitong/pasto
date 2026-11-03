#!/usr/bin/env python3
"""Extract the four original Stack category names without decoding/re-encoding pixels.

Reads the single-leaf BOM/CSI form of the inspected Paste 6.6.6 catalog only.
Keeps original rendition records and their required packed grayscale atlases verbatim.
No CoreUI/AppKit/assetutil/compiler execution or third-party Python dependencies.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

NAMES = ('icon.file', 'icon.link', 'icon.text', 'icon.unknown')
SHA = lambda data: hashlib.sha256(data).hexdigest()


class Catalog:
    def __init__(self, data):
        self.data = data
        assert data[:8] == b'BOMStore'
        version, live, index, length, variables, size = struct.unpack_from('>6I', data, 8)
        assert version == 1 and index + length <= len(data) and variables + size <= len(data)
        self.index_count, = struct.unpack_from('>I', data, index)
        self.locations = [struct.unpack_from('>II', data, index + 4 + i * 8) for i in range(self.index_count)]
        assert sum(size > 0 for _, size in self.locations) == live
        assert all(offset + size <= len(data) for offset, size in self.locations)
        self.variables_data = data[variables:variables + size]
        count, = struct.unpack_from('>I', self.variables_data)
        self.variables = {}
        cursor = 4
        for _ in range(count):
            block, length = struct.unpack_from('>IB', self.variables_data, cursor)
            cursor += 5
            name = self.variables_data[cursor:cursor + length].decode('ascii')
            cursor += length
            self.variables[name] = block
        assert cursor == len(self.variables_data)
        fmt = self.block(self.variables['KEYFORMAT'])
        assert fmt[:4] == b'tmfk'
        count, = struct.unpack_from('<I', fmt, 8)
        self.atoms = struct.unpack_from('<' + 'I' * count, fmt, 12)

    def block(self, index):
        offset, size = self.locations[index]
        assert size > 0
        return self.data[offset:offset + size]

    def tree(self, name):
        header_id = self.variables[name]
        header = self.block(header_id)
        magic, version, node_id, node_size, count = struct.unpack_from('>4s4I', header)
        assert magic == b'tree' and version == 1
        node = self.block(node_id)
        leaf, node_count, forward, backward = struct.unpack_from('>HHII', node)
        assert leaf == 1 and node_count == count and forward == backward == 0 and len(node) >= 12 + count * 8
        return header_id, node_id, [struct.unpack_from('>II', node, 12 + i * 8) for i in range(count)]

    def renditions(self):
        return {struct.unpack('<' + 'H' * len(self.atoms), self.block(key)): (value, key)
                for value, key in self.tree('RENDITIONS')[2]}

    @staticmethod
    def rendition_name(data):
        assert data[:4] == b'ISTC'
        return data[40:168].split(b'\0', 1)[0].decode('utf-8')

    def linked_atlas(self, data):
        assert data[:4] == b'ISTC'
        metadata_size, = struct.unpack_from('<I', data, 168)
        cursor, end, link = 184, 184 + metadata_size, None
        assert end == len(data)  # requested category records contain only metadata/atlas links
        while cursor < end:
            tag, length = struct.unpack_from('<II', data, cursor)
            cursor += 8
            payload = data[cursor:cursor + length]
            assert len(payload) == length
            cursor += length
            if tag == 1010:
                assert link is None
                link = payload
        assert cursor == end and link is not None and link[:4] == b'KLNI'
        flags, x, y, width, height = struct.unpack_from('<5I', link, 4)
        assert flags == 0 and (width, height) == struct.unpack_from('<II', data, 12)
        assert struct.unpack_from('<3H', link, 24) == (12, 20, 0)
        values, cursor = {}, 30
        while cursor < len(link):
            atom, value = struct.unpack_from('<HH', link, cursor)
            cursor += 4
            if atom == 0:
                assert value == 0 and cursor == len(link)
                break
            assert atom in self.atoms and atom not in values
            values[atom] = value
        key = tuple(values.get(atom, 0) for atom in self.atoms)
        value_id, key_id = self.renditions()[key]
        atlas = self.block(value_id)
        atlas_width, atlas_height = struct.unpack_from('<II', atlas, 12)
        assert x + width <= atlas_width and y + height <= atlas_height
        assert atlas[24:28] == data[24:28] == b' 8AG'
        assert self.rendition_name(atlas).startswith('ZZZZPackedAsset-')
        return (value_id, key_id), dict(x=x, y=y, width=width, height=height,
                                      atlas_width=atlas_width, atlas_height=atlas_height, atlas_key=list(key))


def extract(data):
    source = Catalog(data)
    assert set(source.variables) == {'CARHEADER', 'RENDITIONS', 'FACETKEYS', 'APPEARANCEKEYS',
                                     'KEYFORMAT', 'EXTENDED_METADATA', 'BITMAPKEYS'}
    replacements = {}
    keep = set(source.variables.values())
    rendered, selected, atlas_ids = [], [], set()
    for key, (value_id, key_id) in source.renditions().items():
        rendition = source.block(value_id)
        name = source.rendition_name(rendition)
        if name not in {n + suffix for n in NAMES for suffix in ('.png', '@2x.png')}:
            continue
        atlas, rect = source.linked_atlas(rendition)
        rendered.append((value_id, key_id))
        atlas_ids.add(atlas)
        selected.append(dict(name=name, rendition_block=value_id, key_block=key_id,
                             rendition_sha256=SHA(rendition), key=list(key), crop=rect,
                             atlas_block=atlas[0], atlas_sha256=SHA(source.block(atlas[0]))))
    assert len(selected) == 8 and {r['name'] for r in selected} == {n + s for n in NAMES for s in ('.png', '@2x.png')}
    selected_render_pairs = set(rendered) | atlas_ids
    facets = []
    for value_id, key_id in source.tree('FACETKEYS')[2]:
        if source.block(key_id).decode('utf-8') in NAMES:
            facets.append((value_id, key_id))
    assert len(facets) == 4
    for tree_name in ['RENDITIONS', 'FACETKEYS', 'APPEARANCEKEYS', 'BITMAPKEYS']:
        header_id, node_id, original_pairs = source.tree(tree_name)
        keep.add(node_id)
        pairs = ([pair for pair in original_pairs if pair in selected_render_pairs] if tree_name == 'RENDITIONS'
                 else facets if tree_name == 'FACETKEYS' else original_pairs)
        header = bytearray(source.block(header_id))
        struct.pack_into('>I', header, 16, len(pairs))
        node = bytearray(len(source.block(node_id)))
        struct.pack_into('>HHII', node, 0, 1, len(pairs), 0, 0)
        for i, (value_id, key_id) in enumerate(pairs):
            struct.pack_into('>II', node, 12 + i * 8, value_id, key_id)
            keep.add(value_id)
            # BITMAPKEYS' second word is an inline hash, not a BOM block reference.
            if tree_name != 'BITMAPKEYS': keep.add(key_id)
        replacements[header_id], replacements[node_id] = bytes(header), bytes(node)
    header_id = source.variables['CARHEADER']
    header = bytearray(source.block(header_id))
    assert struct.unpack_from('<I', header, 16)[0] == len(source.tree('RENDITIONS')[2])
    struct.pack_into('<I', header, 16, len(selected_render_pairs))
    replacements[header_id] = bytes(header)
    output = bytearray(512)
    locations = [(0, 0)] * source.index_count
    def align(): output.extend(b'\0' * (-len(output) % 16))
    for index in sorted(keep):
        align()
        block = replacements.get(index, source.block(index))
        locations[index] = (len(output), len(block))
        output.extend(block)
    align()
    variables_offset = len(output)
    output.extend(source.variables_data)
    align()
    index_offset = len(output)
    output.extend(struct.pack('>I', source.index_count))
    output.extend(b''.join(struct.pack('>II', *location) for location in locations))
    output.extend(b'\0' * 20)
    struct.pack_into('>8s6I', output, 0, b'BOMStore', 1, len(keep), index_offset,
                     len(output) - index_offset, variables_offset, len(source.variables_data))
    result = bytes(output)
    extracted = Catalog(result)
    assert set(extracted.renditions()) == {key for key, pair in source.renditions().items() if pair in selected_render_pairs}
    assert {extracted.block(key).decode() for _, key in extracted.tree('FACETKEYS')[2]} == set(NAMES)
    for pair in selected_render_pairs:
        for index in pair:
            assert source.block(index) == extracted.block(index)
    for row in selected:
        extracted.linked_atlas(extracted.block(row['rendition_block']))
    return result, dict(source_sha256=SHA(data), output_sha256=SHA(result), source_bytes=len(data),
                        output_bytes=len(result), named_assets=list(NAMES), renditions=selected,
                        atlas_blocks=sorted(value for value, _ in atlas_ids), kept_blocks=sorted(keep),
                        pixel_data_decoded=False, pixel_data_reencoded=False, native_framework_executed=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    output, manifest = extract(args.source.read_bytes())
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    args.destination.write_bytes(output)
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: manifest[k] for k in ['source_bytes', 'output_bytes', 'named_assets', 'atlas_blocks']}))


if __name__ == '__main__': main()
