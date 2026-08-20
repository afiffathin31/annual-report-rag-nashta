"""Test that strategic opportunity clustering and multi-evidence synthesis work cleanly without financial noise."""

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.evidence_engine import evidence_engine
from backend.scoring_engine import scoring_engine

class StrategicRecommendationTests(unittest.TestCase):
    def setUp(self):
        evidence_engine.clear_cache()
        scoring_engine.clear_cache()

    def test_strategic_recommendations_structure(self):
        target_codes = ["BRIS", "BTPS", "BANK", "KAEF", "SIDO"]
        noise_words = ["idaaa", "idbbb", "counterparty credit", "gagal bayar counterparty"]

        for code in target_codes:
            analysis = scoring_engine.analyze_issuer(code)
            recs = analysis.get("strategic_recommendations", [])
            self.assertGreater(len(recs), 0, f"No strategic recommendations generated for {code}")

            print(f"\n=========================================================================")
            print(f"EMITEN: {code} | Total Strategic Recommendations: {len(recs)}")
            print("=========================================================================")

            for r_idx, r in enumerate(recs, 1):
                self.assertIn("problem_synthesis", r)
                self.assertIn("nashta_opportunity", r)
                self.assertIn("supporting_citations", r)
                self.assertGreater(len(r["supporting_citations"]), 0)

                print(f"\n[{r_idx}] {r['title']} ({r['severity']} Priority)")
                print(f"    * Pilar        : {r['pillar_name']}")
                print(f"    * Diagnosa     : {r['problem_synthesis']}")
                print(f"    * Solusi Nashta: {r['nashta_opportunity']}")
                print(f"    * Total Bukti  : {len(r['supporting_citations'])} Sitasi")

                for c_idx, cit in enumerate(r["supporting_citations"], 1):
                    quote = cit["evidence_quote"].lower()
                    for nw in noise_words:
                        self.assertNotIn(nw, quote, f"Found noise term '{nw}' in quote: {quote}")
                    print(f"       ({c_idx}) {cit['page_display']} [{cit['chapter_title']}]")
                    print(f"           \"{cit['evidence_quote'][:120]}...\"")

if __name__ == "__main__":
    unittest.main()
