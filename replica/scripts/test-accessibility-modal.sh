#!/bin/bash
set -euo pipefail
replica_root="$(cd "$(dirname "$0")/.." && pwd)"
test_root="$(mktemp -d "${TMPDIR:-/tmp}/pasto-accessibility-modal.XXXXXX")"
trap 'rm -rf "$test_root"' EXIT
source "$replica_root/Tests/Native/build-support.sh"
prepare_native_test_core
compile_native_test_harness accessibility-modal \
  "$replica_root/Sources/Pasto/UI/OriginalAccessibilityModals.swift" \
  "$replica_root/Sources/Pasto/UI/OriginalAccessibilityRequestAction.swift" \
  "$replica_root/Sources/Pasto/UI/ReplicaBrand.swift" \
  "$replica_root/Tests/Native/AccessibilityModalHarness.swift"
if [[ $# -gt 0 ]]; then
  result=0
  "$test_harness" -AppleLanguages '(zh-Hans)' -AppleLocale zh_CN > "$1" || result=$?
  cat "$1"
  exit "$result"
fi
"$test_harness" -AppleLanguages '(zh-Hans)' -AppleLocale zh_CN
