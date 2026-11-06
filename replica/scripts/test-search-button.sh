#!/bin/bash
set -euo pipefail
replica_root="$(cd "$(dirname "$0")/.." && pwd)"
test_root="$(mktemp -d "${TMPDIR:-/tmp}/pasto-search-button.XXXXXX")"
trap 'rm -rf "$test_root"' EXIT
source "$replica_root/Tests/Native/build-support.sh"
prepare_native_test_core
sparkle_root="$test_build_root/artifacts/replica/Sparkle/Sparkle.xcframework/macos-arm64_x86_64"
compile_native_test_harness search-button \
  -F "$sparkle_root" -framework Sparkle -Xlinker -rpath -Xlinker "$sparkle_root" \
  "$replica_root/Sources/Pasto/UI/"*.swift \
  "$replica_root/Sources/Pasto/ICloudDriveSyncController.swift" \
  "$replica_root/Sources/Pasto/SourceAppColor.swift" \
  "$replica_root/Sources/Pasto/WindowSharingPolicy.swift" \
  "$replica_root/Sources/Pasto/BackgroundService.swift" \
  "$replica_root/Tests/Native/SearchButtonHarness.swift"
run_native_test_harness "$@" | tee "$test_root/result.log"
python3 - "$test_root/result.log" <<'PY'
import json
import pathlib
import sys
reports = []
for line in pathlib.Path(sys.argv[1]).read_text().splitlines():
    try:
        reports.append(json.loads(line))
    except json.JSONDecodeError:
        continue
if not reports or reports[-1].get('passed') is not True:
    raise SystemExit('Search harness did not reach its final passing report')
PY
