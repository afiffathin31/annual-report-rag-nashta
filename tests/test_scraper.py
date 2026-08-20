import unittest

from scrape_annual_reports import (
    reports_aladin_pages,
    reports_btpn,
    reports_from_html,
    reports_pnbs,
)


class ParserTests(unittest.TestCase):
    def test_btpn_ssr(self):
        html = """
        <p><strong><span>2025</span></strong></p>
        <p><a href="https://cdn.example/AR2025.pdf"><img></a></p>
        <p><strong><span>2024</span></strong></p>
        <p><a href="https://cdn.example/AR2024.pdf"><img></a></p>
        """
        result = reports_btpn(html)
        self.assertEqual([(r.year, r.url) for r in result], [
            (2025, "https://cdn.example/AR2025.pdf"),
            (2024, "https://cdn.example/AR2024.pdf"),
        ])

    def test_aladin_articles(self):
        html = """
        <article class="laporan report_category-laporan-tahunan">
          <h3>Laporan Tahunan 2025</h3>
          <a href="/uploads/2026/04/ar-2025.pdf">Download</a>
        </article>
        <article class="laporan report_category-laporan-berkelanjutan">
          <h3>Laporan Keberlanjutan 2025</h3>
          <a href="/uploads/2026/04/sr-2025.pdf">Download</a>
        </article>
        """
        result = reports_aladin_pages([html])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].year, 2025)

    def test_generic_card_prefers_indonesian(self):
        html = """
        <div><h3>Laporan Tahunan 2024 (ENG VERSION)</h3>
          <a href="/storage/reports/eng.pdf">Unduh</a></div>
        <div><h3>Laporan Tahunan 2024 (IND VERSION)</h3>
          <a href="/storage/reports/ind.pdf">Unduh</a></div>
        """
        result = reports_from_html("BRIS", html, "https://www.bankbsi.co.id/")
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0].url.endswith("ind.pdf"))

    def test_pnbs_annual_report_tab(self):
        html = """
        <div id="list-pertama">
          <div class="card"><span>2025</span>
            <a href="/about/download_ar/token-2025">Download</a></div>
        </div>
        <div id="list-kedua">
          <div class="card"><span>2025</span>
            <a href="/about/download_ar/not-an-annual-report">Download</a></div>
        </div>
        """
        result = reports_pnbs(html)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].year, 2025)
        self.assertTrue(result[0].url.endswith("token-2025"))


if __name__ == "__main__":
    unittest.main()
