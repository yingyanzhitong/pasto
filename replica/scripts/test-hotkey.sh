#!/bin/bash
# 可选首参数为 JSON 报告路径。不会发送系统按键，也不读写剪贴板。
set -euo pipefail
replica_root="$(cd "$(dirname "$0")/.." && pwd)"
temporary="$(mktemp -d "${TMPDIR:-/tmp}/pasto-hotkey.XXXXXX")"
trap 'rm -rf "$temporary"' EXIT
swiftc -parse-as-library "$replica_root/Sources/Pasto/GlobalHotKey.swift" \
  "$replica_root/Tests/HotKey/HotKeyHarness.swift" -o "$temporary/harness"
if [[ $# -gt 0 ]]; then
  "$temporary/harness" > "$1"
  cat "$1"
else
  "$temporary/harness"
fi
