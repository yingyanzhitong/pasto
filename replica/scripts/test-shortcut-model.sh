#!/bin/bash
set -euo pipefail
replica_root="$(cd "$(dirname "$0")/.." && pwd)"
temporary="$(mktemp -d "${TMPDIR:-/tmp}/pasto-shortcut.XXXXXX")"
trap 'rm -rf "$temporary"' EXIT
swiftc -parse-as-library "$replica_root/Sources/PastoCore/KeyboardShortcut.swift" \
  "$replica_root/Sources/PastoCore/Models.swift" "$replica_root/Tests/HotKey/ShortcutModelHarness.swift" \
  -o "$temporary/harness"
if [[ $# -gt 0 ]]; then
  "$temporary/harness" > "$1"
  cat "$1"
else
  "$temporary/harness"
fi
