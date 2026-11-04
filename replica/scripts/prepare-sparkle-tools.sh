#!/bin/bash
set -euo pipefail
replica_root="$(cd "$(dirname "$0")/.." && pwd)"
tools="$replica_root/.build/sparkle-tools/2.10.1"
if [[ ! -x "$tools/bin/sign_update" ]]; then
  mkdir -p "$replica_root/.build/sparkle-tools"
  temporary="$(mktemp -d "$replica_root/.build/sparkle-tools/.download.XXXXXX")"
  trap 'rm -rf "$temporary"' EXIT
  curl --fail --location --silent --show-error --proto '=https' --proto-redir '=https' \
    'https://github.com/sparkle-project/Sparkle/releases/download/2.10.1/Sparkle-2.10.1.tar.xz' \
    -o "$temporary/sparkle.tar.xz"
  printf '%s  %s\n' '1a856d2a9edb8e628de88121d7be04cf0e2167f8641650b78fca00b14244cf27' \
    "$temporary/sparkle.tar.xz" | shasum -a 256 --check >&2
  tar -xf "$temporary/sparkle.tar.xz" -C "$temporary" bin/sign_update
  mkdir -p "$tools/bin"
  mv "$temporary/bin/sign_update" "$tools/bin/sign_update"
fi
printf '%s\n' "$tools/bin/sign_update"
