#!/bin/bash
# 可选首参数为 JSON 报告路径。不会发送系统按键，也不读写剪贴板。
set -euo pipefail
replica_root="$(cd "$(dirname "$0")/.." && pwd)"
test_root="$(mktemp -d "${TMPDIR:-/tmp}/pasto-hotkey.XXXXXX")"
trap 'rm -rf "$test_root"' EXIT
source "$replica_root/Tests/Native/build-support.sh"
prepare_native_test_core
compile_native_test_harness hotkey "$replica_root/Sources/Pasto/GlobalHotKey.swift" \
  "$replica_root/Tests/HotKey/HotKeyHarness.swift"
run_native_test_harness "$@"
