#!/bin/bash
set -euo pipefail
replica_root="$(cd "$(dirname "$0")/.." && pwd)"
repository_root="$(cd "$replica_root/.." && pwd)"
report_root="${1:-$repository_root/.local/replica-validation}"
python3 "$repository_root/scripts/function_ledger.py" --require-migration-complete
mkdir -p "$report_root"
bash "$replica_root/scripts/build-app.sh" > "$report_root/build.log" 2>&1
original_binary="${PASTE_ORIGINAL_BINARY:-/Applications/Paste.app/Contents/MacOS/Paste}"
if [[ -f "$original_binary" ]]; then
  python3 "$replica_root/scripts/test-original-functions.py" --original "$original_binary" > "$report_root/original-functions.json"
else
  printf '%s\n' '{"skipped":true,"reason":"Original Paste binary unavailable; saved source-bound comparison reports are checked by the ledger"}' > "$report_root/original-functions.json"
fi
"$replica_root/.build/release/pasto-core-tests" > "$report_root/core.json"
python3 "$repository_root/scripts/function_ledger.py" --record-contracts "$report_root/core.json" > "$report_root/function-ledger.json"
python3 -m unittest discover -s "$repository_root/scripts/tests" > "$report_root/function-ledger-tests.log" 2>&1
bash "$replica_root/scripts/test-hotkey.sh" "$report_root/hotkey.json"
bash "$replica_root/scripts/test-shortcut-model.sh" "$report_root/shortcut-model.json"
bash "$replica_root/scripts/test-window-policy.sh" > "$report_root/window-policy.json"
bash "$replica_root/scripts/test-ui-interaction.sh" > "$report_root/ui-interaction.json"
python3 "$replica_root/scripts/test-helper-lifecycle.py" --report "$report_root/helper-lifecycle.json"
python3 "$replica_root/scripts/test-app-monitor.py" --report "$report_root/app-monitor.json"
python3 "$repository_root/scripts/verify.py" > "$report_root/research.json"
printf '验证报告：%s\n' "$report_root"
