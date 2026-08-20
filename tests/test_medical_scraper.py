import unittest

from scrape_medical_equipment import merge_fallback, reports_generic, reports_halo, safe_url


class MedicalReportParserTests(unittest.TestCase):
    def test_generic_relative_pdf(self):
        html = """
        <section><h4>Laporan Keuangan 2025</h4>
          <a href="../doc/Laporan Keuangan/2025/ARSR CHIP 2025.pdf">
            Annual Report - 2025 PT Pelita Teknologi Global Tbk.
          </a>
        </section>
        """
        reports = reports_generic("CHIP", html)
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0].year, 2025)
        self.assertNotIn(" ", reports[0].url)

    def test_generic_skips_financial_statement(self):
        html = """
        <p><a href="/financial-statement-2025.pdf">Laporan Keuangan 2025</a></p>
        <p><a href="/annual-report-2024.pdf">Annual Report 2024</a></p>
        """
        reports = reports_generic("OMED", html)
        self.assertEqual([r.year for r in reports], [2024])

    def test_visible_fiscal_year_wins_over_upload_folder(self):
        html = """
        <table><tr><td>Laporan Tahunan 2022</td>
          <td><a href="/uploads/2023/04/annual-report.pdf">Lihat</a></td>
        </tr></table>
        """
        reports = reports_generic("IRRA", html)
        self.assertEqual([r.year for r in reports], [2022])

    def test_standalone_sustainability_report_is_skipped(self):
        html = """
        <table><tr><td>Laporan Berkelanjutan 2022</td>
          <td><a href="/uploads/2023/05/SR-IRRA-2022.pdf">Lihat</a></td>
        </tr></table>
        """
        self.assertEqual(reports_generic("IRRA", html), [])

    def test_halo_publication_year_to_fiscal_year(self):
        html = """
        <h4>2026</h4><p><a href="/uploads/ar-final.pdf">ARSR HALO FINAL</a></p>
        <h4>2025</h4><p><a href="/uploads/ar-final-2.pdf">ARSR HALO FINAL</a></p>
        """
        reports = reports_halo(html)
        self.assertEqual([r.year for r in reports], [2025, 2024])

    def test_live_wins_over_fallback(self):
        html = '<a href="/custom-2025.pdf">Annual Report 2025</a>'
        live = reports_generic("PEVE", html)
        merged = merge_fallback("PEVE", live)
        self.assertTrue(merged[0].url.endswith("custom-2025.pdf"))
        self.assertEqual(merged[0].discovery, "live")

    def test_safe_url_encodes_spaces(self):
        self.assertEqual(
            safe_url("https://example.com/a b/file.pdf?x=a b"),
            "https://example.com/a%20b/file.pdf?x=a%20b",
        )


if __name__ == "__main__":
    unittest.main()
