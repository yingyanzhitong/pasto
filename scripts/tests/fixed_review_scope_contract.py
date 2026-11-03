"""Validate this review's exact delta before reusing a historical source snapshot.

Current behavior is checked separately. Historical hashes cannot establish the
new contract, and this helper never changes any production file.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / '.local/p0-p1-fixed-review/2026-11-02'


def before_fixed_review_bytes(path):
    path = Path(path)
    relative = path.relative_to(ROOT).as_posix()
    manifest = json.loads((DIRECTORY / 'source-delta.json').read_text())
    data = path.read_bytes()
    change = manifest.get(relative)
    if change is None:
        return data
    assert hashlib.sha256(data).hexdigest() == change['after_sha256'], relative
    before = (DIRECTORY / 'before' / relative).read_bytes()
    assert hashlib.sha256(before).hexdigest() == change['before_sha256'], relative
    # The recorded complete textual diff is independently checked by the new
    # fixed-worklist tests, rather than dropping arbitrary changed methods.
    return before
