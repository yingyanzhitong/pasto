#!/bin/bash
# Run local product regression even while address-by-address migration is incomplete.
set -euo pipefail
replica_root="$(cd "$(dirname "$0")/.." && pwd)"
repository_root="$(cd "$replica_root/.." && pwd)"
report_root="${1:-$repository_root/.local/local-regression-$(date +%Y%m%d-%H%M%S)}"
mkdir -p "$report_root"
python3 - "$repository_root" "$report_root" <<'PY'
import datetime
import hashlib
import json
import pathlib
import os
import signal
import subprocess
import sys
import time

root = pathlib.Path(sys.argv[1])
reports = pathlib.Path(sys.argv[2]).resolve()
replica = root / 'replica'
app = replica / 'dist/Pasto.app'
results = []

def run(name, command, timeout=180):
    started = time.monotonic()
    log_path = reports / (name + '.log')
    with log_path.open('wb') as log:
        try:
            process = subprocess.Popen(command, cwd=root, stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            try:
                code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                # Python fixture harnesses catch SIGTERM and clean their owned apps.
                for sig, grace in [(signal.SIGTERM, 10), (signal.SIGKILL, 5)]:
                    try:
                        os.killpg(process.pid, sig)
                    except ProcessLookupError:
                        break
                    try:
                        process.wait(timeout=grace)
                    except subprocess.TimeoutExpired:
                        pass
                code = 124
        except OSError as error:
            log.write(str(error).encode())
            code = 127
    result = {'name': name, 'passed': code == 0, 'exit_code': code,
              'duration_seconds': round(time.monotonic() - started, 3), 'log': log_path.name}
    results.append(result)
    print(f'{name}: ' + ('PASS' if code == 0 else f'FAIL ({code})'), flush=True)
    return code

if run('build', ['bash', str(replica / 'scripts/build-app.sh')], timeout=300) == 0:
    if run('binary-path', ['swift', 'build', '--package-path', str(replica), '-c',
                           'release', '--show-bin-path'], timeout=30) == 0:
        binary_root = pathlib.Path((reports / 'binary-path.log').read_text().strip())
        suites = [
            ('core', [str(binary_root / 'pasto-core-tests')]),
            ('hotkey', ['bash', str(replica / 'scripts/test-hotkey.sh')]),
            ('shortcut', ['bash', str(replica / 'scripts/test-shortcut-model.sh')]),
            ('window', ['bash', str(replica / 'scripts/test-window-policy.sh')]),
            ('ui', ['bash', str(replica / 'scripts/test-ui-interaction.sh')]),
            ('accessibility-modal', ['bash', str(replica / 'scripts/test-accessibility-modal.sh')]),
            ('paste-group-migration', ['bash', str(replica / 'scripts/test-paste-group-migration.sh')]),
            ('monitor', ['python3', str(replica / 'scripts/test-app-monitor.py'),
                         '--app', str(app), '--report', str(reports / 'monitor.json')]),
            ('helper', ['python3', str(replica / 'scripts/test-helper-lifecycle.py'),
                        '--report', str(reports / 'helper.json')]),
        ]
        for name, command in suites:
            run(name, command)

summary = {
    'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'passed': all(result['passed'] for result in results),
    'app_binary_sha256': (hashlib.sha256((app / 'Contents/MacOS/Pasto').read_bytes()).hexdigest()
                          if results[0]['passed'] else None),
    'suites': results,
    'scope': 'Local regression using isolated fixtures; no MCP, release, or full migration acceptance.',
}
(reports / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
print('Report: ' + str(reports / 'summary.json'))
sys.exit(0 if summary['passed'] else 1)
PY
