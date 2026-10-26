#!/usr/bin/env python3
"""Static Mach-O SDK-stub reuse evidence. Never loads or executes either executable.

Public API:
    parse_macho(path) -> dict containing binary metadata and validated stubs by address
    generate_reuse_report(root) -> report for the two explicitly paired products
    verify_reuse_report(root, report_path) -> validated function-ID-to-entry mapping

Only actual 12-byte arm64 ADRP/LDR/BR SDK stubs qualify. Ghidra display names are
not used for symbol matching. This module makes no functional-equivalence claim.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import struct

ARM64 = 0x0100000C
APPLICATION_ROOT = Path('/Applications/Paste.app')
TARGET_PRODUCTS = {'Paste': 'Pasto', 'Paste-Helper': 'PastoHelper'}
PRODUCT_SOURCE_TARGETS = {
    'Pasto': ('Pasto', 'PastoCore', 'PastoObjC'),
    'PastoHelper': ('PastoHelper',),
}
REPORT_PATH = 'reports/function-migration/sdk-import-reuse.json'
HEADER = re.compile(r'^/\* Address: (0x[0-9a-f]+) \| .*? \*/$', re.MULTILINE)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def _hex(value):
    return f'0x{value:x}'


def _version(value):
    return f'{value >> 16}.{(value >> 8) & 255}.{value & 255}'


def _unpack(fmt, data, offset):
    size = struct.calcsize(fmt)
    if offset < 0 or offset + size > len(data):
        raise ValueError('Mach-O structure exceeds input bytes')
    return struct.unpack_from(fmt, data, offset)


def _cstring(data, start, end):
    if not 0 <= start < end <= len(data):
        raise ValueError('Invalid Mach-O string range')
    stop = data.find(b'\0', start, end)
    if stop < 0:
        raise ValueError('Unterminated Mach-O string')
    return data[start:stop].decode('utf-8')


def _arm64_slice(container):
    magic = container[:4]
    if magic == b'\xcf\xfa\xed\xfe':
        return container, 0
    fat = {
        b'\xca\xfe\xba\xbe': ('>', False),
        b'\xbe\xba\xfe\xca': ('<', False),
        b'\xca\xfe\xba\xbf': ('>', True),
        b'\xbf\xba\xfe\xca': ('<', True),
    }
    if magic not in fat:
        raise ValueError('Expected a thin or universal Mach-O executable')
    endian, wide = fat[magic]
    count, = _unpack(endian + 'I', container, 4)
    size = 32 if wide else 20
    fmt = endian + ('IIQQII' if wide else 'IIIII')
    matches = []
    for index in range(count):
        row = _unpack(fmt, container, 8 + index * size)
        cpu, subtype, offset, length = row[:4]
        if cpu == ARM64 and subtype == 0:
            if offset + length > len(container) or length < 32:
                raise ValueError('Invalid arm64 slice range')
            matches.append((container[offset:offset + length], offset))
    if len(matches) != 1:
        raise ValueError('Exactly one ordinary arm64 slice is required')
    return matches[0]


def _chained_bindings(data, command_range, segments, dylibs):
    """Decode real dyld chains (ordinary 64/64_OFFSET only), not nlist guesses.

    Layouts follow the platform SDK's mach-o/fixup-chains.h. A slot is accepted
    only if reachable from a page's declared chain start. Unsupported formats
    produce no bindings, so their stubs are conservatively excluded.
    """
    if command_range is None:
        return {}, {'mechanism': 'unconfirmed', 'reason': 'no LC_DYLD_CHAINED_FIXUPS; legacy binding not audited'}
    offset, length = command_range
    if offset + length > len(data):
        raise ValueError('Chained fixups exceed Mach-O slice')
    blob = data[offset:offset + length]
    version, starts_offset, imports_offset, symbols_offset, count, import_format, symbols_format = _unpack('<7I', blob, 0)
    metadata = {'mechanism': 'LC_DYLD_CHAINED_FIXUPS', 'slice_file_offset': offset,
                'data_size': length, 'fixups_version': version,
                'imports_format': import_format, 'imports_count': count,
                'symbols_format': symbols_format, 'unsupported_pointer_formats': []}
    if version != 0 or symbols_format != 0 or import_format not in (1, 2, 3):
        metadata['reason'] = 'unsupported chained-fixup header format'
        return {}, metadata
    imports = []
    for index in range(count):
        record_offset = imports_offset + index * {1: 4, 2: 8, 3: 16}[import_format]
        if import_format in (1, 2):
            encoded, = _unpack('<I', blob, record_offset)
            ordinal = encoded & 255
            if ordinal > 240:
                ordinal -= 256
            weak = bool((encoded >> 8) & 1)
            name_offset = encoded >> 9
            addend = _unpack('<i', blob, record_offset + 4)[0] if import_format == 2 else 0
        else:
            encoded, addend = _unpack('<Qq', blob, record_offset)
            ordinal = encoded & 65535
            if ordinal > 65520:
                ordinal -= 65536
            if (encoded >> 17) & 32767:
                raise ValueError('Nonzero reserved bits in chained import')
            weak = bool((encoded >> 16) & 1)
            name_offset = encoded >> 32
        name = _cstring(blob, symbols_offset + name_offset, len(blob))
        imports.append({'import_index': index, 'import_table_slice_file_offset': offset + record_offset,
                        'symbol': name, 'dylib_ordinal': ordinal,
                        'dylib': dylibs[ordinal - 1] if 1 <= ordinal <= len(dylibs) else None,
                        'weak_import': weak, 'import_addend': addend})
    segment_count, = _unpack('<I', blob, starts_offset)
    if segment_count != len(segments):
        raise ValueError('Dyld starts segment count differs from Mach-O segment order')
    starts = _unpack('<' + str(segment_count) + 'I', blob, starts_offset + 4)
    bases = [segment['address'] for segment in segments if segment['offset'] == 0 and segment['file_size'] > 0]
    if len(bases) != 1:
        raise ValueError('Cannot resolve unique Mach-O image base')
    bindings = {}
    for segment_index, relative in enumerate(starts):
        if not relative:
            continue
        info_offset = starts_offset + relative
        size, page_size, pointer_format, segment_offset, _, page_count = _unpack('<IHHQIH', blob, info_offset)
        if size < 22 + page_count * 2 or info_offset + size > len(blob) or page_size not in (0x1000, 0x4000):
            raise ValueError('Invalid dyld chain starts segment')
        segment = segments[segment_index]
        if segment_offset != segment['address'] - bases[0]:
            raise ValueError('Dyld chain segment offset disagrees with Mach-O segment')
        if pointer_format not in (2, 6):
            metadata['unsupported_pointer_formats'].append(pointer_format)
            continue
        all_starts = _unpack('<' + str((size - 22) // 2) + 'H', blob, info_offset + 22)
        for page_index in range(page_count):
            start = all_starts[page_index]
            if start == 0xFFFF:
                continue
            page_starts = [start]
            if start & 0x8000:
                page_starts = []
                overflow_index = start & 0x7FFF
                while True:
                    if overflow_index >= len(all_starts):
                        raise ValueError('Invalid multi-start dyld chain')
                    item = all_starts[overflow_index]
                    page_starts.append(item & 0x7FFF)
                    overflow_index += 1
                    if item & 0x8000:
                        break
            for page_start in page_starts:
                within_page = page_start
                while True:
                    if within_page + 8 > page_size:
                        raise ValueError('Dyld chain escaped its declared page')
                    within_segment = page_index * page_size + within_page
                    if within_segment + 8 > segment['file_size']:
                        raise ValueError('Dyld chain escaped file-backed segment bytes')
                    file_offset = segment['offset'] + within_segment
                    raw, = _unpack('<Q', data, file_offset)
                    address = segment['address'] + within_segment
                    if raw >> 63:  # dyld_chained_ptr_64_bind, formats 2 and 6
                        ordinal = raw & 0xFFFFFF
                        pointer_addend = (raw >> 24) & 255
                        if (raw >> 32) & 0x7FFFF or ordinal >= len(imports):
                            raise ValueError('Invalid chained bind pointer')
                        if address in bindings:
                            raise ValueError('Overlapping dyld bind chains')
                        imported = imports[ordinal]
                        bindings[address] = {
                            **imported, 'mechanism': 'LC_DYLD_CHAINED_FIXUPS',
                            'fixups_header_slice_file_offset': offset,
                            'pointer_format': pointer_format, 'imports_format': import_format,
                            'segment_index': segment_index, 'page_index': page_index,
                            'page_start': page_start, 'pointer_slice_file_offset': file_offset,
                            'pointer_raw_value': _hex(raw), 'pointer_addend': pointer_addend,
                            'effective_addend': pointer_addend + imported['import_addend'],
                        }
                    next_offset = ((raw >> 51) & 0xFFF) * 4
                    if not next_offset:
                        break
                    within_page += next_offset
    metadata['confirmed_bind_slots'] = len(bindings)
    return bindings, metadata


def parse_macho(path):
    """Read a thin/universal file and return JSON-safe arm64 binding evidence.

    `stubs` includes only mechanically validated complete pure-import bodies.
    Address and stub file offsets are relative to the selected arm64 slice;
    container offsets include its fat-slice offset. No dyld loading occurs.
    """
    path = Path(path)
    container = path.read_bytes()
    data, slice_offset = _arm64_slice(container)
    magic, cpu, subtype, filetype, count, command_bytes, flags, _ = _unpack('<8I', data, 0)
    if magic != 0xFEEDFACF or cpu != ARM64 or subtype != 0 or filetype != 2 or not flags & 0x80:
        raise ValueError('This audit requires an ordinary arm64 MH_EXECUTE image')
    command_end = 32 + command_bytes
    if command_end > len(data):
        raise ValueError('Mach-O load commands exceed slice')
    sections, dylibs, segments = [], [], []
    chained_range = None
    symtab = indirect_info = build_version = None
    position = 32
    for _ in range(count):
        command, length = _unpack('<II', data, position)
        if length < 8 or position + length > command_end:
            raise ValueError('Invalid Mach-O load command')
        if command == 0x19:  # LC_SEGMENT_64
            vmaddr, vmsize, fileoff, filesize = _unpack('<4Q', data, position + 24)
            segments.append({'address': vmaddr, 'memory_size': vmsize,
                             'offset': fileoff, 'file_size': filesize})
            section_count, = _unpack('<I', data, position + 64)
            if 72 + section_count * 80 > length:
                raise ValueError('Sections exceed segment command')
            for index in range(section_count):
                row = _unpack('<16s16sQQIIIIIIII', data, position + 72 + index * 80)
                sections.append({
                    'name': row[0].split(b'\0', 1)[0].decode(),
                    'segment': row[1].split(b'\0', 1)[0].decode(),
                    'address': row[2], 'size': row[3], 'offset': row[4],
                    'type': row[8] & 255, 'reserved1': row[9], 'reserved2': row[10],
                })
        elif command in (0xC, 0x80000018, 0x8000001F, 0x20, 0x80000023):
            name_offset, _, current, compatibility = _unpack('<IIII', data, position + 8)
            dylibs.append({
                'install_name': _cstring(data, position + name_offset, position + length),
                'load_command': _hex(command),
                'current_version': current, 'current_version_string': _version(current),
                'compatibility_version': compatibility,
                'compatibility_version_string': _version(compatibility),
            })
        elif command == 0x80000034:  # LC_DYLD_CHAINED_FIXUPS
            if chained_range is not None:
                raise ValueError('Duplicate chained-fixups command')
            chained_range = _unpack('<II', data, position + 8)
        elif command == 0x2:  # LC_SYMTAB
            if symtab is not None:
                raise ValueError('Duplicate symbol table')
            symtab = _unpack('<4I', data, position + 8)
        elif command == 0xB:  # LC_DYSYMTAB
            if indirect_info is not None:
                raise ValueError('Duplicate dynamic symbol table')
            indirect_info = _unpack('<18I', data, position + 8)[12:14]
        elif command == 0x32:
            platform, minimum, sdk, _ = _unpack('<4I', data, position + 8)
            build_version = {'platform': platform, 'minimum_os': minimum,
                             'minimum_os_string': _version(minimum),
                             'sdk': sdk, 'sdk_string': _version(sdk)}
        position += length
    if position != command_end or symtab is None or indirect_info is None:
        raise ValueError('Incomplete Mach-O command/symbol metadata')
    symbol_offset, symbol_count, string_offset, string_size = symtab
    if string_offset + string_size > len(data):
        raise ValueError('Invalid string table')
    symbols = []
    for index in range(symbol_count):
        string_index, kind, section, description, value = _unpack('<IBBHQ', data, symbol_offset + index * 16)
        if string_index >= string_size:
            raise ValueError('Symbol string is outside string table')
        ordinal = description >> 8
        dylib = dylibs[ordinal - 1] if 1 <= ordinal <= len(dylibs) else None
        symbols.append({
            'symbol_table_index': index,
            'symbol': _cstring(data, string_offset + string_index, string_offset + string_size),
            'n_type': kind, 'n_sect': section, 'n_desc': description, 'n_value': value,
            'dylib_ordinal': ordinal, 'dylib': dylib,
            'weak_import': bool(description & 0x40),
            'is_direct_import': kind & 0xE0 == 0 and kind & 0xE == 0 and bool(kind & 1)
                                and value == 0 and dylib is not None,
        })
    table_offset, table_count = indirect_info
    indirect = _unpack('<' + str(table_count) + 'I', data, table_offset)
    bindings, binding_metadata = _chained_bindings(data, chained_range, segments, dylibs)
    stubs, rejected = {}, Counter()
    for section in sections:
        if section['type'] != 8:  # S_SYMBOL_STUBS
            continue
        width = section['reserved2']
        if width == 0 or section['size'] % width:
            raise ValueError('Invalid symbol stub width')
        for index in range(section['size'] // width):
            address = section['address'] + index * width
            offset = section['offset'] + index * width
            if width != 12:
                rejected['not_three_instruction_stub'] += 1
                continue
            first, second, third = _unpack('<III', data, offset)
            if first & 0x9F00001F != 0x90000010 or second & 0xFFC003FF != 0xF9400210 or third != 0xD61F0200:
                rejected['not_adrp_ldr_br_x16'] += 1
                continue
            symbol_index = indirect[section['reserved1'] + index]
            if symbol_index & 0xC0000000 or symbol_index >= len(symbols):
                rejected['special_indirect_symbol'] += 1
                continue
            symbol = symbols[symbol_index]
            if not symbol['is_direct_import']:
                rejected['not_direct_undefined_dylib_import'] += 1
                continue
            immediate = (((first >> 5) & 0x7FFFF) << 2) | ((first >> 29) & 3)
            if immediate & (1 << 20):
                immediate -= 1 << 21
            pointer = (address & ~0xFFF) + (immediate << 12) + (((second >> 10) & 0xFFF) << 3)
            pointer_sections = [s for s in sections if s['type'] in (6, 7)
                                and s['address'] <= pointer < s['address'] + s['size']]
            if len(pointer_sections) != 1 or (pointer - pointer_sections[0]['address']) % 8:
                rejected['invalid_symbol_pointer_slot'] += 1
                continue
            pointer_section = pointer_sections[0]
            pointer_index = (pointer - pointer_section['address']) // 8
            bound_symbol = indirect[pointer_section['reserved1'] + pointer_index]
            if bound_symbol != symbol_index:
                rejected['pointer_binding_disagrees_with_stub_binding'] += 1
                continue
            pointer_offset = pointer_section['offset'] + pointer_index * 8
            pointer_raw, = _unpack('<Q', data, pointer_offset)
            binding = bindings.get(pointer)
            if binding is None:
                rejected['no_confirmed_dyld_chain_binding_for_pointer'] += 1
                continue
            if binding['symbol'] != symbol['symbol'] or binding['dylib_ordinal'] != symbol['dylib_ordinal'] or binding['dylib'] != symbol['dylib'] or binding['weak_import'] != symbol['weak_import']:
                rejected['dyld_binding_disagrees_with_nlist_indirect_binding'] += 1
                continue
            if binding['effective_addend'] != 0:
                rejected['sdk_entry_has_nonzero_binding_addend'] += 1
                continue
            if binding['pointer_slice_file_offset'] != pointer_offset or binding['pointer_raw_value'] != _hex(pointer_raw):
                raise ValueError('Dyld pointer location differs from decoded stub pointer slot')
            stubs[_hex(address)] = {
                'address': _hex(address), 'file_offset': offset,
                'container_file_offset': slice_offset + offset,
                'section': section['segment'] + ',' + section['name'],
                'body_size': 12, 'body_hex': data[offset:offset + 12].hex(),
                'instruction_words': [_hex(first), _hex(second), _hex(third)],
                'instructions': ['adrp x16, PAGE(symbol_pointer)',
                                 'ldr x16, [x16, PAGEOFF(symbol_pointer)]', 'br x16'],
                'pointer_address': _hex(pointer),
                'pointer_section': pointer_section['segment'] + ',' + pointer_section['name'],
                'pointer_file_offset': pointer_offset,
                'pointer_container_file_offset': slice_offset + pointer_offset,
                'pointer_raw_value': _hex(pointer_raw),
                'dyld_binding': binding,
                'indirect_symbol_index': symbol_index,
                'pointer_indirect_symbol_index': bound_symbol,
                'symbol': symbol['symbol'], 'dylib_ordinal': symbol['dylib_ordinal'],
                'n_type': symbol['n_type'], 'n_sect': symbol['n_sect'],
                'n_desc': symbol['n_desc'], 'weak_import': symbol['weak_import'],
                'dylib': symbol['dylib'],
                'cpu_type': _hex(cpu), 'cpu_subtype': _hex(subtype),
            }
    return {
        'container_sha256': sha256(container), 'arm64_sha256': sha256(data),
        'container_size': len(container), 'arm64_size': len(data), 'slice_offset': slice_offset,
        'cpu_type': _hex(cpu), 'cpu_subtype': _hex(subtype), 'file_type': filetype,
        'header_flags': _hex(flags), 'two_level_namespace': True,
        'dyld_binding_metadata': binding_metadata,
        'build_version': build_version, 'stubs': stubs, 'rejected_stub_counts': dict(rejected),
    }


def _repository_path(root, name):
    path = Path(name)
    if path.is_absolute() or '..' in path.parts or '.local' in path.parts:
        raise ValueError('Expected a public repository-relative source/evidence path')
    full = root / path
    if not full.is_file() or full.is_symlink():
        raise ValueError('Missing source/evidence file: ' + name)
    return full


def _source_manifest(root, product):
    paths = [root / 'replica/Package.swift']
    for target in PRODUCT_SOURCE_TARGETS[product]:
        directory = root / 'replica/Sources' / target
        paths.extend(sorted(path for path in directory.rglob('*')
                            if path.is_file() and path.suffix in {'.swift', '.m', '.h'}))
        resources = directory / 'Resources'
        if resources.is_dir():
            paths.extend(sorted(path for path in resources.rglob('*') if path.is_file()))
    return {str(path.relative_to(root)): sha256(path.read_bytes()) for path in sorted(paths)}


def _fragment_hashes(path):
    text = path.read_text()
    headers = list(HEADER.finditer(text))
    return {
        header.group(1): sha256((text[header.start():headers[index + 1].start()
                                    if index + 1 < len(headers) else len(text)].rstrip() + '\n').encode())
        for index, header in enumerate(headers)
    }


def _binding_key(stub):
    return (stub['symbol'], stub['dylib']['install_name'], stub['weak_import'],
            stub['dylib']['load_command'], stub['cpu_type'], stub['cpu_subtype'])


def generate_reuse_report(root):
    """Produce a stable static snapshot from installed manifest paths and release files.

    The caller must first finish its release build. This function never builds,
    changes a binary, executes app code, or assigns a tested/verified state.
    """
    root = Path(root).resolve()
    manifest_path = root / 'reports/target-manifest.json'
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    source_manifests = {product: _source_manifest(root, product) for product in TARGET_PRODUCTS.values()}
    functions, binaries, summaries, provenance = {}, {}, {}, {}
    fragments = {}
    for target, product in TARGET_PRODUCTS.items():
        original_row = next(row for row in manifest['binaries'] if row['name'].replace(' ', '-') == target)
        original_path = APPLICATION_ROOT / original_row['relative_path']
        replica_path = root / 'replica/.build/release' / product
        original, replica = parse_macho(original_path), parse_macho(replica_path)
        if original['container_sha256'] != original_row['sha256'] or original['arm64_sha256'] != original_row['arm64_sha256']:
            raise ValueError('Installed original does not match target manifest: ' + target)
        original_meta = {k: v for k, v in original.items() if k != 'stubs'}
        replica_meta = {k: v for k, v in replica.items() if k != 'stubs'}
        original_meta['path'] = str(original_path)
        original_meta['manifest_relative_path'] = original_row['relative_path']
        replica_meta['path'] = str(replica_path.relative_to(root))
        binaries[target] = {'original': original_meta, 'replica': replica_meta, 'replica_product': product}
        procedure_name = f'reports/{target}/procedures.json'
        index_name = f'reports/{target}/function-index.json'
        procedure_bytes = _repository_path(root, procedure_name).read_bytes()
        index_bytes = _repository_path(root, index_name).read_bytes()
        provenance[target] = {'procedures': {'path': procedure_name, 'sha256': sha256(procedure_bytes)},
                              'function_index': {'path': index_name, 'sha256': sha256(index_bytes)}}
        procedures = json.loads(procedure_bytes)
        index = {row['address']: row for row in json.loads(index_bytes)}
        replica_bindings = {}
        for stub in replica['stubs'].values():
            replica_bindings.setdefault(_binding_key(stub), []).append(stub)
        summary = Counter()
        for procedure in procedures:
            flags = procedure.get('procedure', {})
            address = procedure['address']
            if not address.startswith('0x') or not flags.get('thunk') or flags.get('external') or not str(flags.get('thunk_target')).startswith('EXTERNAL:'):
                continue
            summary['external_local_thunks'] += 1
            stub = original['stubs'].get(address)
            if stub is None:
                summary['not_a_validated_real_sdk_stub'] += 1
                continue
            matches = replica_bindings.get(_binding_key(stub), [])
            if len(matches) != 1:
                summary['no_unique_exact_counterpart_binding'] += 1
                continue
            item = index.get(address)
            if item is None:
                summary['missing_function_index_record'] += 1
                continue
            source = item['file']
            if source not in fragments:
                fragments[source] = _fragment_hashes(_repository_path(root, source))
            if address not in fragments[source]:
                raise ValueError('Missing indexed pseudocode fragment: ' + target + ':' + address)
            identifier = target + ':' + address
            functions[identifier] = {
                'function_id': identifier, 'classification': 'existing_external_sdk_delegate',
                'contract': 'arm64 纯转发：ADRP/LDR 从导入指针槽读取目标并 BR x16；不修改参数寄存器、栈或返回地址。SDK 内部实现不计入此契约。',
                'original_binary_sha256': original['arm64_sha256'],
                'original_container_sha256': original['container_sha256'],
                'original_pseudocode': {'path': source, 'line': item['line']},
                'original_pseudocode_sha256': fragments[source][address],
                'procedures_reference': {'path': procedure_name, 'address': address,
                                         'thunk_target': flags['thunk_target']},
                'function_index_reference': {'path': index_name, 'address': address},
                'original_stub': stub, 'replica_stub': matches[0],
                'replica_product': product, 'replica_binary_path': str(replica_path.relative_to(root)),
                'replica_binary_sha256': replica['container_sha256'],
                'source_manifest_key': product,
                'functional_regression_executed': False, 'equivalence_verified': False,
            }
            summary['candidate_count'] += 1
        summaries[target] = dict(summary)
    if manifest_path.read_bytes() != manifest_bytes:
        raise ValueError('Manifest changed during static snapshot')
    if any(_source_manifest(root, product) != hashes for product, hashes in source_manifests.items()):
        raise ValueError('Product sources changed during static snapshot')
    for pair in binaries.values():
        for side in ('original', 'replica'):
            meta = pair[side]
            path = Path(meta['path']) if side == 'original' else root / meta['path']
            if sha256(path.read_bytes()) != meta['container_sha256']:
                raise ValueError('Binary changed during static snapshot: ' + str(path))
    return {
        'schema_version': 1, 'kind': 'static_sdk_import_reuse',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'functional_regression_executed': False, 'equivalence_verified': False,
        'scope': '仅完整的本地 SDK 导入跳板；复用系统实现，不声称迁移 SDK 内部函数或证明调用方行为。',
        'target_manifest': {'path': 'reports/target-manifest.json', 'sha256': sha256(manifest_bytes)},
        'parser': {'path': 'scripts/macho_imports.py', 'sha256': sha256((root / 'scripts/macho_imports.py').read_bytes())},
        'source_sha256_by_product': source_manifests, 'binaries': binaries,
        'provenance': provenance, 'target_summary': summaries,
        'function_count': len(functions), 'functions': functions,
        'risks': [
            '原版与复刻链接 SDK 版本不同；系统函数可能读取进程 SDK/可用性信息，必须留待统一功能回归。',
            '相同完整 install name、原始符号和 ABI 表明委托入口相同，不证明 dyld 缓存映像字节或所有调用上下文等价。',
            '纯转发体复用不证明调用方参数、状态、UI、网络行为或 SDK 内部实现已经迁移。',
            '所有源文件、目标资源及 Package.swift 绑定当前已完成构建的静态快照；源码、资源或二进制变化将使报告失效。',
            'paste-mcp-stdio 不属于本报告显式比较的两个产品，没有据跨产品偶然导入计入迁移。',
        ],
    }


def verify_reuse_report(root, report_path):
    """Reparse current artifacts and return an address index or raise ValueError.

    root: repository root; report_path: public repository-relative report path,
    or an absolute path inside root. Every entry, complete source inventory,
    manifest/procedure/index digest, original/product binary SHA and stub binding
    is compared to a fresh static parse. No executable code is run.
    """
    root = Path(root).resolve()
    path = Path(report_path)
    if path.is_absolute():
        path = path.relative_to(root)
    report = json.loads(_repository_path(root, str(path)).read_text())
    if report.get('kind') != 'static_sdk_import_reuse' or report.get('functional_regression_executed') is not False or report.get('equivalence_verified') is not False:
        raise ValueError('Expected a migration-only SDK reuse report')
    current = generate_reuse_report(root)
    for field in ('schema_version', 'target_manifest', 'parser', 'source_sha256_by_product',
                  'binaries', 'provenance', 'target_summary', 'function_count', 'functions'):
        if report.get(field) != current[field]:
            raise ValueError('SDK reuse evidence changed or is invalid: ' + field)
    return report['functions']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--verify', type=Path, help='Only statically revalidate an existing report')
    parser.add_argument('--output', default=REPORT_PATH)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.verify:
        index = verify_reuse_report(root, args.verify)
        print(json.dumps({'statically_validated_entries': len(index), 'functional_tests_executed': False}))
        return
    report = generate_reuse_report(root)
    path = root / args.output
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    batch = {'functions': {
        key: {
            'state': 'migrated', 'contract': entry['contract'],
            'sdk_implementation': {'report': args.output, 'entry_key': key,
                                   'symbol': entry['original_stub']['symbol']},
            'implementation_origin': 'existing_sdk_reused',
            'review': '完整转发体、间接指针槽绑定、相同原始 SDK 符号/完整 dylib/load-kind/weak/arm64 ABI 已逐地址静态核实；没有新增空壳或实现引用。',
            'remaining': 'SDK/链接版本差异和所有运行期上下文留待全量迁移完成后统一功能回归。',
        } for key, entry in report['functions'].items()
    }}
    (root / '.local/sdk-reuse-migration-batch.json').write_text(json.dumps(batch, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'report': args.output, 'function_count': report['function_count'],
                      'target_summary': report['target_summary'], 'functional_tests_executed': False}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
