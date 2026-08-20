"""Test live server endpoints for 8 target issuers."""

import json
import urllib.request
import unittest


class TestLiveAPIServer(unittest.TestCase):
    def test_live_8_issuers_endpoint(self):
        port = 8000
        try:
            url = f"http://127.0.0.1:{port}/api/issuers"
            req = urllib.request.urlopen(url)
        except Exception:
            port = 8001
            url = f"http://127.0.0.1:{port}/api/issuers"
            req = urllib.request.urlopen(url)

        self.assertEqual(req.status, 200)
        data = json.loads(req.read().decode("utf-8"))
        issuers = data.get("issuers", [])
        self.assertEqual(len(issuers), 8)
        codes = [i["code"] for i in issuers]
        expected_8 = ["BRIS", "BTPS", "BANK", "PNBS", "KAEF", "SIDO", "IRRA", "OMED"]
        for code in expected_8:
            self.assertIn(code, codes)

    def test_live_target_details(self):
        port = 8000
        for code in ["BRIS", "BANK", "BTPS", "PNBS", "KAEF", "SIDO", "IRRA", "OMED"]:
            try:
                url = f"http://127.0.0.1:{port}/api/issuers/{code}"
                req = urllib.request.urlopen(url)
            except Exception:
                url = f"http://127.0.0.1:8001/api/issuers/{code}"
                req = urllib.request.urlopen(url)

            self.assertEqual(req.status, 200)
            data = json.loads(req.read().decode("utf-8"))
            self.assertEqual(data["issuer"]["code"], code)
            self.assertEqual(len(data["pillar_scores"]), 10)
            self.assertGreater(len(data["verified_weaknesses"]), 0)


if __name__ == "__main__":
    unittest.main()
