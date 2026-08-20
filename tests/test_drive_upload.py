import json
import tempfile
import unittest
from pathlib import Path

from upload_reports_to_drive import (
    ReportItem,
    allow_tls_fallback,
    download_headers,
    find_child,
    google_drive_download_url,
    load_reports,
)


class _FakeRequest:
    def __init__(self, response):
        self.response = response

    def execute(self):
        return self.response


class _FakeFiles:
    def __init__(self, response):
        self.response = response

    def list(self, **_kwargs):
        return _FakeRequest(self.response)


class _FakeService:
    def __init__(self, response):
        self.response = response

    def files(self):
        return _FakeFiles(self.response)


class DriveUploadTests(unittest.TestCase):
    def test_tls_fallback_is_limited_to_pnbs_official_host(self):
        self.assertTrue(allow_tls_fallback("https://www.pdsb.co.id/about/download_ar/token"))
        self.assertFalse(allow_tls_fallback("https://example.com/file.pdf"))

    def test_only_bris_2025_is_expected_non_pdf(self):
        from upload_reports_to_drive import EXPECTED_NON_PDF

        self.assertEqual(EXPECTED_NON_PDF, {("BRIS", 2025)})

    def test_btps_download_uses_official_referer(self):
        item = ReportItem("BTPS", "BTPN Syariah", 2025, "https://cdn/a.pdf", "x.json")
        self.assertEqual(
            download_headers(item),
            {"Referer": "https://www.btpnsyariah.com/laporan-tahunan"},
        )

    def test_other_issuer_has_no_forced_referer(self):
        item = ReportItem("IRRA", "Itama", 2025, "https://example/a.pdf", "x.json")
        self.assertEqual(download_headers(item), {})

    def test_find_child_empty_result_returns_none(self):
        self.assertIsNone(find_child(_FakeService({"files": []}), "parent", "IRRA"))

    def test_find_child_returns_first_match(self):
        result = find_child(
            _FakeService({"files": [{"id": "abc", "name": "IRRA"}]}),
            "parent",
            "IRRA",
        )
        self.assertEqual(result["id"], "abc")

    def test_load_both_scraper_shapes_and_deduplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first.json"
            second = Path(tmp) / "second.json"
            first.write_text(json.dumps({"issuers": {"AAA": {"reports": [
                {"year": 2025, "url": "https://a/old.pdf", "company": "A"}
            ]}}}), encoding="utf-8")
            second.write_text(json.dumps({"issuers": {"AAA": {"reports": [
                {"year": 2025, "url": "https://a/new.pdf", "company": "A"},
                {"year": 2024, "url": "https://a/2024.pdf", "company": "A"}
            ]}}}), encoding="utf-8")
            reports = load_reports([first, second])
            self.assertEqual([(r.code, r.year) for r in reports], [("AAA", 2025), ("AAA", 2024)])
            self.assertEqual(reports[0].url, "https://a/new.pdf")

    def test_google_drive_view_url_conversion(self):
        url = "https://drive.google.com/file/d/abc123/view?usp=sharing"
        self.assertEqual(
            google_drive_download_url(url),
            "https://drive.usercontent.google.com/download?id=abc123&export=download&confirm=t",
        )

    def test_folder_name_is_code_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.json"
            source.write_text(json.dumps({"issuers": {"IRRA": {"reports": [
                {"year": 2025, "url": "https://a/2025.pdf", "company": "Itama"}
            ]}}}), encoding="utf-8")
            report = load_reports([source])[0]
            self.assertEqual(report.code, "IRRA")
            self.assertEqual(report.pdf_name, "IRRA_Annual_Report_2025.pdf")


if __name__ == "__main__":
    unittest.main()
