#!/usr/bin/env python3
"""一次扫描全部地址及已有映射；只检查静态引用，不自动认定语义等价。"""
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from function_ledger import source_fragments

ROOT = Path(__file__).resolve().parents[1]
SKIP = {'Paste:0x100ac35f8', 'Paste:0x100ac746c'}


def main():
    mapping = json.loads((ROOT / 'replica/function-map.json').read_text())['functions']
    ledger = {}
    for path in sorted((ROOT / 'reports/function-implementation').glob('*/*.jsonl')):
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if row['id'] in ledger:
                raise ValueError('Duplicate address: ' + row['id'])
            ledger[row['id']] = row
    texts, hashes, evidence, fragments = {}, {}, {}, {}

    def digest(path):
        if path not in hashes:
            file = ROOT / path
            hashes[path] = hashlib.sha256(file.read_bytes()).hexdigest() if file.is_file() else None
        return hashes[path]

    rows = []
    for key, entry in mapping.items():
        issues, references = [], []
        for ref in entry.get('implementations', []):
            path, symbol = ref['path'], ref['symbol']
            if path not in texts:
                file = ROOT / path
                texts[path] = file.read_text() if file.is_file() else ''
            present = bool(symbol) and symbol in texts[path]
            references.append({'path': path, 'symbol': symbol, 'present': present})
            if not present:
                issues.append('missing_source_reference')
        ep = entry.get('migration_evidence')
        saved = {}
        if ep:
            if ep not in evidence:
                file = ROOT / ep
                evidence[ep] = json.loads(file.read_text()) if file.is_file() else {}
            saved = evidence[ep]
            if not saved:
                issues.append('missing_evidence')
            elif 'functions' in saved:
                functions = saved['functions']
                if isinstance(functions, list):
                    saved = next((item for item in functions if item.get('function_id') == key), {})
                elif isinstance(functions, dict):
                    saved = functions.get(key, {})
                if not saved:
                    issues.append('missing_address_in_evidence')
        if key not in ledger:
            issues.append('address_missing_from_ledger')
        source_hashes = saved.get('source_sha256', {})
        binding = 'not_recorded'
        if references and all(r['path'] in source_hashes for r in references):
            binding = 'current' if all(digest(r['path']) == source_hashes[r['path']] for r in references) else 'file_changed_needs_method_review'
        original_binding = 'not_recorded'
        if saved.get('original_pseudocode_sha256') and key in ledger:
            original = ledger[key]['original']
            path = original['path']
            if path not in fragments:
                fragments[path] = source_fragments(ROOT / path)
            fragment = fragments[path].get(key.split(':')[1], {})
            original_binding = 'current' if saved['original_pseudocode_sha256'] == fragment.get('sha256') else 'changed'
        sdk_binding = None
        if entry.get('sdk_implementation'):
            sdk = entry['sdk_implementation']
            sdk_binding = 'current_report' if saved.get('sdk_reuse_report_sha256') == digest(sdk['report']) else 'report_changed_or_missing'
        rows.append({'function_id': key, 'state': entry['state'], 'source_references': references,
                     'source_binding': binding, 'original_binding': original_binding,
                     'sdk_binding': sdk_binding, 'issues': sorted(set(issues))})
    eligible = {k for k in ledger if k not in SKIP and mapping.get(k, {}).get('state') != 'excluded_by_scope'}
    unmapped = eligible - mapping.keys()
    kinds = Counter(ledger[k]['kind'] for k in unmapped)
    thunk_groups = {}
    for key in sorted(unmapped):
        row = ledger[key]
        if row['kind'] != 'local_thunk' or not row.get('thunk_target'):
            continue
        target = key.split(':')[0] + ':' + row['thunk_target']
        thunk_groups.setdefault(target, []).append(key)
    reuse_candidates = [{'target_function_id': target, 'target_state': mapping.get(target, {}).get('state', 'pending'),
                         'function_ids': ids, 'count': len(ids)} for target, ids in thunk_groups.items()]
    reuse_candidates.sort(key=lambda group: (-group['count'], group['target_function_id']))
    states = Counter(v['state'] for v in mapping.values())
    report = {'kind': 'batch_static_reference_inventory', 'generated_at': datetime.now(timezone.utc).isoformat(),
              'policy': '全地址扫描只代表库存检查；引用存在、摘要一致及跳板分类均不自动升级完整迁移。文件摘要改变不直接判定函数缺失。',
              'source_edited': False, 'build_executed': False, 'tests_executed': False,
              'total_addresses_scanned': len(ledger), 'eligible_denominator': len(eligible),
              'inventory_scan_percent': 100.0, 'mapping_states': dict(states),
              'ledger_marked_migration_percent': round(states['migrated'] / len(eligible) * 100, 4),
              'mapped_reference_records_checked': len(rows), 'unmapped_eligible_count': len(unmapped),
              'unmapped_by_kind': dict(kinds),
              'pending_thunk_target_groups': len(thunk_groups),
              'pending_thunks_to_migrated_targets': sum(g['count'] for g in reuse_candidates if g['target_state'] == 'migrated'),
              'source_binding_counts': dict(Counter(r['source_binding'] for r in rows if r['state'] == 'migrated')),
              'sdk_binding_counts': dict(Counter(r['sdk_binding'] for r in rows if r['sdk_binding'])),
              'reference_issue_counts': dict(Counter(i for r in rows for i in r['issues'])),
              'rows': rows}
    output = ROOT / 'reports/replica/batch-completeness-inventory.json'
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    output.with_name('batch-thunk-review-groups.json').write_text(json.dumps({
        'policy': '只按原始跳转目标归组；必须核实参数/返回/副作用及真实消费者，不自动计完整。',
        'groups': reuse_candidates}, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'rows'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
