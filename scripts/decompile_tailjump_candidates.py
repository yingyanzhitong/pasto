#!/usr/bin/env python3
"""只读筛选成功伪代码中跳向已映射入口的 ARM64 尾跳候选。"""
import argparse
import bisect
from collections import Counter
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT_SHA = {}


def load_json(path):
    raw = (ROOT / path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if path in INPUT_SHA and INPUT_SHA[path] != digest:
        raise ValueError(f'分析期间输入发生变化：{path}')
    INPUT_SHA[path] = digest
    return json.loads(raw)


def safe_source_refs(record, original_sha):
    """核实记录及引用；只确认文本存在，不声称源码与原版行为等价。"""
    evidence_path = record.get('evidence_path')
    if not isinstance(evidence_path, str) or not evidence_path:
        return None, 'missing_evidence'
    relative = Path(evidence_path)
    if relative.is_absolute() or '..' in relative.parts or not (ROOT / relative).resolve().is_relative_to(ROOT):
        return None, 'unsafe_evidence_path'
    try:
        evidence = load_json(evidence_path)
    except (OSError, json.JSONDecodeError):
        return None, 'unreadable_evidence'
    if (evidence.get('function_id') != record['function_id']
            or evidence.get('original_binary_sha256') != original_sha):
        return None, 'evidence_identity_mismatch'
    checked = []
    has_source = False
    if not isinstance(record['implementation_refs'], list) or not record['implementation_refs']:
        return None, 'missing_implementation_refs'
    for ref in record['implementation_refs']:
        if not isinstance(ref, dict):
            return None, 'invalid_reference'
        path = ref.get('path')
        symbol = ref.get('symbol')
        if not isinstance(path, str) or not isinstance(symbol, str) or not symbol:
            return None, 'invalid_reference'
        relative = Path(path)
        if relative.is_absolute() or '..' in relative.parts or not (ROOT / relative).resolve().is_relative_to(ROOT):
            return None, 'unsafe_source_path'
        try:
            raw = (ROOT / relative).read_bytes()
            if symbol not in raw.decode('utf-8'):
                return None, 'symbol_not_found'
        except (OSError, UnicodeError):
            return None, 'unreadable_source'
        digest = hashlib.sha256(raw).hexdigest()
        if path in INPUT_SHA and INPUT_SHA[path] != digest:
            raise ValueError(f'分析期间输入发生变化：{path}')
        INPUT_SHA[path] = digest
        previous = evidence.get('source_sha256', {}).get(path)
        checked.append({'path': path, 'symbol': symbol, 'sha256': digest,
                        'matches_recorded_source': None if previous is None else digest == previous})
        has_source |= path.startswith('replica/Sources/') and relative.suffix in ('.swift', '.m', '.h')
    return ({'evidence_path': evidence_path, 'refs': checked}, None) if has_source else (None, 'no_source_code_reference')


def read_macho(data):
    if len(data) < 32 or struct.unpack_from('<I', data)[0] != 0xfeedfacf:
        raise ValueError('需要本机已分析的 arm64 thin Mach-O 文件')
    if struct.unpack_from('<I', data, 4)[0] != 0x100000c:
        raise ValueError('Mach-O 架构不匹配')
    count, size = struct.unpack_from('<II', data, 16)
    cursor, segments, starts_command = 32, [], None
    if 32 + size > len(data):
        raise ValueError('Mach-O load command 表超出文件范围')
    for _ in range(count):
        if cursor + 8 > 32 + size:
            raise ValueError('Mach-O load command 头部截断')
        cmd, length = struct.unpack_from('<II', data, cursor)
        if length < 8 or cursor + length > 32 + size:
            raise ValueError('Mach-O load command 无效')
        if cmd == 0x19:
            if length < 72:
                raise ValueError('Mach-O 段命令截断')
            name = data[cursor + 8:cursor + 24].split(b'\0')[0].decode()
            vm, _, offset, file_size = struct.unpack_from('<4Q', data, cursor + 24)
            initial_protection = struct.unpack_from('<I', data, cursor + 60)[0]
            if offset + file_size > len(data):
                raise ValueError('Mach-O 段超出文件范围')
            segments.append((name, vm, offset, file_size, initial_protection))
        elif cmd == 0x26:
            if length < 16:
                raise ValueError('LC_FUNCTION_STARTS 命令截断')
            if starts_command is not None:
                raise ValueError('重复的 LC_FUNCTION_STARTS')
            starts_command = struct.unpack_from('<II', data, cursor + 8)
        cursor += length
    if cursor != 32 + size or starts_command is None:
        raise ValueError('缺少或截断的 LC_FUNCTION_STARTS')
    text = next((s for s in segments if s[0] == '__TEXT'), None)
    if text is None:
        raise ValueError('缺少 __TEXT 段')
    offset, length = starts_command
    if offset + length > len(data):
        raise ValueError('LC_FUNCTION_STARTS 超出文件范围')
    payload = data[offset:offset + length]
    entries, cursor, address, terminated = [], 0, text[1], False
    while cursor < len(payload):
        delta = shift = 0
        while True:
            if cursor >= len(payload) or shift >= 64:
                raise ValueError('无效的 ULEB128 函数起始表')
            byte = payload[cursor]
            cursor += 1
            delta |= (byte & 0x7f) << shift
            if delta > 0xffffffffffffffff:
                raise ValueError('ULEB128 超出 64 位')
            if not byte & 0x80:
                break
            shift += 7
        if delta == 0:
            terminated = True
            break
        address += delta
        if address > 0xffffffffffffffff:
            raise ValueError('函数起始地址超出 64 位')
        if address % 4 or (entries and address <= entries[-1]):
            raise ValueError('函数起始表未对齐或未严格递增')
        entries.append(address)
    if not terminated or any(payload[cursor:]):
        raise ValueError('函数起始表未正确结束')
    return segments, entries


def candidates(endpoint="sdk"):
    binary = ROOT / '.local/targets/Paste.arm64'
    data = binary.read_bytes()
    original_sha = hashlib.sha256(data).hexdigest()
    manifest = load_json('reports/target-manifest.json')
    target = next(x for x in manifest['binaries'] if x['name'] == 'Paste')
    if original_sha != target['arm64_sha256']:
        raise ValueError('目标二进制 SHA 与原分析清单不一致')
    coverage = load_json('reports/Paste/coverage.json')
    if coverage['sha256'] != original_sha:
        raise ValueError('反编译覆盖记录与原分析二进制不一致')
    segments, starts = read_macho(data)
    rows = load_json('reports/Paste/function-index.json')
    index = {int(row['address'], 16): row for row in rows}
    if len(index) != len(rows):
        raise ValueError('成功函数索引包含重复地址')
    failed = {int(item['address'], 16) for item in coverage['failures']}
    if set(index) & failed:
        raise ValueError('成功索引与失败集合重叠，拒绝读取入口')
    success_names = {r['address'] for r in rows}
    procedures = {int(p['address'], 16): p['procedure']
                  for p in load_json('reports/Paste/procedures.json') if p['address'] in success_names}
    mapping = load_json('replica/function-map.json')['functions']
    sdk = {}
    if endpoint == 'sdk':
        sdk_report = load_json('reports/function-migration/sdk-import-reuse.json')
        for key, record in mapping.items():
            if not key.startswith('Paste:') or record.get('state') != 'migrated' or not record.get('sdk_implementation'):
                continue
            reference = record['sdk_implementation']
            if reference.get('report') != 'reports/function-migration/sdk-import-reuse.json' or reference.get('entry_key') != key:
                raise ValueError(f'SDK 报告引用不匹配：{key}')
            entry = sdk_report['functions'].get(key)
            if entry is None or entry['original_binary_sha256'] != original_sha:
                raise ValueError(f'已映射 SDK 入口缺少匹配原二进制的报告：{key}')
            symbol = record['sdk_implementation']['symbol']
            if entry['original_stub']['address'] != key.split(':')[1] or entry['original_stub']['symbol'] != symbol:
                raise ValueError(f'SDK 符号与报告不匹配：{key}')
            sdk[int(key.split(':')[1], 16)] = symbol
    source = {}
    for key, record in mapping.items():
        if not key.startswith('Paste:') or record.get('state') != 'migrated' or record.get('sdk_implementation'):
            continue
        refs = record.get('implementations', [])
        source_address = int(key.split(':')[1], 16)
        if source_address in index and source_address not in failed:
            source[source_address] = {'function_id': key, 'implementation_refs': refs,
                                      'evidence_path': record.get('migration_evidence')}
    branches = {}
    for i, address in enumerate(starts[:-1]):
        if address not in index or starts[i + 1] != address + 4:
            continue
        segment = next((s for s in segments if s[4] & 4 and s[1] <= address and address + 4 <= s[1] + s[3]), None)
        if segment is None:
            continue
        offset = segment[2] + address - segment[1]
        raw = data[offset:offset + 4]
        if len(raw) != 4:
            raise ValueError('指令超出文件范围')
        word = struct.unpack('<I', raw)[0]
        if word >> 26 != 5:  # B，不是 BL；不修改 LR。
            continue
        displacement = word & 0x3ffffff
        if displacement & (1 << 25):
            displacement -= 1 << 26
        target_address = address + 4 * displacement
        proc = procedures.get(address, {})
        if proc.get('thunk') is not True or proc.get('thunk_target') != hex(target_address):
            continue
        branches[address] = (target_address, raw.hex())
    sorted_success = sorted(index)
    result = []
    checked_sources = {}
    rejected_source_entries = {}
    tracked_start_states = Counter()
    for address in sorted(branches):
        key = 'Paste:' + hex(address)
        if key in mapping:  # 包括 partial、excluded 和已映射；不篡改既有状态。
            tracked_start_states[mapping[key].get('state', 'unknown')] += 1
            continue
        path, seen, cursor = [], set(), address
        while cursor in branches and cursor not in seen and len(path) < 16:
            if cursor != address and endpoint == 'source' and cursor in source:
                break
            intermediate = mapping.get('Paste:' + hex(cursor))
            if cursor in failed or (intermediate is not None and intermediate.get('state') != 'migrated'):
                break
            seen.add(cursor)
            next_address, raw = branches[cursor]
            path.append({'address': hex(cursor), 'instruction_hex': raw, 'target': hex(next_address)})
            cursor = next_address
        if cursor in failed:
            continue
        next_pos = bisect.bisect_right(sorted_success, address)
        next_success = sorted_success[next_pos] if next_pos < len(sorted_success) else None
        base = {'function_id': key, 'hops': path, 'pseudocode': index[address]['file'],
                'pseudocode_line': index[address]['line'],
                'next_success_index_distance': None if next_success is None else next_success - address,
                'ghidra_body_addressset_verified': False}
        if endpoint == 'sdk' and cursor in sdk:
            base.update(sdk_entry=hex(cursor), sdk_symbol=sdk[cursor])
        elif endpoint == 'source' and cursor in source:
            if cursor not in checked_sources:
                checked_sources[cursor] = safe_source_refs(source[cursor], original_sha)
            checked, reason = checked_sources[cursor]
            if checked is None:
                rejected_source_entries[source[cursor]['function_id']] = reason
                continue
            base.update(source_entry=hex(cursor), source_mapping=source[cursor], source_ref_check=checked,
                        source_endpoint_binding='textual_refs_only')
        else:
            continue
        result.append(base)
    provenance = dict(INPUT_SHA)
    for path, expected in provenance.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise ValueError(f'分析期间输入发生变化：{path}')
    if hashlib.sha256(binary.read_bytes()).hexdigest() != original_sha:
        raise ValueError('分析期间目标二进制发生变化')
    return {'kind': 'static_candidates_not_migration', 'original_sha256': original_sha,
            'input_sha256': provenance, 'endpoint': endpoint,
            'sdk_endpoint_binding': 'reported_not_revalidated' if endpoint == 'sdk' else 'not_used',
            'current_source_build_verified': False, 'count': len(result), 'candidates': result,
            'rejected_source_entries': rejected_source_entries,
            'tracked_branch_starts_skipped_by_state': dict(tracked_start_states),
            'limits': ['只筛选入口转发候选，不证明 Ghidra 完整 AddressSet、调用方、SDK 内部或动态等价。',
                       '终点映射和 SDK 报告只来自已有记录，未重新验证真实消费者或当前工作树构建。',
                       '下一成功索引间距不是函数体大小；LC 起始表也不能替代 Ghidra AddressSet。',
                       '已有映射的起点及经过未完成状态的路径会跳过，不代表原有证据消失。',
                       '仅解码成功索引入口，失败地址不被单独读取或重试。',
                       '不修改迁移台账。']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--endpoint', choices=('sdk', 'source'), default='sdk',
                        help='终点类型：SDK（默认）或已映射源码')
    args = parser.parse_args()
    print(json.dumps(candidates(args.endpoint), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
