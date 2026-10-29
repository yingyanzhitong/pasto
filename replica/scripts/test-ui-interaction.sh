#!/bin/bash
set -euo pipefail
replica_root="$(cd "$(dirname "$0")/.." && pwd)"
test_root="$(mktemp -d "${TMPDIR:-/tmp}/pasto-ui-interaction.XXXXXX")"
trap 'rm -rf "$test_root"' EXIT
source "$replica_root/Tests/Native/build-support.sh"
prepare_native_test_core
compile_native_test_harness ui-interaction \
  "$replica_root/Sources/Pasto/UI/"*.swift \
  "$replica_root/Sources/Pasto/ICloudDriveSyncController.swift" \
  "$replica_root/Sources/Pasto/SourceAppColor.swift" \
  "$replica_root/Sources/Pasto/WindowSharingPolicy.swift" \
  "$replica_root/Sources/Pasto/BackgroundService.swift" \
  "$replica_root/Tests/Native/UIInteractionHarness.swift"
run_native_test_harness "$@" | tee "$test_root/result.log"
python3 - "$test_root/result.log" <<'PY'
import json
import pathlib
import sys
reports = []
for line in pathlib.Path(sys.argv[1]).read_text().splitlines():
    try:
        report = json.loads(line)
    except json.JSONDecodeError:
        continue
    if isinstance(report, dict):
        reports.append(report)
if not reports or reports[-1].get('passed') is not True:
    raise SystemExit('UI harness did not reach its final passing report')
PY
