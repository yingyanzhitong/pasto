#!/bin/bash
set -euo pipefail
replica_root="$(cd "$(dirname "$0")/.." && pwd)"
binary_root="$(swift build --package-path "$replica_root" -c release --show-bin-path)"
test_root="$(mktemp -d "${TMPDIR:-/tmp}/paste-ui-interaction.XXXXXX")"
trap 'rm -rf "$test_root"' EXIT
xcrun swiftc -parse-as-library -swift-version 5 -I "$binary_root/Modules" \
  "$replica_root/Sources/Pasto/UI/"*.swift \
  "$replica_root/Sources/Pasto/SourceAppColor.swift" \
  "$replica_root/Sources/Pasto/WindowSharingPolicy.swift" \
  "$replica_root/Sources/Pasto/BackgroundService.swift" \
  "$replica_root/Tests/Native/UIInteractionHarness.swift" \
  "$binary_root/PastoCore.build/"*.o -o "$test_root/test-ui-interaction"
"$test_root/test-ui-interaction"
