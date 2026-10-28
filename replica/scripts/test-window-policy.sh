#!/bin/bash
set -euo pipefail
replica_root="$(cd "$(dirname "$0")/.." && pwd)"
test_root="$(mktemp -d "${TMPDIR:-/tmp}/pasto-window-policy.XXXXXX")"
trap 'rm -rf "$test_root"' EXIT
source "$replica_root/Tests/Native/build-support.sh"
prepare_native_test_core
compile_native_test_harness window-policy \
  "$replica_root/Sources/Pasto/WindowSharingPolicy.swift" \
  "$replica_root/Tests/Native/WindowSharingPolicyHarness.swift"
run_native_test_harness "$@"
