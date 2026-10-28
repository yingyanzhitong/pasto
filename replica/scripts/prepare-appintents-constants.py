#!/usr/bin/env python3
"""Extract production AppIntents compiler constants, never system registration metadata.

Requires a successful source/build SHA receipt. Does not modify an app bundle,
invoke intent actions, or run appintentsmetadataprocessor. Normal builds are unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {
    "PastoCreateItemIntent": "AppIntent",
    "PastoCreatePinboardIntent": "AppIntent",
    "PastoGetItemAtIndexIntent": "AppIntent",
    "PastoGetLatestItemIntent": "AppIntent",
    "PastoPinboardEntity": "AppEntity",
    "PastoPinboardQuery": "EntityQuery",
    "PastoLatestItemType": "AppEnum",
    "PastoShortcutsProvider": "AppShortcutsProvider",
}
SOURCE_SUFFIXES = {".swift", ".m", ".h", ".strings", ".stringsdict", ".modulemap"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv):
    return subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def source_snapshot():
    sources = [ROOT / "replica/Package.swift"] + sorted(
        p for p in (ROOT / "replica/Sources").rglob("*")
        if p.is_file() and p.suffix in SOURCE_SUFFIXES
    )
    return {str(p.relative_to(ROOT)): digest(p) for p in sources}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-directory", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--arch", choices=["arm64", "x86_64"], required=True)
    args = parser.parse_args()
    build = args.build_directory.resolve()
    receipt_path = args.receipt.resolve()
    output = args.output_directory.absolute()
    if output.exists() or output.is_symlink():
        raise ValueError("Output directory already exists; no files were overwritten")
    receipt_bytes = receipt_path.read_bytes()
    receipt = json.loads(receipt_bytes)
    if receipt.get("kind") != "isolated_swiftpm_build_receipt" or receipt.get("exit_code") != 0:
        raise ValueError("A successful isolated SwiftPM build receipt is required")
    source_hashes = source_snapshot()
    if source_hashes != receipt.get("source_sha256"):
        raise ValueError("Receipt source inventory/SHA differs from current production sources; rebuild first")
    products = [build / "Pasto", build / "Modules/Pasto.swiftmodule", build / "Modules/PastoCore.swiftmodule"]
    product_hashes = {str(p): digest(p) for p in products}
    recorded_products = receipt.get("products_sha256", {})
    resolved_products = {str(Path(p).resolve()): sha for p, sha in recorded_products.items()}
    if len(resolved_products) != len(recorded_products) or product_hashes != resolved_products:
        raise ValueError("Compiled executable/module paths or SHA differ from the build receipt")
    description_path = build / "description.json"
    description_bytes = description_path.read_bytes()
    commands = [c for c in json.loads(description_bytes)["swiftCommands"].values()
                if c["moduleName"] == "Pasto"]
    if len(commands) != 1:
        raise ValueError("Expected one actual Pasto module compile command")
    command = commands[0]
    other_args = command["otherArguments"]
    target = other_args[other_args.index("-target") + 1]
    if not target.startswith(args.arch + "-apple-macos"):
        raise ValueError("Build target architecture/platform does not match --arch")
    intents = sorted((ROOT / "replica/Sources/Pasto/AppIntents").glob("*.swift"))
    if not intents or not {str(p) for p in intents}.issubset(set(command["sources"])):
        raise ValueError("AppIntents sources are absent from the actual Pasto build command")
    swiftc_probe = run(["xcrun", "--find", "swiftc"])
    sdk_probe = run(["xcrun", "--sdk", "macosx", "--show-sdk-path"])
    if swiftc_probe.returncode or sdk_probe.returncode:
        raise ValueError("Selected Swift compiler/SDK could not be resolved")
    swiftc = Path(swiftc_probe.stdout.strip())
    if swiftc.resolve() != Path(command["executable"]).resolve():
        raise ValueError("Selected compiler differs from the successful build compiler")
    processor = run(["xcrun", "--find", "appintentsmetadataprocessor"])
    report = {
        "status": "constants_extraction_pending",
        "scope": "compiler_constants_only",
        "source_sha256": source_hashes,
        "products_sha256": product_hashes,
        "receipt_sha256": hashlib.sha256(receipt_bytes).hexdigest(),
        "target": target,
        "swiftc": str(swiftc),
        "swift_version": run([str(swiftc), "--version"]).stdout.strip(),
        "sdk": sdk_probe.stdout.strip(),
        "metadata_processor_found": processor.returncode == 0,
        "metadata_processor_probe": processor.stdout.strip(),
        "final_metadata_generated": False,
        "system_registration_verified": False,
        "product_or_functional_tests_executed": False,
    }
    output.mkdir(parents=True)
    try:
        protocols = output / "protocols.json"
        protocols.write_text(json.dumps(sorted(set(EXPECTED.values()))) + "\n")
        constants = output / "Pasto.swiftconstvalues"
        argv = [str(swiftc), "-frontend", "-typecheck", "-parse-as-library", "-module-name", "Pasto",
                "-target", target, "-sdk", sdk_probe.stdout.strip(), "-swift-version", "5",
                "-I", str(build / "Modules"), "-I", str(ROOT / "replica/Sources/PastoObjC/include"),
                "-module-cache-path", str(output / "ModuleCache")]
        argv += [a for a in other_args if a.startswith("-D")]
        argv += [str(p) for p in intents]
        argv += ["-const-gather-protocols-file", str(protocols), "-emit-const-values-path", str(constants)]
        result = run(argv)
        (output / "compiler.log").write_text(result.stdout)
        report.update(command=argv, compiler_exit_code=result.returncode)
        if result.returncode:
            raise ValueError("Production AppIntents typecheck/constant extraction failed; see compiler.log")
        values = json.loads(constants.read_text())
        actual = {v["typeName"]: v for v in values}
        wanted = {"Pasto." + name for name in EXPECTED}
        if len(values) != len(wanted) or set(actual) != wanted:
            raise ValueError("Extracted type count/names differ from the eight expected production declarations")
        for name, protocol in EXPECTED.items():
            if "AppIntents." + protocol not in actual["Pasto." + name]["conformances"]:
                raise ValueError("Unexpected extracted conformance for " + name)
        if source_snapshot() != source_hashes:
            raise ValueError("Production source changed during extraction")
        if any(digest(Path(p)) != sha for p, sha in product_hashes.items()):
            raise ValueError("Compiled product/module changed during extraction")
        if receipt_path.read_bytes() != receipt_bytes or description_path.read_bytes() != description_bytes:
            raise ValueError("Build receipt/description changed during extraction")
        report.update(status="compiler_constants_ready_final_metadata_not_generated",
                      extracted_types=sorted(actual), expected_type_count=len(wanted),
                      constants_sha256=digest(constants))
    except Exception as error:
        report.update(status="failed", error=str(error))
        raise
    finally:
        (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "types": len(EXPECTED),
                      "report": str(output / "report.json"), "system_registration_verified": False}))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
