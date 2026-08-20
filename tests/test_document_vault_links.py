"""Test that all document URLs in emiten_database.json return 200 OK and stream valid PDFs."""

import json
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

class DocumentVaultLinkTests(unittest.TestCase):
    def setUp(self):
        db_path = Path(__file__).resolve().parent.parent / "data" / "emiten_database.json"
        with open(db_path, "r", encoding="utf-8") as f:
            self.db = json.load(f)

    def test_all_issuers_document_vault_links(self):
        target_codes = ["BRIS", "BTPS", "BANK", "PNBS", "KAEF", "SIDO", "IRRA", "OMED"]
        for issuer in self.db.get("issuers", []):
            code = issuer["code"]
            if code not in target_codes:
                continue
            
            reports = issuer.get("reports", [])
            self.assertGreater(len(reports), 0, f"No reports found for {code}")
            
            print(f"\nVerifying Document Vault for [{code}] ({len(reports)} reports):")
            for r in reports:
                year = r["year"]
                url = r["url"]
                # Must be local /api/documents/{code}/{year}
                self.assertTrue(url.startswith("/api/documents/"), f"Invalid local URL format for {code} {year}: {url}")
                
                resp = client.get(url)
                print(f"  * Year {year} -> {url} -> Status: {resp.status_code} ({len(resp.content)/(1024*1024):.2f} MB)")
                self.assertEqual(resp.status_code, 200, f"Failed to access PDF for {code} {year} at {url}")
                self.assertEqual(resp.headers.get("content-type"), "application/pdf")
                self.assertGreater(len(resp.content), 1000, f"PDF file empty for {code} {year}")

    def test_list_local_documents_api(self):
        for code in ["BRIS", "BTPS", "BANK", "KAEF"]:
            resp = client.get(f"/api/documents/{code}")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("documents", data)
            self.assertGreater(data["count"], 0)

if __name__ == "__main__":
    unittest.main()
