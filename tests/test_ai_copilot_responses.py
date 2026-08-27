"""Tests to verify AI Copilot accurately and contextually answers diverse user queries."""

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.rag_engine import rag_engine

class AICopilotResponseTests(unittest.TestCase):

    def test_greeting_small_talk(self):
        res = rag_engine.process_chat("hai", active_emiten="BRIS")
        self.assertIn("reply", res)
        self.assertIn("Halo!", res["reply"])
        self.assertIn("AI Business Copilot Nashta", res["reply"])
        self.assertEqual(len(res["citations"]), 0)

    def test_pillar_inquiry_cyber_security(self):
        res = rag_engine.process_chat("Jelaskan tentang Cyber Security di BRIS", active_emiten="BRIS")
        self.assertIn("reply", res)
        self.assertIn("Cyber Security", res["reply"])
        self.assertIn("Metrik Kesiapan", res["reply"])

    def test_pillar_inquiry_cloud(self):
        res = rag_engine.process_chat("Bagaimana layanan Cloud untuk BTPS?", active_emiten="BTPS")
        self.assertIn("reply", res)
        self.assertIn("Cloud Services", res["reply"])

    def test_finding_solution_inquiry(self):
        query = 'Bagaimana Nashta dapat menawarkan solusi untuk mengatasi temuan di Halaman 213: "Penguatan arsitektur inti perbankan"?'
        res = rag_engine.process_chat(query, active_emiten="BANK")
        self.assertIn("reply", res)
        self.assertIn("Rekomendasi Solusi & Action Plan", res["reply"])
        self.assertIn("Tahap 1", res["reply"])

    def test_tech_stack_inquiry(self):
        res = rag_engine.process_chat("Apa tech stack dan teknologi yang digunakan oleh Bank Aladin?", active_emiten="BANK")
        self.assertIn("reply", res)
        self.assertIn("Infrastruktur & Stack Teknologi", res["reply"])

    def test_proposal_inquiry(self):
        res = rag_engine.process_chat("Tolong buatkan proposal penawaran untuk Kimia Farma", active_emiten="KAEF")
        self.assertIn("proposal_markdown", res)
        self.assertIn("EXECUTIVE PROPOSAL", res["proposal_markdown"])

    def test_general_rag_question(self):
        res = rag_engine.process_chat("Bagaimana strategi digitalisasi dan transformasi BRIS?", active_emiten="BRIS")
        self.assertIn("reply", res)
        self.assertIn("Temuan Fakta", res["reply"])

    def test_mistral_provider_configuration(self):
        import os
        from backend.llm_provider import llm_provider
        os.environ["MISTRAL_API_KEY"] = "test_mistral_key_123"
        os.environ["MISTRAL_MODEL"] = "ministral-8b-latest"
        info = llm_provider.get_active_provider_info()
        self.assertEqual(info["provider"], "mistral")
        self.assertEqual(info["model"], "ministral-8b-latest")
        self.assertTrue(info["has_key"])
        del os.environ["MISTRAL_API_KEY"]

if __name__ == "__main__":
    unittest.main()
