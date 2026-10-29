#!/bin/bash
set -euo pipefail
replica_root="$(cd "$(dirname "$0")/.." && pwd)"
test_root="$(mktemp -d "${TMPDIR:-/tmp}/pasto-icloud-sync.XXXXXX")"
trap 'rm -rf "$test_root"' EXIT
source "$replica_root/Tests/Native/build-support.sh"
prepare_native_test_core
case "${1:-}" in
  '') harness="ICloudDriveSyncHarness.swift" ;;
  --live-icloud) harness="LiveICloudDriveSyncHarness.swift" ;;
  *) printf '%s\n' '用法：test-icloud-sync.sh [--live-icloud]' >&2; exit 2 ;;
esac
compile_native_test_harness icloud-sync "$replica_root/Tests/Native/$harness"
"$test_harness"
