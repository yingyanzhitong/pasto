#!/usr/bin/env python3
"""按目标和地址从已导出的反编译索引直接读取伪代码，不调用分析引擎。"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ("Paste", "Paste-Helper", "paste-mcp-stdio")
HEADER = re.compile(r"^/\* Address: (0x[0-9a-fA-F]+) \| .* \*/$", re.MULTILINE)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", choices=TARGETS)
    parser.add_argument("addresses", nargs="+", help="一个或多个十六进制函数起始地址")
    args = parser.parse_args()
    try:
        addresses = ["0x%x" % int(value, 16) for value in args.addresses]
    except ValueError:
        parser.error("地址必须是十六进制函数起始地址")
    rows = json.loads((ROOT / "reports" / args.target / "function-index.json").read_text())
    index = {}
    for row in rows:
        key = row["address"].lower()
        if key in index:
            parser.exit(1, "函数索引含重复地址。\n")
        index[key] = row
    file_cache = {}
    fragments = []
    for address in addresses:
        row = index.get(address)
        if row is None:
            parser.exit(1, "索引中没有成功导出的函数；没有读取或重试失败地址。\n")
        relative = Path(row["file"])
        expected = Path("decompiled") / args.target
        if relative.is_absolute() or ".." in relative.parts or relative.parent != expected:
            parser.exit(1, "索引文件路径无效。\n")
        if relative not in file_cache:
            text = (ROOT / relative).read_text()
            file_cache[relative] = (text, list(HEADER.finditer(text)))
        text, headers = file_cache[relative]
        matches = [(i, match) for i, match in enumerate(headers) if match.group(1).lower() == address]
        if len(matches) != 1:
            parser.exit(1, "伪代码分片中没有唯一的地址标记。\n")
        i, match = matches[0]
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        fragments.append(text[match.start():end].rstrip())
    print("\n\n".join(fragments))


if __name__ == "__main__":
    main()
