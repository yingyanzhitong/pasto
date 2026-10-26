#!/usr/bin/env python3
"""静态比较原版颜色常量及真实重定位与复刻源码；不加载或运行应用。"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

from macho_imports import _arm64_slice
from paywall_scope_exclusion import bytes_at

ROOT = Path(__file__).resolve().parents[1]
REPORT = 'reports/replica/source-application-color-table.json'
SOURCE = 'replica/Sources/PastoCore/OriginalSourceApplicationColors.swift'


def snapshot():
    target = next(b for b in json.loads((ROOT / 'reports/target-manifest.json').read_text())['binaries']
                  if b['name'] == 'Paste')
    container = (Path('/Applications/Paste.app') / target['relative_path']).read_bytes()
    data, _ = _arm64_slice(container)
    if (hashlib.sha256(container).hexdigest() != target['sha256']
            or hashlib.sha256(data).hexdigest() != target['arm64_sha256']):
        raise ValueError('原版输入与已审清单不一致')
    fixups = None
    offset = 32
    for _ in range(struct.unpack_from('<I', data, 16)[0]):
        command, size = struct.unpack_from('<II', data, offset)
        if command == 0x80000034:
            fixups = struct.unpack_from('<II', data, offset + 8)
        offset += size
    if fixups is None:
        raise ValueError('缺少真实页链')
    begin, length = fixups
    blob = data[begin:begin + length]
    version, starts = struct.unpack_from('<II', blob)
    if version != 0:
        raise ValueError('不支持的页链版本')
    count = struct.unpack_from('<I', blob, starts)[0]
    reached = {}
    for segment in range(count):
        relative = struct.unpack_from('<I', blob, starts + 4 + segment * 4)[0]
        if not relative:
            continue
        info = starts + relative
        size, page_size, format_, segment_offset, _, pages = struct.unpack_from('<IHHQIH', blob, info)
        if format_ != 6 or size < 22 + pages * 2:
            raise ValueError('原版页链格式改变')
        page_starts = struct.unpack_from('<' + str((size - 22) // 2) + 'H', blob, info + 22)
        for page in range(pages):
            first = page_starts[page]
            if first == 0xffff:
                continue
            chain_starts = [first]
            if first & 0x8000:
                chain_starts = []
                extra = first & 0x7fff
                while True:
                    item = page_starts[extra]
                    chain_starts.append(item & 0x7fff)
                    extra += 1
                    if item & 0x8000:
                        break
            for chain_start in chain_starts:
                position = chain_start
                seen = set()
                while True:
                    if position in seen or position + 8 > page_size:
                        raise ValueError('页链越界或成环')
                    seen.add(position)
                    address = 0x100000000 + segment_offset + page * page_size + position
                    raw = struct.unpack('<Q', bytes_at(data, address, 8))[0]
                    reached[address] = raw
                    step = (raw >> 51) & 0xfff
                    if not step:
                        break
                    position += step * 4
    rows = []
    for index in range(47):
        address = 0x100fbefb8 + index * 24
        raw = bytes_at(data, address, 24)
        word0, word1, color = struct.unpack('<QQQ', raw)
        small = word1 >> 60 == 0xe
        if small:
            if address + 8 in reached:
                raise ValueError('内联字符串被误作重定位')
            name = raw[:(word1 >> 56) & 15].decode('utf-8')
        else:
            if reached.get(address + 8) != word1 or word1 >> 63 or (word1 >> 44) & 0x7f:
                raise ValueError('大字符串缺少有效非绑定页链证据')
            pointer = (((word1 & 0xfffffffff) | (((word1 >> 36) & 255) << 56)) + 0x100000000) & ((1 << 64) - 1)
            string_address = (pointer & ((1 << 63) - 1)) + 32
            name = bytes_at(data, string_address, word0 & 0xffffffffffff).decode('utf-8')
        rows.append({'slot': hex(address), 'bundle_identifier': name, 'raw_color': hex(color),
                     'small_inline': small, 'second_word': hex(word1),
                     'entry_sha256': hashlib.sha256(raw).hexdigest()})
    source = (ROOT / SOURCE).read_text()
    pairs = re.findall(r'"([^"\n]+)":\s*(0x[0-9a-fA-F]+)', source)
    expected = {row['bundle_identifier']: int(row['raw_color'], 16) for row in rows}
    if len(expected) != 47 or len(pairs) != 47 or {k: int(v, 16) for k, v in pairs} != expected:
        raise ValueError('源码覆盖表与原版47项不一致')
    return {'kind': 'static_source_application_color_constant_comparison',
            'parser_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'original_binary_sha256': target['arm64_sha256'],
            'source_sha256': {SOURCE: hashlib.sha256((ROOT / SOURCE).read_bytes()).hexdigest()},
            'raw_table_sha256': hashlib.sha256(bytes_at(data, 0x100fbefb8, 47 * 24)).hexdigest(),
            'entry_count': 47, 'large_reachable_rebases': sum(not r['small_inline'] for r in rows),
            'inline_small_strings': sum(r['small_inline'] for r in rows), 'entries': rows,
            'limits': '只核固定原表、实际页链与源码常量，不验证取色算法、原函数ABI或运行行为。',
            'functional_tests_executed': False, 'product_executed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    report = snapshot()
    path = ROOT / REPORT
    if args.check:
        if json.loads(path.read_text()) != report:
            raise ValueError('已存静态证据不是当前输入')
    else:
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'checked': args.check, 'source_constants_match': True, 'entries': 47,
                      'large_rebases': report['large_reachable_rebases'],
                      'inline_small_strings': report['inline_small_strings'],
                      'functional_tests_executed': False}))


if __name__ == '__main__':
    main()
