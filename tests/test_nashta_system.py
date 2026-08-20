"""Unit and integration tests for True RAG Nashta 10-Pillars Opportunity Intelligence System."""

import unittest
from backend.catalog import catalog_manager
from backend.rag_indexer import rag_indexer
from backend.evidence_engine import evidence_engine
from backend.scoring_engine import scoring_engine
from backend.rag_engine import rag_engine


class TestNashtaTrueRAGSystem(unittest.TestCase):
    def test_pillars_taxonomy(self):
        pillars = catalog_manager.get_pillars()
        self.assertEqual(len(pillars), 10, "Should contain exactly 10 Nashta pillars")

    def test_rag_indexer_chunks(self):
        chunks = rag_indexer.get_chunks_for_emiten("BRIS")
        self.assertGreaterEqual(len(chunks), 3, "BRIS should have indexed paragraph chunks")
        c = chunks[0]
        self.assertIn("page_number", c)
        self.assertIn("raw_paragraph", c)
        self.assertIn("chapter_title", c)
        self.assertIn("doc_name", c)
        self.assertGreater(len(c["raw_paragraph"]), 50)

    def test_evidence_engine_extraction(self):
        weaknesses = evidence_engine.discover_weaknesses("BRIS")
        self.assertGreaterEqual(len(weaknesses), 2, "BRIS should have extracted weakness citations")
        for w in weaknesses:
            self.assertIn("evidence_quote", w)
            self.assertIn("context_window", w)
            self.assertIn("page_number", w)
            self.assertIn("doc_name", w)
            self.assertIn("match_confidence", w)
            self.assertGreaterEqual(w["match_confidence"], 80)
            # Verify exact quote is contained in the context window
            self.assertIn(w["evidence_quote"], w["context_window"])

    def test_scoring_engine_analysis(self):
        bris_analysis = scoring_engine.analyze_issuer("BRIS")
        self.assertIn("overall_opportunity_score", bris_analysis)
        self.assertEqual(len(bris_analysis["pillar_scores"]), 10)
        self.assertGreater(len(bris_analysis["verified_weaknesses"]), 0)

    def test_rag_engine_chat(self):
        chat_res = rag_engine.process_chat("apa kelemahan operasional BRIS?", active_emiten="BRIS")
        self.assertIn("reply", chat_res)
        self.assertIn("citations", chat_res)
        self.assertGreaterEqual(len(chat_res["citations"]), 1)
        self.assertIn("context", chat_res["citations"][0])

    def test_proposal_generation(self):
        proposal_res = rag_engine.generate_proposal("BRIS")
        self.assertIn("proposal_markdown", proposal_res)
        self.assertTrue("Hal." in proposal_res["proposal_markdown"] or "Halaman" in proposal_res["proposal_markdown"])


if __name__ == "__main__":
    unittest.main()
