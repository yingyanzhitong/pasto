#!/bin/bash
set -euo pipefail
replica_root="$(cd "$(dirname "$0")/.." && pwd)"
configuration="${1:-release}"
version="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$replica_root/../package.json")"
if [[ ! "$version" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)(-dev\.([0-9]+))?$ ]]; then
  printf '%s\n' 'package.json version 必须为 major.minor.patch 或 major.minor.patch-dev.N。' >&2
  exit 1
fi
short_version="${BASH_REMATCH[1]}.${BASH_REMATCH[2]}.${BASH_REMATCH[3]}"
build_version="$short_version"
if [[ -n "${BASH_REMATCH[5]}" ]]; then
  build_version="${BASH_REMATCH[1]}.${BASH_REMATCH[2]}.${BASH_REMATCH[5]}"
fi
swift build --package-path "$replica_root" -c "$configuration" --jobs 2
binary_root="$(swift build --package-path "$replica_root" -c "$configuration" --show-bin-path)"
mkdir -p "$replica_root/dist"
staging="$(mktemp -d "$replica_root/dist/.pasto-build.XXXXXX")"
trap 'rm -rf "$staging"' EXIT
bundle="$staging/Pasto.app"
mkdir -p "$bundle/Contents/MacOS" "$bundle/Contents/Resources"
cp "$binary_root/Pasto" "$bundle/Contents/MacOS/Pasto"
cp "$binary_root/pasto-mcp" "$bundle/Contents/MacOS/pasto-mcp"
cp "$replica_root/Assets/Pasto.icns" "$bundle/Contents/Resources/Pasto.icns"
ditto "$binary_root/Pasto_PastoCore.bundle" "$bundle/Contents/Resources/Pasto_PastoCore.bundle"
helper="$bundle/Contents/Library/LoginItems/Pasto Helper.app"
mkdir -p "$helper/Contents/MacOS"
cp "$binary_root/PastoHelper" "$helper/Contents/MacOS/PastoHelper"
cat > "$helper/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>com.yingyanzhitong.paste-replica.helper</string>
<key>CFBundleName</key><string>Pasto Helper</string>
<key>CFBundleExecutable</key><string>PastoHelper</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleShortVersionString</key><string>$short_version</string>
<key>CFBundleVersion</key><string>$build_version</string>
<key>PastoSourceVersion</key><string>$version</string>
<key>LSMinimumSystemVersion</key><string>14.0</string>
<key>LSUIElement</key><true/>
<key>NSPrincipalClass</key><string>NSApplication</string>
</dict></plist>
PLIST
plutil -lint "$helper/Contents/Info.plist"
codesign --force --sign - "$helper"
cat > "$bundle/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>com.yingyanzhitong.paste-replica</string>
<key>CFBundleName</key><string>Pasto</string>
<key>CFBundleDisplayName</key><string>Pasto</string>
<key>CFBundleIconFile</key><string>Pasto</string>
<key>CFBundleExecutable</key><string>Pasto</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleShortVersionString</key><string>$short_version</string>
<key>CFBundleVersion</key><string>$build_version</string>
<key>PastoSourceVersion</key><string>$version</string>
<key>LSMinimumSystemVersion</key><string>14.0</string>
<key>LSUIElement</key><true/>
<key>NSHighResolutionCapable</key><true/>
<key>NSPrincipalClass</key><string>NSApplication</string>
</dict></plist>
PLIST
plutil -lint "$bundle/Contents/Info.plist"
codesign --force --sign - "$bundle"
codesign --verify --deep --strict "$bundle"
if [[ -e "$replica_root/dist/Pasto.app" ]]; then
  backup="$replica_root/../.local/app-bundle-backups/$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$backup"
  mv "$replica_root/dist/Pasto.app" "$backup/Pasto.app"
fi
mv "$bundle" "$replica_root/dist/Pasto.app"
printf '%s\n' "$replica_root/dist/Pasto.app"
