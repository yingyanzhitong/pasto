#!/usr/bin/env python3
"""校验导出覆盖率、函数索引和待公开文本；不输出匹配到的凭据。"""
import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXCLUDED = {".local", ".git", "__pycache__"}


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def verify_target(binary):
    name = binary["name"].replace(" ", "-")
    report = ROOT / "reports" / name
    for filename in ("coverage.json", "function-index.json", "procedures.json"):
        require((report / filename).is_file(), name + ": 缺少 " + filename)
    coverage = json.loads((report / "coverage.json").read_text())
    index = json.loads((report / "function-index.json").read_text())
    procedures = json.loads((report / "procedures.json").read_text())
    require(coverage["target"] == name and coverage["architecture"] == binary["analyzed_architecture"],
            name + ": 分析目标不一致")
    require(coverage["sha256"] == binary["arm64_sha256"], name + ": 哈希不一致")
    target = ROOT / ".local/targets" / (name + ".arm64")
    if target.is_file():
        require(hashlib.sha256(target.read_bytes()).hexdigest() == binary["arm64_sha256"],
                name + ": 本地分析输入哈希不一致")
    for key in ("total_procedures", "internal_procedures", "external_procedures_skipped",
                "internal_thunks", "succeeded", "failed"):
        require(type(coverage[key]) is int and coverage[key] >= 0, name + ": 统计值无效")
    internal = [p for p in procedures if not p["procedure"]["external"]]
    require(len(procedures) == coverage["total_procedures"]
            and len(internal) == coverage["internal_procedures"]
            and len(procedures) - len(internal) == coverage["external_procedures_skipped"]
            and sum(p["procedure"]["thunk"] for p in internal) == coverage["internal_thunks"],
            name + ": 过程清单与统计不一致")
    require(coverage["succeeded"] + coverage["failed"] == len(internal)
            and len(index) == coverage["succeeded"]
            and len(coverage["failures"]) == coverage["failed"], name + ": 导出计数不一致")
    addresses = [item["address"] for item in index] + [item["address"] for item in coverage["failures"]]
    require(len(set(addresses)) == len(addresses)
            and set(addresses) == {p["address"] for p in internal}, name + ": 导出地址与过程清单不一致")
    source_lines = {}
    for item in index:
        path = pathlib.Path(item["file"])
        require(not path.is_absolute() and ".." not in path.parts
                and path.parts[:2] == ("decompiled", name)
                and not EXCLUDED.intersection(path.parts), name + ": 索引文件路径无效")
        source = ROOT / path
        require(source.resolve().is_relative_to((ROOT / "decompiled" / name).resolve()),
                name + ": 索引文件指向目标目录之外")
        if item["file"] not in source_lines:
            source_lines[item["file"]] = source.read_text().splitlines()
        lines = source_lines[item["file"]]
        require(type(item["line"]) is int and 2 <= item["line"] <= len(lines),
                name + ": 索引行号越界")
        require(bool(lines[item["line"] - 1].strip()), name + ": 索引未指向首个非空伪代码行")
        header = item["line"] - 2
        while header >= 0 and not lines[header].strip():
            header -= 1
        require(header >= 0 and lines[header].startswith("/* Address: " + item["address"] + " | "),
                name + ": 索引地址与源码行不一致")
    return {"target": name, "succeeded": coverage["succeeded"], "failed": coverage["failed"],
            "local_input_sha256_checked": target.is_file()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--secret-source", type=pathlib.Path)
    args = parser.parse_args()
    secrets = []
    if args.secret_source:
        for line in args.secret_source.read_text().splitlines():
            if re.search(r"token|secret|password|密钥|令牌|密码", line, re.I):
                value = re.split(r"[：:]\s*", line)[-1].strip().strip("`\"'")
                if len(value) >= 16 and re.fullmatch(r"[\w+/=.\-]+", value):
                    secrets.append(value)
    patterns = [r"gh[pousr]_[A-Za-z0-9]{30,}", r"github_pat_[A-Za-z0-9_]{30,}",
                r"GOCSPX-[A-Za-z0-9_-]{20,}", r"sk-(?:proj-)?[A-Za-z0-9_-]{40,}",
                r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"]
    # Check exactly the tracked and publishable untracked files, excluding local builds.
    names = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT
    ).decode().split("\0")
    files = [ROOT / name for name in sorted(set(names)) if name and (ROOT / name).is_file()]
    issues = []
    binary_assets = {
        "replica/Assets/PastoIcon.png": b"\x89PNG\r\n\x1a\n",
        "replica/Assets/Pasto.icns": b"icns",
    }
    binary_count = 0
    for path in files:
        if path.name == ".DS_Store":
            continue
        if path.is_symlink():
            issues.append(str(path.relative_to(ROOT)) + ": 不允许公开符号链接")
            continue
        data = path.read_bytes()
        asset_header = binary_assets.get(str(path.relative_to(ROOT)))
        if asset_header is not None:
            require(data.startswith(asset_header), str(path.relative_to(ROOT)) + ": 图标格式不符")
            if asset_header == b"icns":
                require(len(data) >= 8 and int.from_bytes(data[4:8], "big") == len(data), "ICNS 长度不符")
            text = data.decode("latin-1")
            binary_count += 1
        else:
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                issues.append(str(path.relative_to(ROOT)) + ": 非文本文件")
                continue
        if any(re.search(pattern, text) for pattern in patterns) or any(s in text for s in secrets):
            issues.append(str(path.relative_to(ROOT)) + ": 疑似凭据")
    if issues:
        raise SystemExit("\n".join(issues))
    manifest = json.loads((ROOT / "reports/target-manifest.json").read_text())
    totals = [verify_target(binary) for binary in manifest["binaries"]]
    function_ledger = None
    if (ROOT / "reports/function-implementation/summary.json").exists():
        function_ledger = json.loads(subprocess.check_output(
            [sys.executable, str(ROOT / "scripts/function_ledger.py"), "--check"], cwd=ROOT, text=True))
    print(json.dumps({"verified": True, "public_text_files": len(files) - binary_count, "public_binary_assets": binary_count,
                      "known_secret_values_checked": len(secrets), "targets": totals,
                      "function_implementation_ledger": function_ledger}, indent=2))


if __name__ == "__main__":
    main()
