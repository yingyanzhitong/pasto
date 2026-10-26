#!/usr/bin/env python3
"""Build an address-complete implementation ledger without manufacturing implementations."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PAGE_SIZE = 1024
STATES = {"pending", "partial", "migrated", "implemented", "verified", "excluded_by_scope"}
HEADER = re.compile(r"^/\* Address: (0x[0-9a-f]+) \| .*? \*/$", re.MULTILINE)


def relative_file(root, value):
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or ".local" in path.parts:
        raise ValueError("Only public repository-relative evidence paths are allowed: " + value)
    result = root / path
    if not result.is_file() or result.is_symlink():
        raise ValueError("Missing evidence file: " + value)
    return result


def validate_sdk_review(root, key, review, result, cache):
    sdk = review["sdk_implementation"]
    if review["state"] != "migrated" or review.get("implementations") or review.get("tests"):
        raise ValueError("SDK reuse is migration-only binary evidence, not source or test evidence: " + key)
    path = relative_file(root, sdk["report"])
    cache_key = (str(root.resolve()), sdk["report"])
    if cache_key not in cache:
        spec = importlib.util.spec_from_file_location("macho_imports", root / "scripts/macho_imports.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cache[cache_key] = (module.verify_reuse_report(root, path), hashlib.sha256(path.read_bytes()).hexdigest())
    entries, report_digest = cache[cache_key]
    entry = entries.get(key)
    if (not entry or sdk.get("entry_key") != key
            or sdk.get("symbol") != entry["original_stub"]["symbol"]
            or result.get("sdk_implementation") != sdk
            or result.get("compiled_app_binary_sha256") != entry["replica_binary_sha256"]
            or result.get("original_binary_sha256") != entry["original_binary_sha256"]
            or result.get("original_pseudocode_sha256") != entry["original_pseudocode_sha256"]
            or result.get("sdk_reuse_report_sha256") != report_digest
            or review.get("contract") != entry["contract"]):
        raise ValueError("Address-specific original/compiled SDK stub binding is invalid: " + key)


def validate_review(root, key, review, sdk_cache=None):
    cache = sdk_cache if sdk_cache is not None else {}
    if not isinstance(review, dict) or review.get("state") not in STATES - {"pending"}:
        raise ValueError("Invalid explicit review state: " + key)
    if not review.get("contract"):
        raise ValueError("A reviewed function needs an individual contract: " + key)
    if review.get("sdk_implementation") and review["state"] != "migrated":
        raise ValueError("Static SDK reuse cannot claim tested function equivalence: " + key)
    for reference in review.get("implementations", []) + review.get("tests", []):
        source = relative_file(root, reference["path"]).read_text()
        if not reference.get("symbol") or reference["symbol"] not in source:
            raise ValueError("Evidence symbol is missing: " + key)
    if review["state"] in {"implemented", "verified"} and not review.get("implementations"):
        raise ValueError("Implementation required: " + key)
    if review["state"] == "migrated":
        if (not review.get("implementations") and not review.get("sdk_implementation")) or not review.get("migration_evidence"):
            raise ValueError("Migrated code needs implementation and static build evidence: " + key)
        result = json.loads(relative_file(root, review["migration_evidence"]).read_text())
        if result.get("function_id") != key or result.get("kind") != "static_code_migration":
            raise ValueError("Address-specific static migration evidence required: " + key)
        if result.get("build_succeeded") is not True or result.get("functional_regression_executed") is not False:
            raise ValueError("Migration-only evidence must separate compilation from regression: " + key)
        if "manifest" not in cache:
            cache["manifest"] = json.loads((root / "reports/target-manifest.json").read_text())
        manifest = cache["manifest"]
        target = key.split(":")[0]
        binary = next((row for row in manifest["binaries"] if row["name"].replace(" ", "-") == target), None)
        if not binary or result.get("original_binary_sha256") != binary["arm64_sha256"]:
            raise ValueError("Static migration must bind the analyzed original binary: " + key)
        index_key = ("index", target)
        if index_key not in cache:
            cache[index_key] = {row["address"]: row for row in json.loads((root / "reports" / target / "function-index.json").read_text())}
        entry = cache[index_key].get(key.split(":")[1])
        if entry:
            fragment_key = ("fragment", entry["file"])
            if fragment_key not in cache:
                cache[fragment_key] = source_fragments(relative_file(root, entry["file"]))
            fragment = cache[fragment_key][entry["address"]]
            if result.get("original_pseudocode_sha256") != fragment["sha256"]:
                raise ValueError("Static migration must bind the reviewed original function: " + key)
        else:
            fallback_file = root / "reports" / target / "assembly-fallbacks.json"
            fallbacks = json.loads(fallback_file.read_text()) if fallback_file.exists() else []
            fallback = next((row for row in fallbacks if row["address"] == key.split(":")[1]), None)
            if not fallback or result.get("original_assembly_sha256") != hashlib.sha256(relative_file(root, fallback["file"]).read_bytes()).hexdigest():
                raise ValueError("Failed decompilation needs reviewed assembly migration evidence: " + key)
        for reference in review.get("implementations", []):
            digest = hashlib.sha256(relative_file(root, reference["path"]).read_bytes()).hexdigest()
            if result.get("source_sha256", {}).get(reference["path"]) != digest:
                raise ValueError("Source changed since static migration build: " + key)
        if review.get("sdk_implementation"):
            validate_sdk_review(root, key, review, result, cache)
    contract_test = review.get("contract_test")
    if contract_test:
        report = json.loads(relative_file(root, contract_test["report"]).read_text())
        result = report["functions"].get(key)
        if not result or result.get("case") != contract_test["case"] or result.get("passed") is not True:
            raise ValueError("Missing passed address-specific contract result: " + key)
        for reference in review.get("implementations", []) + review.get("tests", []):
            digest = hashlib.sha256(relative_file(root, reference["path"]).read_bytes()).hexdigest()
            if result["source_sha256"].get(reference["path"]) != digest:
                raise ValueError("Source changed since contract test; rerun tests: " + key)
    if review["state"] in {"implemented", "verified"} and (not contract_test or not review.get("tests")):
        raise ValueError("A tested implementation needs explicit contract evidence: " + key)
    if review["state"] == "verified":
        evidence = review.get("equivalence_evidence")
        if not evidence or not review.get("tests"):
            raise ValueError("Feature tests alone cannot verify a function: " + key)
        result = json.loads(relative_file(root, evidence).read_text())
        if result.get("function_id") != key or result.get("passed") is not True:
            raise ValueError("Function-specific equivalence result required: " + key)
        if not result.get("original_inputs") or not result.get("replica_inputs") or not result.get("comparison"):
            raise ValueError("Original/replica comparison provenance required: " + key)
        manifest = json.loads((root / "reports/target-manifest.json").read_text())
        binary = next((row for row in manifest["binaries"] if row["name"].replace(" ", "-") == key.split(":")[0]), None)
        if not binary or result.get("original_binary_sha256") != binary["arm64_sha256"]:
            raise ValueError("Comparison must bind the analyzed original binary: " + key)
        if result.get("kind") != "original_machine_code_differential" or result.get("original_binary_executed") is not True:
            raise ValueError("Original machine-code execution required: " + key)
        section = result.get("original_text_section", {})
        if not re.fullmatch(r"[0-9a-f]{64}", section.get("sha256", "")) or section.get("size", 0) <= 0:
            raise ValueError("Original code-section integrity evidence required: " + key)
        cases = result.get("cases", [])
        if not cases or result.get("case_count") != len(cases) or any(case.get("equal") is not True for case in cases):
            raise ValueError("All recorded original/replica cases must pass: " + key)
        sources = result.get("source_sha256", {})
        references = review.get("implementations", []) + review.get("tests", [])
        if not {reference["path"] for reference in references}.issubset(sources):
            raise ValueError("Comparison must bind implementation and test sources: " + key)
        for path, digest in sources.items():
            if hashlib.sha256(relative_file(root, path).read_bytes()).hexdigest() != digest:
                raise ValueError("Source changed since original comparison; rerun differential tests: " + key)
    if review["state"] == "excluded_by_scope":
        evidence = review.get("scope_evidence", {})
        if not review.get("user_scope_reason") or evidence.get("entry_key") != key:
            raise ValueError("Exclusion needs an explicit per-address user scope reason: " + key)
        report = evidence.get("report", "")
        relative_file(root, report)
        scope_key = ("scope_exclusions", report)
        if scope_key not in cache:
            from scope_exclusions import verify_scope_report
            cache[scope_key] = verify_scope_report(root, report)
        entry = cache[scope_key].get(key)
        if not entry or review["user_scope_reason"] != entry["user_scope_reason"]:
            raise ValueError("Address-specific scope exclusion evidence is invalid: " + key)


def source_fragments(path):
    text = path.read_text()
    headers = list(HEADER.finditer(text))
    result = {}
    for i, match in enumerate(headers):
        address = match.group(1)
        if address in result:
            raise ValueError("Duplicate address in source: " + address)
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        body = text[match.start():end].rstrip() + "\n"
        result[address] = {
            "sha256": hashlib.sha256(body.encode()).hexdigest(),
            "line_count": len(body.splitlines()),
        }
    return result


def target_records(root, target, reviews, sdk_cache=None):
    folder = root / "reports" / target
    coverage = json.loads((folder / "coverage.json").read_text())
    procedures = json.loads((folder / "procedures.json").read_text())
    index = json.loads((folder / "function-index.json").read_text())
    exported = {row["address"]: row for row in index}
    failed = {row["address"]: row for row in coverage["failures"]}
    internal = [p for p in procedures if not p["procedure"]["external"]]
    addresses = [p["address"] for p in internal]
    if len(set(addresses)) != len(addresses) or len(exported) != len(index):
        raise ValueError("Duplicate inventory/index address: " + target)
    if set(exported) & set(failed) or set(exported) | set(failed) != set(addresses):
        raise ValueError("Every internal address, including failed decompilations, must be tracked: " + target)
    if len(internal) != coverage["internal_procedures"]:
        raise ValueError("Coverage denominator mismatch: " + target)
    fallback_path = folder / "assembly-fallbacks.json"
    fallbacks = {x["address"]: x for x in json.loads(fallback_path.read_text())} if fallback_path.exists() else {}
    fragments = {}
    rows = []
    for procedure in sorted(internal, key=lambda p: int(p["address"], 16)):
        address = procedure["address"]
        key = target + ":" + address
        if address in exported:
            source = exported[address]
            file = source["file"]
            if file not in fragments:
                fragments[file] = source_fragments(relative_file(root, file))
            fragment = fragments[file][address]
            original = {"state": "pseudocode_exported", "path": file,
                        "line": source["line"], **fragment}
        else:
            original = {"state": "decompilation_failed"}
            if address in fallbacks:
                file = fallbacks[address]["file"]
                data = relative_file(root, file).read_bytes()
                original.update(path=file, sha256=hashlib.sha256(data).hexdigest(),
                                limitation="Assembly slice; not a recovered complete semantic body")
        review = reviews.get(key)
        if review:
            validate_review(root, key, review, sdk_cache)
        rows.append({"id": key, "symbol": procedure["value"],
                     "kind": "local_thunk" if procedure["procedure"]["thunk"] else "native_function",
                     "thunk_target": procedure["procedure"].get("thunk_target"),
                     "original": original,
                     "review": review or {"state": "pending"}})
    return rows


def render(root):
    manifest = json.loads((root / "reports/target-manifest.json").read_text())
    mapping = json.loads((root / "replica/function-map.json").read_text())
    reviews = mapping["functions"]
    outputs, all_ids, targets = {}, set(), []
    sdk_cache = {}
    total_states = Counter()
    for binary in manifest["binaries"]:
        target = binary["name"].replace(" ", "-")
        records = target_records(root, target, reviews, sdk_cache)
        all_ids.update(r["id"] for r in records)
        states = Counter(r["review"]["state"] for r in records)
        total_states.update(states)
        pages = []
        for start in range(0, len(records), PAGE_SIZE):
            page = records[start:start + PAGE_SIZE]
            path = f"{target}/part-{start // PAGE_SIZE:04d}.jsonl"
            outputs[path] = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in page)
            pages.append({"path": path, "count": len(page), "first": page[0]["id"], "last": page[-1]["id"]})
        targets.append({"target": target, "original_binary_sha256": binary["arm64_sha256"],
                        "count": len(records), "local_thunks": sum(r["kind"] == "local_thunk" for r in records),
                        "states": {state: states[state] for state in sorted(STATES)}, "pages": pages})
    if set(reviews) - all_ids:
        raise ValueError("Reviews reference nonexistent function IDs: " + ", ".join(sorted(set(reviews) - all_ids)))
    migration_remaining = total_states["pending"] + total_states["partial"]
    summary = {"schema_version": 1, "scope": mapping["scope"], "total_functions": len(all_ids),
               "states": {state: total_states[state] for state in sorted(STATES)}, "targets": targets,
               "migration": {"code_complete": sum(total_states[state] for state in ("migrated", "implemented", "verified")),
                             "source_functions": sum(r["state"] in {"migrated", "implemented", "verified"} and not r.get("sdk_implementation") for r in reviews.values()),
                             "sdk_forwarders_reused": sum(r["state"] == "migrated" and bool(r.get("sdk_implementation")) for r in reviews.values()),
                             "remaining": migration_remaining,
                             "regression_ready": migration_remaining == 0,
                             "policy": "Finish all in-scope code migration before functional regression; retain explicit per-address scope exclusions."},
               "full_function_equivalence": False,
               "counting_rule": "Exported pseudocode, partial implementation, contract tests, SDK delegation and scope exclusions are not verified function equivalence."}
    outputs["summary.json"] = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    return outputs, summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--lookup", metavar="TARGET:ADDRESS")
    parser.add_argument("--require-migration-complete", action="store_true",
                        help="Read-only gate: refuse functional regression while code migration is incomplete")
    parser.add_argument("--record-contracts", type=Path, metavar="CORE_REPORT")
    args = parser.parse_args()
    if args.record_contracts:
        core = json.loads(args.record_contracts.read_text())
        if core.get("passed") is not True or core.get("failure_count") != 0:
            raise SystemExit("Core tests failed; cannot record passed contracts")
        cases = {test["name"]: test for test in core["tests"]}
        mappings = json.loads((ROOT / "replica/function-map.json").read_text())["functions"]
        results = {}
        for key, review in mappings.items():
            contract = review.get("contract_test")
            if not contract:
                continue
            if contract["case"] not in cases or cases[contract["case"]].get("passed") is not True:
                raise SystemExit("Missing successful contract case: " + key)
            references = review.get("implementations", []) + review.get("tests", [])
            results[key] = {"case": contract["case"], "passed": True,
                            "source_sha256": {ref["path"]: hashlib.sha256(relative_file(ROOT, ref["path"]).read_bytes()).hexdigest() for ref in references}}
        binary = ROOT / "replica/.build/release/pasto-core-tests"
        report = {"kind": "replica_contract_tests_only", "native_runner_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
                  "core_test_count": core["test_count"], "original_binary_executed": False,
                  "function_equivalence_verified": False, "functions": results}
        (ROOT / "reports/replica/function-contracts.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    output = ROOT / "reports/function-implementation"
    generated, summary = render(ROOT)
    if args.require_migration_complete:
        print(json.dumps(summary["migration"], ensure_ascii=False, indent=2))
        if not summary["migration"]["regression_ready"]:
            raise SystemExit(2)
        return
    if args.lookup:
        for name, content in generated.items():
            if name.endswith(".jsonl"):
                for line in content.splitlines():
                    value = json.loads(line)
                    if value["id"] == args.lookup:
                        print(json.dumps(value, ensure_ascii=False, indent=2))
                        return
        raise SystemExit("Unknown function ID: " + args.lookup)
    existing = {str(p.relative_to(output)) for p in output.rglob("*") if p.is_file()} if output.exists() else set()
    stale = existing - set(generated)
    if stale:
        raise SystemExit("Unexpected ledger files; review instead of deleting: " + ", ".join(sorted(stale)))
    for name, content in generated.items():
        path = output / name
        if args.check:
            if not path.exists() or path.read_text() != content:
                raise SystemExit("Stale or missing ledger: " + str(path.relative_to(ROOT)))
        elif not path.exists() or path.read_text() != content:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    print(json.dumps({"checked": args.check, "total_functions": summary["total_functions"],
                      "states": summary["states"], "full_function_equivalence": False}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
