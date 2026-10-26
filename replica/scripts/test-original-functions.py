#!/usr/bin/env python3
"""Execute a small, explicitly recovered arm64 ABI whitelist against local Paste.

No original binary, user clipboard, or original application data is published.
The original executable entry point is never invoked.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SOURCES = [
    "replica/Tests/Original/FunctionOracle.swift", "replica/Tests/Original/OracleABI.h",
    "replica/Tests/Original/OracleABI.s", "replica/scripts/test-original-functions.py",
    "replica/Tests/Original/OracleObjects.m",
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def text_section(data):
    if struct.unpack_from("<I", data)[0] != 0xFEEDFACF:
        raise ValueError("A thin little-endian Mach-O64 is required")
    cursor = 32
    for _ in range(struct.unpack_from("<I", data, 16)[0]):
        command, length = struct.unpack_from("<II", data, cursor)
        if command == 0x19:
            for index in range(struct.unpack_from("<I", data, cursor + 64)[0]):
                section = cursor + 72 + index * 80
                if data[section:section + 16].rstrip(b"\0") == b"__text" and data[section + 16:section + 32].rstrip(b"\0") == b"__TEXT":
                    address, size, offset = struct.unpack_from("<QQI", data, section + 32)
                    return {"address": hex(address), "size": size, "offset": offset,
                            "sha256": sha(data[offset:offset + size])}
        cursor += length
    raise ValueError("Missing __TEXT,__text section")


def run(command, log, timeout=180):
    with log.open("ab") as output:
        subprocess.run([str(x) for x in command], cwd=ROOT, stdout=output, stderr=output,
                       check=True, timeout=timeout)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", type=Path, default=Path("/Applications/Paste.app/Contents/MacOS/Paste"))
    parser.add_argument("--work", type=Path, default=ROOT / ".local/original-function-tests")
    args = parser.parse_args()
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise SystemExit("This recovered ABI harness requires native arm64 macOS")
    work = args.work.resolve()
    if not work.is_relative_to(ROOT / ".local"):
        raise SystemExit("Original binary copies must stay in the Git-ignored .local directory")
    work.mkdir(parents=True, exist_ok=True)
    log = work / "run.log"
    log.write_text("")
    manifest = json.loads((ROOT / "reports/target-manifest.json").read_text())
    target = next(row for row in manifest["binaries"] if row["name"] == "Paste")
    original = args.original.resolve()
    original_hash = sha(original.read_bytes())
    if original_hash == target["arm64_sha256"]:
        thin = original.read_bytes()
    elif original_hash == target["sha256"]:
        run(["/usr/bin/lipo", original, "-thin", "arm64", "-output", work / "Paste.arm64"], log)
        thin = (work / "Paste.arm64").read_bytes()
    else:
        raise SystemExit("Original binary differs from the REA manifest; refusing unsafe address calls")
    if sha(thin) != target["arm64_sha256"]:
        raise SystemExit("arm64 slice hash mismatch")
    section = text_section(thin)
    if struct.unpack_from("<I", thin, 12)[0] != 2:
        raise SystemExit("Expected original MH_EXECUTE file type")
    patched = bytearray(thin)
    struct.pack_into("<I", patched, 12, 8)  # MH_BUNDLE permits dlopen; never run original main.
    bundle = work / "Paste.oracle.bundle"
    bundle.write_bytes(patched)
    run(["/usr/bin/codesign", "--force", "--sign", "-", bundle], log)
    if text_section(bundle.read_bytes()) != section:
        raise SystemExit("Signing/header conversion changed the original __text section")
    run(["swift", "build", "--package-path", "replica", "-c", "release"], log)
    run(["xcrun", "clang", "-c", ROOT / SOURCES[2], "-o", work / "OracleABI.o"], log)
    run(["xcrun", "clang", "-fobjc-arc", "-c", ROOT / SOURCES[4], "-o", work / "OracleObjects.o"], log)
    objects = sorted((ROOT / "replica/.build/release/PastoCore.build").glob("*.o"))
    if not objects:
        raise SystemExit("Missing replica core object files")
    runner = work / "function-oracle"
    run(["xcrun", "swiftc", "-parse-as-library", "-swift-version", "5",
         "-I", ROOT / "replica/.build/release/Modules", "-import-objc-header", ROOT / SOURCES[1],
         ROOT / SOURCES[0], work / "OracleABI.o", work / "OracleObjects.o", *objects, "-o", runner], log)
    sandbox = work / "no-network-or-user-data.sb"
    denied = [Path.home() / "Library" / name for name in ["Application Support", "Containers", "Group Containers"]]
    sandbox.write_text('(version 1)\n(allow default)\n(deny network*)\n(deny file-read* file-write*\n'
                       + "\n".join("  (subpath " + json.dumps(str(path)) + ")" for path in denied) + ')\n')
    output = work / "results.json"
    output.unlink(missing_ok=True)
    run(["/usr/bin/sandbox-exec", "-f", sandbox, runner, bundle, output], log, timeout=240)
    raw = json.loads(output.read_text())
    if raw.get("passed") is not True or len(raw["functions"]) != 13:
        raise SystemExit("Missing successful native comparison results")
    mappings = json.loads((ROOT / "replica/function-map.json").read_text())["functions"]
    reports = ROOT / "reports/function-equivalence"
    reports.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    for key, cases in raw["functions"].items():
        if not cases or any(row.get("equal") is not True for row in cases):
            raise SystemExit("Unsuccessful comparison: " + key)
        references = mappings[key]["implementations"] + mappings[key]["tests"]
        paths = sorted(set(SOURCES + [ref["path"] for ref in references]))
        report = {
            "schema_version": 1, "kind": "original_machine_code_differential", "function_id": key,
            "passed": True, "tested_at": timestamp, "original_binary_executed": True,
            "original_binary_sha256": sha(thin), "original_text_section": section,
            "loader_changes": ["MH_EXECUTE to MH_BUNDLE header", "ad-hoc signature"],
            "original_entry_point_executed": False, "original_user_data_access": False,
            "sandbox_network_denied": True, "sandbox_profile_sha256": sha(sandbox.read_bytes()),
            "runner_sha256": sha(runner.read_bytes()), "replica_object_sha256": {
                path.name: sha(path.read_bytes()) for path in objects},
            "source_sha256": {path: sha((ROOT / path).read_bytes()) for path in paths},
            "original_inputs": "cases[].input; synthetic images/objects only; same values supplied to original code",
            "replica_inputs": "cases[].input; same synthetic data or same Vision observations",
            "comparison": "Exact Data bytes, token strings/Float confidence/CGRect?, NSError domain/code/userInfo; array identity/order/COW, scalar count/boolean, cached constraint identity/anchor/activation and immediate/settled height as applicable",
            "environment": {"macos": raw["macos"], "architecture": platform.machine(), "word_layout": raw["word_layout"]},
            "case_count": len(cases), "cases": cases,
            "limits": ["Only listed cases and recovered source-level contracts; not proof over every possible input",
                       "Replica has its own Swift types and symbols; binary ABI/type identity is not promised",
                       "OCR wrapper comparison checks original word-array contract; replica also retains line text",
                       "No original UI entry point or private application state is executed"],
        }
        if key in {"Paste:0x100082b90", "Paste:0x100083a20", "Paste:0x100085230", "Paste:0x100085670"}:
            report["limits"].extend([
                "Original snippets use synthetic NSObject elements; only Array count is read, no original snippet members are accessed",
                "Replica uses ClipboardItem elements with the same count; this is source-contract comparison, not memory-layout identity",
                "Height comparison uses a zero-duration animation group and a later run-loop turn; full animation curves and missing-outlet traps are not verified",
            ])
        (reports / (key.replace(":", "-") + ".json")).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"passed": True, "functions": len(raw["functions"]),
                      "cases": sum(len(cases) for cases in raw["functions"].values()),
                      "original_text_sha256": section["sha256"]}, indent=2))


if __name__ == "__main__":
    main()
