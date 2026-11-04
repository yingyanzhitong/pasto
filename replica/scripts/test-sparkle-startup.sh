#!/bin/bash
set -euo pipefail
replica_root="$(cd "$(dirname "$0")/.." && pwd)"
test_root="$(mktemp -d "${TMPDIR:-/tmp}/pasto-sparkle-startup.XXXXXX")"
trap 'rm -rf "$test_root"' EXIT
architecture="${PASTO_TEST_ARCHITECTURE:-$(uname -m)}"
app="$test_root/Startup.app"
binary_root="$(swift build --package-path "$replica_root" --scratch-path "$replica_root/.build/native-regression" -c debug --show-bin-path)"
mkdir -p "$app/Contents/MacOS" "$app/Contents/Frameworks"
ditto "$binary_root/Sparkle.framework" "$app/Contents/Frameworks/Sparkle.framework"
python3 - "$app" "$replica_root" <<'PY'
from pathlib import Path
import plistlib
import sys
import uuid
app, replica = map(Path, sys.argv[1:])
info = {
    'CFBundleIdentifier': 'local.pasto.sparkle-startup.' + str(uuid.uuid4()),
    'CFBundleExecutable': 'harness', 'CFBundleName': 'Pasto Update Startup Test',
    'CFBundleVersion': '1.0.5', 'CFBundleShortVersionString': '1.0.5',
    'CFBundlePackageType': 'APPL', 'LSUIElement': True,
    'SUFeedURL': 'https://github.com/yingyanzhitong/pasto/releases/latest/download/appcast.xml',
    'SUPublicEDKey': (replica / 'Assets/UpdatePublicKey.txt').read_text().strip(),
    'SURequireSignedFeed': True, 'SUVerifyUpdateBeforeExtraction': True,
    'SUEnableAutomaticChecks': False, 'SUAutomaticallyUpdate': False, 'SUSendProfileInfo': False}
(app / 'Contents/Info.plist').write_bytes(plistlib.dumps(info))
PY
xcrun swiftc -parse-as-library -swift-version 5 -target "$architecture-apple-macosx14.0" \
  -F "$binary_root" -framework Sparkle -Xlinker -rpath -Xlinker '@executable_path/../Frameworks' \
  "$replica_root/Sources/Pasto/UI/PastoInAppUpdater.swift" \
  "$replica_root/Tests/Native/SparkleStartupHarness.swift" -o "$app/Contents/MacOS/harness"
codesign --force --sign - "$app" >&2
"$app/Contents/MacOS/harness"
