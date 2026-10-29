#!/bin/bash
# Test-only module linking. Uses an independent scratch directory and an isolated bundle ID.
prepare_native_test_core() {
  test_build_root="${PASTO_TEST_SCRATCH_PATH:-$replica_root/.build/native-regression}"
  test_configuration="${PASTO_TEST_CONFIGURATION:-debug}"
  swift build --package-path "$replica_root" --scratch-path "$test_build_root" \
    -c "$test_configuration" --target PastoCore -j 4 >&2
  binary_root="$(swift build --package-path "$replica_root" --scratch-path "$test_build_root" -c "$test_configuration" --show-bin-path)"
}

compile_native_test_harness() {
  local name="$1"
  shift
  local app="$test_root/$name.app"
  mkdir -p "$app/Contents/MacOS" "$app/Contents/Resources"
  cat > "$app/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict><key>CFBundleIdentifier</key><string>local.pasto.regression.$name.$(uuidgen)</string><key>CFBundleExecutable</key><string>harness</string><key>CFBundleName</key><string>$name</string><key>CFBundlePackageType</key><string>APPL</string><key>LSUIElement</key><true/><key>UIDesignRequiresCompatibility</key><false/></dict></plist>
PLIST
  cp -R "$binary_root/Pasto_PastoCore.bundle" "$app/Contents/Resources/"
  local optimization=-Onone
  if [[ "${PASTO_TEST_CONFIGURATION:-debug}" == release ]]; then optimization=-O; fi
  xcrun swiftc -parse-as-library -swift-version 5 -target "$(uname -m)-apple-macosx14.0" \
    "$optimization" \
    -I "$binary_root/Modules" -I "$binary_root/PastoObjC.build" \
    -Xcc "-fmodule-map-file=$replica_root/Sources/PastoObjC/include/module.modulemap" \
    -Xcc "-I$replica_root/Sources/PastoObjC/include" \
    "$@" "$binary_root/PastoCore.build/"*.o "$binary_root/PastoObjC.build/"*.o \
    -o "$app/Contents/MacOS/harness"
  test_harness="$app/Contents/MacOS/harness"
}

run_native_test_harness() {
  if [[ $# -gt 0 ]]; then
    local result=0
    "$test_harness" > "$1" || result=$?
    cat "$1"
    return "$result"
  fi
  "$test_harness"
}
