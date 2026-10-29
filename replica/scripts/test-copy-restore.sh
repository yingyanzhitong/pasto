#!/bin/bash
set -euo pipefail
replica_root="$(cd "$(dirname "$0")/.." && pwd)"
test_root="$(mktemp -d "${TMPDIR:-/tmp}/pasto-copy-restore.XXXXXX")"
trap 'rm -rf "$test_root"' EXIT
export PASTO_TEST_CONFIGURATION=release
export PASTO_TEST_SCRATCH_PATH="${PASTO_TEST_SCRATCH_PATH:-$replica_root/.build/copy-restore-regression}"
source "$replica_root/Tests/Native/build-support.sh"
prepare_native_test_core
compile_native_test_harness copy-restore \
  "$replica_root/Sources/Pasto/UI/"*.swift \
  "$replica_root/Sources/Pasto/ICloudDriveSyncController.swift" \
  "$replica_root/Sources/Pasto/SourceAppColor.swift" \
  "$replica_root/Sources/Pasto/WindowSharingPolicy.swift" \
  "$replica_root/Sources/Pasto/BackgroundService.swift" \
  "$replica_root/Tests/Native/CopyRestoreHarness.swift"
run_native_test_harness "$@"
