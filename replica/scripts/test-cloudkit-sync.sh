#!/bin/bash
set -euo pipefail
replica_root="$(cd "$(dirname "$0")/.." && pwd)"
test_root="$(mktemp -d "${TMPDIR:-/tmp}/pasto-cloudkit-contract.XXXXXX")"
trap 'rm -rf "$test_root"' EXIT
source "$replica_root/Tests/Native/build-support.sh"
prepare_native_test_core
compile_native_test_harness cloudkit-live-compile "$replica_root/Tests/Native/LiveCloudKitSyncHarness.swift"
compile_native_test_harness cloudkit-contract "$replica_root/Tests/Native/OriginalCloudKitSyncHarness.swift"
"$test_harness"
