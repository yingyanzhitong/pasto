"""Guard fast source-review reuse against stale or incomplete provenance."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("migration_completeness_audit", SCRIPTS / "migration_completeness_audit.py")
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class UnchangedSourceReviewTests(unittest.TestCase):
    def setUp(self):
        self.entry = {"state": "migrated", "contract": "returns message"}
        self.evidence = {"contract": "returns message", "source_review": "getter and production caller reviewed",
                         "original_pseudocode_sha256": "original", "original_binary_sha256": "binary",
                         "source_sha256": {"leaf.swift": "leaf", "caller.swift": "caller"}}
        self.refs = [{"path": "leaf.swift", "present": True}]
        self.current = {"leaf.swift": "leaf", "caller.swift": "caller"}

    def reusable(self, **kwargs):
        args = dict(entry=self.entry, evidence=self.evidence, references=self.refs,
                    original_sha256="original", binary_sha256="binary", digest=self.current.get)
        args.update(kwargs)
        return audit.unchanged_source_review(**args)

    def test_unchanged_bound_review_is_reusable_without_compiled_product(self):
        before = copy.deepcopy(self.entry)
        self.assertTrue(self.reusable())
        self.assertEqual(before, self.entry, "Checking reuse must never upgrade migration states")

    def test_changed_caller_invalidates_even_when_implementation_is_unchanged(self):
        self.current["caller.swift"] = "changed"
        self.assertFalse(self.reusable())

    def test_changed_or_missing_original_inputs_invalidate(self):
        for arguments in [{"original_sha256": "changed"}, {"original_sha256": None},
                          {"binary_sha256": "other"}, {"binary_sha256": None}]:
            with self.subTest(arguments=arguments): self.assertFalse(self.reusable(**arguments))

    def test_missing_reference_hash_or_missing_symbol_invalidates(self):
        self.refs[0]["present"] = False
        self.assertFalse(self.reusable())
        self.refs[0]["present"] = True
        del self.evidence["source_sha256"]["leaf.swift"]
        self.assertFalse(self.reusable())

    def test_missing_file_or_empty_digest_never_counts_as_equal(self):
        del self.current["caller.swift"]
        self.assertFalse(self.reusable())
        self.evidence["source_sha256"]["caller.swift"] = None
        self.assertFalse(self.reusable())

    def test_new_or_missing_contract_requires_review(self):
        self.entry["contract"] = "different behavior"
        self.assertFalse(self.reusable())
        self.entry["contract"] = self.evidence["contract"] = ""
        self.assertFalse(self.reusable())

    def test_source_existence_or_partial_state_alone_is_not_a_prior_review(self):
        self.assertFalse(self.reusable(references=[]))
        self.entry["state"] = "partial"
        self.assertFalse(self.reusable())
        self.entry["state"] = "migrated"
        del self.evidence["source_review"]
        self.assertFalse(self.reusable())


if __name__ == "__main__":
    unittest.main()
