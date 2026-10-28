#!/usr/bin/env python3
"""只读校验已登记的尾跳 partial 静态证据；不升级迁移状态。"""
import hashlib
import importlib.util
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = 'reports/function-migration/tailjump-partial-static.json'
INPUTS = {}


def read(path):
    relative = Path(path)
    full = ROOT / relative
    if relative.is_absolute() or '..' in relative.parts or not full.resolve().is_relative_to(ROOT):
        raise ValueError(f'路径超出工作区：{path}')
    raw = full.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if path in INPUTS and INPUTS[path] != digest:
        raise ValueError(f'分析期间文件改变：{path}')
    INPUTS[path] = digest
    return raw


def read_json(path):
    return json.loads(read(path))


def module(name, path):
    read(path)  # 将解析器脚本本身纳入同一次输入快照。
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def ensure(condition, message):
    if not condition:
        raise ValueError(message)


def verify(root=ROOT):
    global ROOT, INPUTS
    ROOT = Path(root).resolve()
    INPUTS = {}
    data = read('.local/targets/Paste.arm64')
    binary_sha = hashlib.sha256(data).hexdigest()
    manifest = read_json('reports/target-manifest.json')
    coverage = read_json('reports/Paste/coverage.json')
    report = read_json(REPORT)
    mapping = read_json('replica/function-map.json')['functions']
    sdk_report = read_json('reports/function-migration/sdk-import-reuse.json')
    rows = read_json('reports/Paste/function-index.json')
    index = {row['address']: row for row in rows}
    failed = {row['address'] for row in coverage['failures']}
    expected = next(row['arm64_sha256'] for row in manifest['binaries'] if row['name'] == 'Paste')
    ensure(binary_sha == expected == coverage['sha256'] == report['original_binary_sha256'], '原二进制摘要不匹配')
    ensure(len(index) == len(rows) and not (set(index) & failed), '成功/失败索引重叠或地址重复')
    ensure(report['kind'] == 'static_partial_evidence_not_complete' and report['count'] == len(report['functions']), '报告类型或数量无效')
    ensure(not report['current_source_build_verified'] and not report['functional_tests_executed'] and not report['equivalence_verified'], '报告不得声称完整验证')
    linked = {key for key, value in mapping.items()
              if value.get('static_review_evidence', {}).get('report') == REPORT}
    ensure(linked == set(report['functions']), '报告与台账的地址集合不一致')
    procedures = {row['address']: row['procedure'] for row in read_json('reports/Paste/procedures.json') if row['address'] in index}
    scanner = module('tailjump_scanner', 'scripts/decompile_tailjump_candidates.py')
    ledger = module('tailjump_ledger', 'scripts/function_ledger.py')
    macho = module('tailjump_macho', 'scripts/macho_imports.py')
    segments, starts = scanner.read_macho(data)
    starts = set(starts)
    # 只解析二进制中的导入表；不执行应用。源码晚于该二进制，不能当作当前构建。
    original_stubs = macho.parse_macho(ROOT / '.local/targets/Paste.arm64')['stubs']
    compiled_path = 'replica/.build/release/Pasto'
    compiled_sha = hashlib.sha256(read(compiled_path)).hexdigest()
    compiled_stubs = macho.parse_macho(ROOT / compiled_path)['stubs']
    fragments, source_count, sdk_count = {}, 0, 0
    fields = ('address', 'section', 'body_size', 'body_hex', 'instruction_words', 'pointer_address',
              'pointer_section', 'pointer_file_offset', 'pointer_raw_value', 'dyld_binding',
              'indirect_symbol_index', 'symbol', 'dylib_ordinal', 'n_type', 'n_sect', 'n_desc',
              'weak_import', 'dylib', 'cpu_type', 'cpu_subtype')
    for key, evidence in report['functions'].items():
        ensure(key.startswith('Paste:') and evidence['function_id'] == key, f'地址标识不匹配：{key}')
        review = mapping.get(key, {})
        ref = review.get('static_review_evidence', {})
        ensure(review.get('state') == 'partial' and not review.get('sdk_implementation')
               and ref == {'report': REPORT, 'entry_key': key}, f'partial 映射不匹配：{key}')
        ensure(not evidence['ghidra_body_addressset_verified'] and not evidence['current_source_build_verified']
               and not evidence['complete_implementation_verified'], f'证据超出静态范围：{key}')
        address = key.split(':', 1)[1]
        ensure(address in index and address not in failed, f'入口不在成功索引：{key}')
        original = evidence['original_pseudocode']
        row = index[address]
        ensure(original['path'] == row['file'] and original['line'] == row['line'], f'伪代码索引不匹配：{key}')
        path = original['path']
        if path not in fragments:
            read(path)  # 固定来源摘要；source_fragments 会二次读取，结束时再次比较。
            fragments[path] = ledger.source_fragments(ROOT / path)
        ensure(fragments[path][address]['sha256'] == original['sha256'], f'伪代码摘要不匹配：{key}')
        hops = evidence['original_hops']
        ensure(0 < len(hops) <= 16 and hops[0]['address'] == address, f'跳转链起点无效：{key}')
        seen = set()
        for i, hop in enumerate(hops):
            addr = hop['address']
            ensure(addr in index and addr not in failed and addr not in seen, f'跳转链包含失败或重复入口：{key}')
            seen.add(addr)
            if i:
                ensure(hops[i - 1]['target'] == addr, f'跳转链断开：{key}')
                middle = mapping.get('Paste:' + addr, {})
                ensure(middle.get('state') == 'partial' and middle.get('static_review_evidence') == {'report': REPORT, 'entry_key': 'Paste:' + addr}
                       and report['functions']['Paste:' + addr]['original_hops'] == hops[i:], f'中间别名未绑定相同链：{key}')
            value = int(addr, 16)
            ensure(value in starts and value + 4 in starts, f'LC 函数起始边界不匹配：{key}')
            segment = next((s for s in segments if s[4] & 4 and s[1] <= value and value + 4 <= s[1] + s[3]), None)
            ensure(segment is not None, f'入口不在可执行段：{key}')
            offset = segment[2] + value - segment[1]
            raw = data[offset:offset + 4]
            ensure(len(raw) == 4 and raw.hex() == hop['instruction_hex'], f'指令字节不匹配：{key}')
            word = struct.unpack('<I', raw)[0]
            ensure(word >> 26 == 5, f'指令不是 B 尾跳：{key}')
            imm = word & 0x3ffffff
            if imm & (1 << 25):
                imm -= 1 << 26
            dest = hex(value + 4 * imm)
            proc = procedures.get(addr, {})
            ensure(dest == hop['target'] and proc.get('thunk') is True and proc.get('thunk_target') == dest, f'跳转目标不匹配：{key}')
        terminal = evidence['terminal']
        terminal_address = terminal.split(':', 1)[-1]
        ensure(hops[-1]['target'] == terminal_address and terminal_address in index and terminal_address not in failed,
               f'终点不匹配或不在成功索引：{key}')
        target_key = 'Paste:' + terminal_address
        target = mapping.get(target_key, {})
        ensure(target.get('state') == 'migrated', f'终点不再是已映射状态：{key}')
        if evidence['kind'] == 'sdk':
            sdk_count += 1
            sdk = target.get('sdk_implementation', {})
            entry = sdk_report['functions'].get(target_key, {})
            ensure(sdk.get('entry_key') == target_key and sdk.get('report') == evidence['historical_sdk_report']
                   and sdk.get('symbol') == evidence['symbol'] == entry.get('original_stub', {}).get('symbol')
                   and entry.get('original_binary_sha256') == binary_sha and entry.get('replica_binary_sha256') == compiled_sha,
                   f'SDK 历史报告不匹配：{key}')
            original_stub = original_stubs.get(terminal_address, {})
            compiled_stub = compiled_stubs.get(entry.get('replica_stub', {}).get('address'), {})
            ensure(original_stub and compiled_stub and macho._binding_key(original_stub) == macho._binding_key(compiled_stub),
                   f'SDK 原版与历史构建绑定不一致：{key}')
            for stub in (original_stub, compiled_stub):
                ensure(all(stub['dyld_binding'][field] == 0
                           for field in ('import_addend', 'pointer_addend', 'effective_addend')),
                       f'SDK 导入存在非零 addend：{key}')
            for field in fields:
                ensure(original_stub.get(field) == entry['original_stub'].get(field)
                       and compiled_stub.get(field) == entry['replica_stub'].get(field), f'SDK 导入字段不匹配：{key} {field}')
            sdk_evidence = read_json(target['migration_evidence'])
            ensure(sdk_evidence.get('function_id') == target_key
                   and sdk_evidence.get('sdk_implementation') == sdk
                   and sdk_evidence.get('original_binary_sha256') == binary_sha
                   and sdk_evidence.get('compiled_app_binary_sha256') == compiled_sha
                   and sdk_evidence.get('sdk_reuse_report_sha256') == INPUTS['reports/function-migration/sdk-import-reuse.json'],
                   f'SDK 终点证据不匹配：{key}')
        elif evidence['kind'] == 'source':
            source_count += 1
            ensure(not target.get('sdk_implementation') and target.get('migration_evidence') == evidence['terminal_evidence'], f'源码终点不匹配：{key}')
            terminal_evidence = read_json(evidence['terminal_evidence'])
            ensure(terminal_evidence.get('function_id') == target_key and terminal_evidence.get('original_binary_sha256') == binary_sha, f'源码终点原版证据不匹配：{key}')
            expected_refs = {(r['path'], r['symbol']) for r in target.get('implementations', [])}
            supplied_refs = {(r['path'], r['symbol']) for r in evidence['source_refs']}
            ensure(expected_refs and any(path.startswith('replica/Sources/') and symbol
                                         and Path(path).suffix in ('.swift', '.m', '.h')
                                         for path, symbol in expected_refs)
                   and expected_refs == supplied_refs
                   and expected_refs == {(r['path'], r['symbol']) for r in review.get('implementations', [])},
                   f'源码终点引用不匹配：{key}')
            for ref in evidence['source_refs']:
                raw = read(ref['path'])
                ensure(hashlib.sha256(raw).hexdigest() == ref['sha256'] and ref['symbol'] in raw.decode('utf-8'), f'源码引用已变化：{key}')
                old = terminal_evidence.get('source_sha256', {}).get(ref['path'])
                ensure(ref['matches_recorded_source'] == (None if old is None else ref['sha256'] == old), f'历史源码比对状态不匹配：{key}')
        else:
            raise ValueError(f'未知终点类型：{key}')
    for path, digest in INPUTS.items():
        ensure(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, f'校验期间文件改变：{path}')
    return {'partial_bindings_checked': sdk_count + source_count, 'sdk': sdk_count, 'source': source_count,
            'current_source_build_verified': False, 'functional_tests_executed': False,
            'complete_implementation_verified': False}


def main():
    print(json.dumps(verify(), ensure_ascii=False))


if __name__ == '__main__':
    main()
