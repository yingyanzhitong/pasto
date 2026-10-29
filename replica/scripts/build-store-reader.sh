#!/bin/bash
set -euo pipefail
replica_root="$(cd "$(dirname "$0")/.." && pwd)"
test_root="$1"
mkdir -p "$test_root"
source "$replica_root/Tests/Native/build-support.sh"
prepare_native_test_core
compile_native_test_harness store-reader "$replica_root/Tests/Native/StoreReadHarness.swift"
