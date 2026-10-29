#!/bin/bash
set -euo pipefail
replica_root="$(cd "$(dirname "$0")/.." && pwd)"
test_root="$(mktemp -d "${TMPDIR:-/tmp}/pasto-drive-controller.XXXXXX")"
trap 'rm -rf "$test_root"' EXIT
source "$replica_root/Tests/Native/build-support.sh"
prepare_native_test_core
compile_native_test_harness drive-controller \
  "$replica_root/Sources/Pasto/ICloudDriveSyncController.swift" \
  "$replica_root/Tests/Native/ICloudDriveControllerHarness.swift"
run_native_test_harness "$@"
