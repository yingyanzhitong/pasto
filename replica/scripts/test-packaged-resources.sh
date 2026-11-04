#!/bin/bash
set -euo pipefail
replica_root="$(cd "$(dirname "$0")/.." && pwd)"
test_root="$(mktemp -d "${TMPDIR:-/tmp}/pasto-packaged-resources.XXXXXX")"
hidden_resources=""
restore_resources() {
  if [[ -n "$hidden_resources" && -d "$hidden_resources" ]]; then
    mv "$hidden_resources" "$binary_root/Pasto_PastoCore.bundle"
  fi
  rm -rf "$test_root"
}
trap restore_resources EXIT
source "$replica_root/Tests/Native/build-support.sh"
prepare_native_test_core
compile_native_test_harness packaged-resources "$replica_root/Tests/Native/PackagedResourcesHarness.swift"
# The app contains the shipped Contents/Resources layout. Hide only this test
# build's fallback so the check behaves like an installation on another Mac.
hidden_resources="$test_root/build-resources.bundle"
mv "$binary_root/Pasto_PastoCore.bundle" "$hidden_resources"
run_native_test_harness
test_app="$(dirname "$(dirname "$(dirname "$test_harness")")")"
mv "$test_app/Contents/Resources/Pasto_PastoCore.bundle" "$test_app/Pasto_PastoCore.bundle"
run_native_test_harness
