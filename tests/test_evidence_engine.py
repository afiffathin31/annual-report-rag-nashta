"""Test evidence engine accuracy and page citations."""

import unittest
from backend.evidence_engine import evidence_engine


class TestEvidenceExtraction(unittest.TestCase):
    def test_bank_and_btps_real_extractions(self):
        for code in ["BANK", "BTPS", "BRIS", "SILO", "KLBF"]:
            weaknesses = evidence_engine.discover_weaknesses(code)
            self.assertGreater(len(weaknesses), 0, f"{code} should have findings")
            for w in weaknesses:
                self.assertIn("evidence_quote", w)
                self.assertIn("page_number", w)
                self.assertIn("context_window", w)
                self.assertIn("pillar_name", w)
                self.assertIn("doc_name", w)
                self.assertGreater(len(w["evidence_quote"]), 20)
                self.assertGreater(len(w["context_window"]), 40)


if __name__ == "__main__":
    unittest.main()
