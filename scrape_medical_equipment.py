#!/usr/bin/env python3
"""Scrape laporan tahunan IRRA, OMED, CHIP, HALO, dan PEVE.

Skrip selalu mencoba halaman Hubungan Investor resmi terlebih dahulu. Jika
halaman sedang menolak koneksi otomatis, daftar URL resmi yang diverifikasi
pada 18 Agustus 2026 dipakai sebagai fallback. Skrip tidak menembus CAPTCHA,
login, atau firewall.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


YEAR_RE = re.compile(r"\b(20(?:1\d|2\d|3\d))\b")
ANNUAL_RE = re.compile(r"(?i)annual\s+(?:and\s+sustainability\s+)?report|integrated\s+report|laporan\s+tahunan")
FINANCIAL_RE = re.compile(r"(?i)financial[\s_-]+statements?|laporan[\s_-]+keuangan")
SUSTAINABILITY_RE = re.compile(r"(?i)sustainability\s+report|laporan\s+berkelanjutan|laporan\s+keberlanjutan")
PDF_RE = re.compile(r"(?i)\.pdf(?:$|[?#])")
WINDOW = set(range(2021, 2026))


@dataclass(frozen=True)
class Issuer:
    code: str
    name: str
    technology: str
    page_url: str
    classification: str
    note: str = ""


@dataclass
class Report:
    code: str
    company: str
    year: int
    url: str
    discovery: str
    link_status: str = "belum diuji"
    link_detail: str = ""


ISSUERS: dict[str, Issuer] = {
    "IRRA": Issuer(
        "IRRA",
        "PT Itama Ranoraya Tbk",
        "WordPress + Divi + Bootstrap + jQuery",
        "https://itama.co.id/investors/openness/",
        "Alat & perlengkapan medis (distributor)",
    ),
    "OMED": Issuer(
        "OMED",
        "PT Jayamas Medica Industri Tbk",
        "PHP/Laravel-style storage + HTML/CSS/JavaScript",
        "https://www.onemed.co.id/laporan-tahunan",
        "Alat & perlengkapan medis (produsen)",
        "Laporan resmi tersedia sejak tahun buku 2022, bertepatan dengan tahun IPO.",
    ),
    "CHIP": Issuer(
        "CHIP",
        "PT Pelita Teknologi Global Tbk",
        "HTML statis + Bootstrap 5 + JavaScript",
        "https://www.pelitateknologi.com/investor.html",
        "Teknologi/telekomunikasi — bukan alat medis",
        "Tetap diproses karena kode ini ada dalam daftar pengguna.",
    ),
    "HALO": Issuer(
        "HALO",
        "PT Haloni Jane Tbk",
        "WordPress + WPBakery + jQuery",
        "https://www.halonijane.co.id/annual-report/",
        "Alat & perlengkapan medis (sarung tangan medis)",
        "Halaman menamai bagian menurut tahun terbit; tahun buku laporan adalah satu tahun sebelumnya.",
    ),
    "PEVE": Issuer(
        "PEVE",
        "PT Penta Valent Tbk",
        "WordPress + Gradiant theme + jQuery",
        "https://www.pentavalent.co.id/sustainability-reports",
        "Distribusi farmasi dan alat kesehatan",
        "Tautan 2022 diarahkan oleh situs resmi perusahaan ke Google Drive.",
    ),
}


# Snapshot URL dokumen yang ditautkan halaman resmi. Fallback diperlukan saat
# halaman indeks menolak koneksi bot atau subdomain penyimpanan sedang lambat.
FALLBACK_URLS: dict[str, dict[int, str]] = {
    "IRRA": {
        2025: "https://iris.co.id/public/file_web_itama/IRRA-Annual-Report-2025.pdf",
        2024: "https://irfis.itama.co.id:882/files/Annual-Report-2024-IRRA.pdf",
        2023: "https://irfis.itama.co.id:882/files/annual-report-irra-2023.pdf",
        2022: "https://itama.co.id/wp-content/uploads/2023/04/Annual-Report-2022-PT-Itama-Ranoraya-Tbk.pdf",
        2021: "https://itama.co.id/wp-content/uploads/2022/05/AR-IRRA-2021_FINAL.pdf",
    },
    "OMED": {
        2025: "https://www.onemed.co.id/storage/images/image/web-laporan-tahunan-dan-keberlanjutan-2025-omed.pdf",
        2024: "https://www.onemed.co.id/storage/images/image/integrated-report-omed-2024.pdf",
        2023: "https://www.onemed.co.id/storage/images/image/ir-omed-2023-hi-res-compressed.pdf",
        2022: "https://www.onemed.co.id/storage/images/image/ir-jayamas-medika-2022-hires3.pdf",
    },
    "CHIP": {
        2025: "https://www.pelitateknologi.com/doc/Laporan%20Keuangan/2025/ARSR%20CHIP%202025.pdf",
        2024: "https://www.pelitateknologi.com/doc/Laporan%20Keuangan/2024/Annual%20Report%20ARSR%20CHIP%202024.pdf",
        2023: "https://www.pelitateknologi.com/doc/Laporan%20Keuangan/2023/Annual%20Report_CHIP_2023.pdf",
        2022: "https://www.pelitateknologi.com/doc/Laporan%20Keuangan/2022/Annual%20Report%20CHIP%202022.pdf",
    },
    "HALO": {
        2025: "https://www.halonijane.co.id/wp-content/uploads/2026/06/20260430-AR-SR-HALONI-Final.pdf",
        2024: "https://www.halonijane.co.id/wp-content/uploads/2025/04/20250327-IR-HALO-2024.pdf",
        2023: "https://www.halonijane.co.id/wp-content/uploads/2024/04/20240429-AR-SR-HALO-JANE-23.pdf",
        2022: "https://www.halonijane.co.id/wp-content/uploads/2023/06/ARSR-HALO-FINAL-31052023-FINAL.pdf",
    },
    "PEVE": {
        2025: "https://www.pentavalent.co.id/wp-content/uploads/2026/05/IR25-PEVE-30April2026.pdf",
        2024: "https://www.pentavalent.co.id/wp-content/uploads/2025/05/Book_IR24_PEVE_OJK.pdf",
        2023: "https://www.pentavalent.co.id/wp-content/uploads/2024/06/IR-PEVE-2023_0905-R.pdf",
        2022: "https://drive.google.com/file/d/1S52hGF-rHN21XIh4L0WU7bIm8iVfkhS9/view?usp=sharing",
    },
}


def new_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/126.0 Safari/537.36 "
            "AnnualReportResearch/1.0"
        ),
        "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
        "Accept-Language": "id-ID,id;q=0.9,en;q=0.7",
    })
    retry = Retry(
        total=2,
        connect=2,
        read=2,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "HEAD"),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def safe_url(url: str) -> str:
    """Encode spasi/non-ASCII tanpa mengubah slash dan query URL."""
    parts = urlparse(url)
    return urlunparse((
        parts.scheme,
        parts.netloc,
        quote(parts.path, safe="/%:@"),
        parts.params,
        quote(parts.query, safe="=&?/%:@+"),
        parts.fragment,
    ))


def fetch_html(session: requests.Session, url: str, timeout: float) -> str:
    response = session.get(safe_url(url), timeout=timeout)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").lower()
    if "html" not in content_type and "text" not in content_type:
        raise ValueError(f"respons bukan HTML ({content_type or 'tanpa content-type'})")
    return response.text


def anchor_context(anchor, levels: int = 5) -> str:
    node = anchor
    best = " ".join(anchor.stripped_strings)
    for _ in range(levels):
        node = node.parent
        if node is None:
            break
        text = " ".join(node.stripped_strings)
        if len(text) <= 700:
            best = text
        # Tahun dari blok terdekat lebih dapat dipercaya daripada tahun folder
        # upload pada URL (contoh: dokumen FY2022 diunggah pada 2023).
        if YEAR_RE.search(text) and len(text) <= 700:
            return text
    return best


def reports_generic(code: str, html: str) -> list[Report]:
    """Parser untuk IRRA, OMED, CHIP, dan PEVE."""
    issuer = ISSUERS[code]
    soup = BeautifulSoup(html, "html.parser")
    found: dict[int, str] = {}
    for anchor in soup.select("a[href]"):
        href = urljoin(issuer.page_url, anchor.get("href", "").strip())
        text = " ".join(anchor.stripped_strings)
        context = anchor_context(anchor)
        if not (PDF_RE.search(href) or "drive.google.com/file/" in href):
            continue
        # Jangan biarkan blok induk yang juga memuat annual report mengubah
        # sebuah tautan laporan keuangan menjadi false positive.
        if FINANCIAL_RE.search(f"{text} {href}") and not ANNUAL_RE.search(f"{text} {href.replace('-', ' ')}"):
            continue
        visible = f"{text} {context}"
        filename = urlparse(href).path.rsplit("/", 1)[-1].replace("-", " ").replace("_", " ")
        if SUSTAINABILITY_RE.search(visible) and not ANNUAL_RE.search(visible):
            continue
        if not ANNUAL_RE.search(f"{visible} {filename}"):
            continue
        match = YEAR_RE.search(visible) or YEAR_RE.search(filename)
        if match and int(match.group(1)) in WINDOW:
            found[int(match.group(1))] = safe_url(href)
    return [
        Report(code, issuer.name, year, url, "live")
        for year, url in sorted(found.items(), reverse=True)
    ]


def reports_halo(html: str) -> list[Report]:
    """HALO memakai tahun terbit pada heading (2026 berarti tahun buku 2025)."""
    issuer = ISSUERS["HALO"]
    soup = BeautifulSoup(html, "html.parser")
    found: dict[int, str] = {}
    for anchor in soup.select("a[href]"):
        href = urljoin(issuer.page_url, anchor.get("href", "").strip())
        if not PDF_RE.search(href):
            continue
        heading = anchor.find_previous(["h2", "h3", "h4", "h5"])
        match = YEAR_RE.search(" ".join(heading.stripped_strings) if heading else "")
        if not match:
            continue
        fiscal_year = int(match.group(1)) - 1
        if fiscal_year in WINDOW:
            found[fiscal_year] = safe_url(href)
    return [
        Report("HALO", issuer.name, year, url, "live")
        for year, url in sorted(found.items(), reverse=True)
    ]


def merge_fallback(code: str, live: list[Report]) -> list[Report]:
    issuer = ISSUERS[code]
    by_year = {report.year: report for report in live if report.year in WINDOW}
    for year, url in FALLBACK_URLS[code].items():
        by_year.setdefault(year, Report(code, issuer.name, year, url, "fallback resmi"))
    return [by_year[year] for year in sorted(by_year, reverse=True) if year in WINDOW][:5]


def validate_link(session: requests.Session, report: Report, timeout: float) -> None:
    """Cek URL dengan GET parsial; cukup untuk PDF besar dan server tanpa HEAD."""
    try:
        response = session.get(
            safe_url(report.url),
            headers={"Range": "bytes=0-1023"},
            timeout=timeout,
            stream=True,
            allow_redirects=True,
        )
        status = response.status_code
        content_type = response.headers.get("content-type", "").lower()
        first = next(response.iter_content(8), b"")
        response.close()
        if status in (200, 206):
            is_pdf = first.startswith(b"%PDF") or "pdf" in content_type
            if "drive.google.com" in report.url:
                report.link_status = "OK"
                report.link_detail = f"HTTP {status}; halaman resmi Google Drive"
            elif is_pdf:
                report.link_status = "OK"
                report.link_detail = f"HTTP {status}; PDF"
            else:
                report.link_status = "PERIKSA"
                report.link_detail = f"HTTP {status}; tipe {content_type or 'tidak diketahui'}"
        else:
            report.link_status = "GAGAL"
            report.link_detail = f"HTTP {status}"
    except requests.RequestException as exc:
        report.link_status = "TERHALANG"
        report.link_detail = f"{type(exc).__name__}: {str(exc)[:140]}"


def scrape(code: str, session: requests.Session, timeout: float) -> tuple[list[Report], str]:
    issuer = ISSUERS[code]
    live: list[Report] = []
    error = ""
    try:
        html = fetch_html(session, issuer.page_url, timeout)
        live = reports_halo(html) if code == "HALO" else reports_generic(code, html)
    except (requests.RequestException, ValueError) as exc:
        error = f"{type(exc).__name__}: {str(exc)[:180]}"
    return merge_fallback(code, live), error


def markdown(results: dict[str, list[Report]], errors: dict[str, str]) -> str:
    lines = [
        "## Alat & Perlengkapan Medis",
        "",
        "> Periode tahun buku: 2021–2025. Emiten yang IPO pada 2022 hanya memiliki empat laporan publik (2022–2025).",
        "",
    ]
    for code, issuer in ISSUERS.items():
        lines += [
            f"- **{code}** - {issuer.name} (**{issuer.technology}**)",
            f"  - `Klasifikasi`: {issuer.classification}",
            f"  - `Halaman resmi`: [Annual Report]({issuer.page_url})",
        ]
        if issuer.note:
            lines.append(f"  - `Catatan`: {issuer.note}")
        if errors.get(code):
            lines.append(f"  - `Akses halaman saat pengujian`: fallback dipakai ({errors[code]})")
        lines.append("  - `Laporan per tahun`:")
        for report in results[code]:
            lines.append(
                f"    - **{report.year}**: [Laporan Tahunan {report.year}]({report.url}) "
                f"— `{report.link_status}` ({report.discovery}; {report.link_detail})"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codes", nargs="+", choices=ISSUERS, default=list(ISSUERS))
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--skip-link-check", action="store_true")
    parser.add_argument("--output-prefix", default="hasil_alat_perlengkapan_medis")
    args = parser.parse_args()

    session = new_session()
    results: dict[str, list[Report]] = {}
    errors: dict[str, str] = {}
    for code in args.codes:
        reports, error = scrape(code, session, args.timeout)
        if not args.skip_link_check:
            for report in reports:
                validate_link(session, report, args.timeout)
        results[code] = reports
        errors[code] = error

    prefix = Path(args.output_prefix)
    prefix.with_suffix(".md").write_text(markdown(results, errors), encoding="utf-8")
    payload = {
        "period": {"from": 2021, "to": 2025},
        "issuers": {
            code: {
                "metadata": asdict(ISSUERS[code]),
                "page_access_error": errors[code],
                "reports": [asdict(report) for report in results[code]],
            }
            for code in results
        },
    }
    prefix.with_suffix(".json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    total = sum(len(items) for items in results.values())
    ok = sum(r.link_status == "OK" for items in results.values() for r in items)
    print(f"Selesai: {total} laporan; {ok} tautan OK.")
    print(prefix.with_suffix(".md").resolve())
    print(prefix.with_suffix(".json").resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
