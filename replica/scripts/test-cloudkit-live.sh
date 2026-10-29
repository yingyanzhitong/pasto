#!/bin/bash
set -euo pipefail
replica_root="$(cd "$(dirname "$0")/.." && pwd)"
if [[ "${1:-}" == --preflight ]]; then
  python3 - <<'PY'
import json, re, subprocess
result = subprocess.run(['security', 'find-identity', '-v', '-p', 'codesigning'], capture_output=True, text=True)
match = re.search(r'(\d+) valid identities found', result.stdout)
print(json.dumps({'validSigningIdentities': int(match[1]) if match else None, 'cloudKitNetworkTestRun': False}, ensure_ascii=False))
PY
  exit 0
fi
if [[ "${1:-}" != --synthetic-only ]]; then
  printf '%s\n' '用法：test-cloudkit-live.sh --preflight | --synthetic-only' >&2
  exit 2
fi
: "${PASTO_CLOUDKIT_PROFILE:?真实测试需要 Pasto 自有开发环境描述文件}"
: "${PASTO_CLOUDKIT_CONTAINER:?真实测试需要 Pasto 自有 CloudKit 容器}"
: "${PASTO_SIGNING_IDENTITY:?真实测试需要本机 Apple 签名身份}"
: "${PASTO_CLOUDKIT_TEST_BUNDLE_ID:?真实测试需要与描述文件匹配的测试 Bundle ID}"
test_root="$(mktemp -d "${TMPDIR:-/tmp}/pasto-cloudkit-live.XXXXXX")"
trap 'rm -rf "$test_root"' EXIT
source "$replica_root/Tests/Native/build-support.sh"
prepare_native_test_core
compile_native_test_harness cloudkit-live "$replica_root/Tests/Native/LiveCloudKitSyncHarness.swift"
test_bundle="$(dirname "$(dirname "$(dirname "$test_harness")")")"
python3 - "$test_bundle/Contents/Info.plist" "$PASTO_CLOUDKIT_TEST_BUNDLE_ID" <<'PY'
import plistlib, sys
from pathlib import Path
path = Path(sys.argv[1]); info = plistlib.loads(path.read_bytes())
info['CFBundleIdentifier'] = sys.argv[2]
path.write_bytes(plistlib.dumps(info))
PY
python3 "$replica_root/scripts/configure-cloudkit-signing.py" \
  --profile "$PASTO_CLOUDKIT_PROFILE" --bundle "$test_bundle" --container "$PASTO_CLOUDKIT_CONTAINER" \
  --environment Development --output "$test_root/entitlements.plist"
codesign --force --sign "$PASTO_SIGNING_IDENTITY" --entitlements "$test_root/entitlements.plist" "$test_bundle"
codesign --verify --strict "$test_bundle"
PASTO_CLOUDKIT_ALLOW_LIVE_TEST=1 "$test_harness"
