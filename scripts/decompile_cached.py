#!/usr/bin/env python3
"""从本地 REA 缓存离线重建伪代码；不打开二进制或覆盖已有目录。"""
import argparse
import json
from pathlib import Path

from decompile import ROOT, public_failure

TARGETS = ("Paste", "Paste-Helper", "paste-mcp-stdio")


def export_target(name, destination):
    local = ROOT / ".local" / name
    inventory = json.loads((local / "procedures.json").read_text())
    procedures = inventory["normalized_result"]
    internal = [p for p in procedures if not p["procedure"]["external"]]
    output = destination / "decompiled" / name
    report = destination / "reports" / name
    output.mkdir(parents=True)
    report.mkdir(parents=True)
    failures, index = [], []
    limitations = set(inventory.get("limitations", []))
    for offset in range(0, len(internal), 64):
        addresses = [p["address"] for p in internal[offset:offset + 64]]
        cache = local / ("batch-%04d.json" % (offset // 64))
        try:
            evidence = json.loads(cache.read_text())
        except (OSError, ValueError) as exc:
            raise ValueError(f"缓存缺失或损坏：{cache}") from exc
        if (evidence.get("parameters", {}).get("addresses") != addresses
                or evidence.get("subject", {}).get("digest") != inventory["subject"]["digest"]
                or evidence.get("analysis_profile", {}).get("parameters", {}).get("upstream_analysis_profile")
                != inventory["analysis_profile"]):
            raise ValueError(f"缓存与目标或分析配置不一致：{cache}")
        result = evidence["normalized_result"]
        if result["total"] != len(addresses) or [i["address"] for i in result["items"]] != addresses:
            raise ValueError(f"缓存地址或数量不一致：{cache}")
        limitations.update(evidence.get("limitations", []))
        filename = "part-%04d.c" % (offset // 64)
        parts = ["/* REA 6.7.0 / Ghidra 12.1.4: arm64 decompiler pseudocode.\n"
                 " * Generated analysis output; not original or buildable source. */\n"]
        line = parts[0].count("\n") + 1
        for item in result["items"]:
            if item["status"] != "ok":
                failures.append(public_failure(item))
                continue
            code = item["pseudocode"]
            label = str(item["procedure"].get("name", item["address"])).replace("*/", "* /")
            header = "\n/* Address: %s | %s */\n" % (item["address"], label)
            parts.append(header + code + "\n")
            leading = code[:len(code) - len(code.lstrip())].count("\n")
            index.append({"address": item["address"], "procedure": item["procedure"],
                          "file": f"decompiled/{name}/{filename}", "line": line + 2 + leading})
            line += (header + code + "\n").count("\n")
        (output / filename).write_text("".join(parts))
    coverage = {"target": name, "architecture": "arm64", "sha256": inventory["subject"]["digest"]["sha256"],
                "inventory_evidence_id": inventory["evidence_id"], "analysis_profile": inventory["analysis_profile"],
                "internal_procedures": len(internal), "succeeded": len(index), "failed": len(failures),
                "failures": failures, "limitations": sorted(limitations),
                "source": "local REA evidence cache; no new decompilation"}
    if len(index) + len(failures) != len(internal):
        raise ValueError(f"{name} 导出数量不一致")
    (report / "function-index.json").write_text(json.dumps(index, indent=2) + "\n")
    (report / "coverage.json").write_text(json.dumps(coverage, indent=2) + "\n")
    return {"target": name, "succeeded": len(index), "failed": len(failures)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="不存在的新输出目录")
    parser.add_argument("targets", nargs="*", help="目标名，省略时处理全部目标")
    args = parser.parse_args()
    if any(name not in TARGETS for name in args.targets) or len(set(args.targets)) != len(args.targets):
        parser.error("目标名无效或重复")
    args.targets = args.targets or list(TARGETS)
    destination = args.output.absolute()
    if destination.exists() or destination.is_symlink():
        parser.error("输出目录已存在；为保护已有文件，请指定新目录")
    if not destination.parent.is_dir():
        parser.error("输出目录的父目录不存在")
    # mkdir 是独占创建；失败时保留新目录和已写文件，便于检查，不删除任何数据。
    try:
        destination.mkdir()
    except FileExistsError:
        parser.error("输出目录已存在；为保护已有文件，请指定新目录")
    result = [export_target(name, destination) for name in args.targets]
    print(json.dumps({"output": str(destination), "targets": result}, ensure_ascii=False))


if __name__ == "__main__":
    main()
