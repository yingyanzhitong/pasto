#!/bin/bash
set -euo pipefail
if [[ "$#" -lt 2 || "$#" -gt 3 || "${1:-}" != *.app || "${2:-}" != *.dmg ]]; then
  printf '%s\n' '用法：build-dmg.sh <已构建的 Pasto.app> <目标.dmg> [arm64|x86_64|universal]' >&2
  exit 1
fi
expected_architecture="${3:-auto}"
case "$expected_architecture" in auto|arm64|x86_64|universal) ;; *) printf '%s\n' '目标架构必须为 arm64、x86_64 或 universal。' >&2; exit 1 ;; esac
app="$(cd "$1" && pwd)"
mkdir -p "$(dirname "$2")"
output="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"
if [[ -e "$output" || -L "$output" ]]; then
  printf '%s\n' "目标已存在，拒绝覆盖：$output" >&2
  exit 1
fi
work="$(mktemp -d "$(dirname "$output")/.pasto-dmg.XXXXXX")"
stage="$work/stage"
mount="$work/mount"
attached=0
cleanup() {
  result=$?
  if [[ "$attached" == 1 ]]; then
    if ! hdiutil detach "$mount" >/dev/null 2>&1; then
      printf '%s\n' "无法卸载临时卷，请检查：$mount" >&2
      exit 1
    fi
  fi
  rm -rf "$work"
  exit "$result"
}
trap cleanup EXIT
mkdir "$stage" "$mount"
codesign --verify --deep --strict "$app"
ditto "$app" "$stage/Pasto.app"
ln -s /Applications "$stage/Applications"
hdiutil create -srcfolder "$stage" -volname Pasto -fs HFS+ -format UDZO "$work/Pasto.dmg"
hdiutil verify "$work/Pasto.dmg"
attached=1
hdiutil attach "$work/Pasto.dmg" -readonly -nobrowse -mountpoint "$mount" -plist > "$work/attach.plist"
codesign --verify --deep --strict "$mount/Pasto.app"
python3 - "$app" "$mount" "$work/attach.plist" "$expected_architecture" <<'PY'
from pathlib import Path
import hashlib
import os
import plistlib
import stat
import subprocess
import sys

source, mounted, attachment = map(Path, sys.argv[1:4])
expected = sys.argv[4]
app = mounted / "Pasto.app"
if not (mounted / "Applications").is_symlink() or os.readlink(mounted / "Applications") != "/Applications":
    raise ValueError("Applications 快捷链接目标错误")
entities = plistlib.loads(attachment.read_bytes())["system-entities"]
if not any(entity.get("mount-point") == str(mounted) for entity in entities):
    raise ValueError("挂载记录与临时挂载点不一致")

def tree(root):
    rows = []
    for directory, directories, files in os.walk(root, followlinks=False):
        for name in directories + files:
            path = Path(directory) / name
            mode = stat.S_IMODE(path.lstat().st_mode)
            value = (os.readlink(path) if path.is_symlink() else
                     hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None)
            kind = "symlink" if path.is_symlink() else "file" if path.is_file() else "directory"
            rows.append((path.relative_to(root).as_posix(), kind, mode, value))
    return sorted(rows)

if tree(source) != tree(app):
    raise ValueError("DMG 内应用的文件内容、权限或符号链接发生改变")
info = plistlib.loads((app / "Contents/Info.plist").read_bytes())
source_info = plistlib.loads((source / "Contents/Info.plist").read_bytes())
if info != source_info or info.get("CFBundleExecutable") != "Pasto" or info.get("CFBundleDisplayName") != "Pasto":
    raise ValueError("DMG 内应用元数据不匹配")
allowed = {frozenset(["arm64"]), frozenset(["x86_64"]), frozenset(["arm64", "x86_64"])}
expected_set = frozenset(["arm64", "x86_64"] if expected == "universal" else [expected])
common_architectures = None
for relative in ["Contents/MacOS/Pasto", "Contents/MacOS/pasto-mcp",
                 "Contents/Library/LoginItems/Pasto Helper.app/Contents/MacOS/PastoHelper"]:
    executable = app / relative
    architectures = subprocess.run(["lipo", "-archs", str(executable)],
                                   check=True, capture_output=True, text=True).stdout.split()
    actual = frozenset(architectures)
    if len(actual) != len(architectures) or actual not in allowed:
        raise ValueError("可执行文件包含不支持或重复的架构")
    if expected != "auto" and actual != expected_set:
        raise ValueError("可执行文件架构与指定目标不一致")
    if common_architectures is not None and actual != common_architectures:
        raise ValueError("三个可执行文件必须具有完全相同的架构")
    common_architectures = actual
    for architecture in architectures:
        subprocess.run(["codesign", "--verify", "--strict", "--architecture", architecture,
                        str(executable)], check=True)
print("DMG 应用内容、架构、签名与 Applications 快捷链接校验通过：" + ", ".join(sorted(common_architectures)))
PY
hdiutil detach "$mount"
attached=0
# Same-filesystem exclusive link prevents a concurrent writer being overwritten.
python3 - "$work/Pasto.dmg" "$output" <<'PY'
import os
import sys
os.link(sys.argv[1], sys.argv[2])
PY
printf '%s\n' "$output"
