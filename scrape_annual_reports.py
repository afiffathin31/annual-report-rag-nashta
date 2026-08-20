#!/usr/bin/env python3
"""Scrape lima laporan tahunan terbaru emiten bank syariah di BEI.

Prinsip kerja:
1. Ambil tautan dari halaman resmi emiten.
2. Jika situs sedang diblokir WAF/DNS bermasalah, gunakan snapshot tautan resmi
   yang sudah diverifikasi pada 18 Agustus 2026.
3. Jangan mencoba menembus CAPTCHA, login, atau proteksi akses.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.exceptions import InsecureRequestWarning


YEAR_RE = re.compile(r"\b(20(?:1\d|2\d|3\d))\b")
YEAR_EXACT_RE = re.compile(r"^(20(?:1\d|2\d|3\d))$")
ANNUAL_RE = re.compile(r"(?i)laporan\s+tahunan|annual\s+report")
PDF_RE = re.compile(r"(?i)\.pdf(?:$|[?#])")


@dataclass(frozen=True)
class Issuer:
    code: str
    name: str
    technology: str
    page_url: str


@dataclass
class Report:
    code: str
    company: str
    year: int
    url: str
    discovery: str
    link_status: str = "belum diuji"
    link_detail: str = ""


ISSUERS = {
    "BRIS": Issuer(
        "BRIS",
        "PT Bank Syariah Indonesia (Persero) Tbk",
        "PHP + Vue/jQuery + Bootstrap; Imperva WAF",
        "https://www.bankbsi.co.id/index.php/company-information/reports",
    ),
    "BTPS": Issuer(
        "BTPS",
        "PT Bank BTPN Syariah Tbk",
        "Nuxt 3/Vue (SSR) + Tailwind CSS",
        "https://www.btpnsyariah.com/laporan-tahunan",
    ),
    "BANK": Issuer(
        "BANK",
        "PT Bank Aladin Syariah Tbk",
        "WordPress + Elementor/Elementor Pro",
        "https://aladinbank.id/laporan-tahunan/",
    ),
    "PNBS": Issuer(
        "PNBS",
        "PT Bank Panin Dubai Syariah Tbk",
        "Laravel/PHP + Bootstrap + jQuery",
        "https://www.pdsb.co.id/about/laporan_keuangan",
    ),
}


# Fallback hanya berisi URL dokumen milik domain resmi emiten. URL ini juga membuat
# hasil tetap dapat direproduksi saat halaman indeks diblokir WAF atau DNS rusak.
FALLBACK_URLS: dict[str, dict[int, str]] = {
    "BRIS": {
        # PDF storage 2025 yang semula dipublikasikan kini 404; gunakan flipbook resmi.
        2025: "https://ir.bankbsi.co.id/misc/AR/AR2025-ID/",
        2024: "https://www.bankbsi.co.id/storage/reports/H32Xdj6IecC3OvR6HpXaVYZpg3aTPfjxLqolqvtr.pdf",
        2023: "https://www.bankbsi.co.id/storage/reports/XE4D91ZySzkYrdpr9Vt7m1aiXNsUcmAzQ9Im8W4b.pdf",
        2022: "https://www.bankbsi.co.id/storage/reports/CYUiWN8xhxNSweszsprHjbXOULvEoo9wB6NzzHd2.pdf",
        2021: "https://www.bankbsi.co.id/storage/reports/aB6eOJrdWGntv3yApMzatw4808SM9P1jRMAyh03G.pdf",
    },
    "BTPS": {
        2025: "https://cdn-btpns-cms-prod.s3.ap-southeast-3.amazonaws.com/1776675345816-568448371-AR_BTPN_Syariah_2025__.pdf",
        2024: "https://cdn-btpns-cms-prod.s3.ap-southeast-3.amazonaws.com/1744633438703-718947652-BTPSAR2024IND-final.pdf",
        2023: "https://cdn-btpns-cms-prod.s3.ap-southeast-3.amazonaws.com/1737349460964-672629434-AR2023.pdf",
        2022: "https://cdn-btpns-cms-prod.s3.ap-southeast-3.amazonaws.com/1737349542713-248463324-AR2022.pdf",
        2021: "https://cdn-btpns-cms-prod.s3.ap-southeast-3.amazonaws.com/1737349620482-316816540-AR2021.pdf",
    },
    "BANK": {
        2025: "https://aladinbank.id/uploads/2026/04/AR-Bank-Aladin-Syariah-2025.pdf",
        2024: "https://aladinbank.id/uploads/2025/04/Laporan-Tahunan-Aladin-2024-Final_compressed.pdf",
        2023: "https://aladinbank.id/uploads/2024/04/AR-2023.pdf",
        2022: "https://aladinbank.id/uploads/2023/05/AR-ALADIN-22-1.pdf",
        2021: "https://aladinbank.id/uploads/2021/04/AR-BANK-ALADIN-2021-upload.pdf",
    },
    "PNBS": {
        # Sampai pengujian 18-08-2026, halaman resmi masih menampilkan 2024
        # sebagai laporan tahunan terbaru. Karena itu lima terbaru = 2020-2024.
        2024: "https://www.panindubaisyariah.co.id.paninbanksyariah.co.id/about/download_ar/eyJpdiI6ImhiU0x5cllZVENQbEJwMDliNDhMUnc9PSIsInZhbHVlIjoiaWtiTWtya1VTanlOc0dHT25CR0JrbjlKMEhPQ2Erc1FwWnQyNythMEVuUT0iLCJtYWMiOiI5YjQyNTVmZDJjNTcyMTcwZTRlM2MxMzI2NDJkM2Q3YjU4NWM3MDRmM2FhZWRmNWQ3MzA0YjcyNDBlOTZkMTViIiwidGFnIjoiIn0%3D",
        2023: "https://www.panindubaisyariah.co.id.paninbanksyariah.co.id/about/download_ar/eyJpdiI6Ijd0RTNTQWYzd05yMGFvZ1VVTXA2NUE9PSIsInZhbHVlIjoiNHRGZjFYMDcyRHhqcHhBSEkyMVIyOU5QY1lXVlZFVHY5VEQ5QWMrQ3pxbz0iLCJtYWMiOiIxMTdiYjIzNDk0MmM5ZGVmM2ViN2QwMmMwYmVlZmQ3OWIwZmFhNTJlYzljNTU0NTM4MGFlZDdhN2ExY2JjMzdiIiwidGFnIjoiIn0%3D",
        2022: "https://www.panindubaisyariah.co.id.paninbanksyariah.co.id/about/download_ar/eyJpdiI6IkwwVDVJdTNrelUxa2p6eEY3MkxCTlE9PSIsInZhbHVlIjoibm52Zk1FM1lqNFcyekFqZ3FKWUFvdmd0c2lmUTBLZ0tVNFA5UjRnQ0RoOD0iLCJtYWMiOiJiZTAyMjExNTA4NTUxNWJhNjc5NDQ1OTkwMDMxZGYzMzA2YjAxMDRjZjYzYzIwNTJmNGIzMTVjY2YwODkzOGNhIiwidGFnIjoiIn0%3D",
        2021: "https://www.panindubaisyariah.co.id.paninbanksyariah.co.id/about/download_ar/eyJpdiI6IjNBWTMrdWhzM09ONU1ERGtCb1dTamc9PSIsInZhbHVlIjoiektTeERjNDA3cmhEd2RLbElwZ2hQUXlhbW5UNXdmbEIwMUJ0MDl2cC8rdz0iLCJtYWMiOiI3ODNlYmIxNTdiYzA3NGJhYjBlMGJjOWU4Y2QyODNhMmRmMDI2MjYzNzYzMWYyNDBjNzI3NjM2M2NjZDVjYmExIiwidGFnIjoiIn0%3D",
        2020: "https://www.panindubaisyariah.co.id.paninbanksyariah.co.id/about/download_ar/eyJpdiI6IjhlTURPckFqWnlpL0JkUWEwOXJEK2c9PSIsInZhbHVlIjoiNExOQnJ6S0E0ekZKTHdyL1JnWmFXc1MzWVhuYmdaN3JGU1M2cnp2ZGpPYz0iLCJtYWMiOiJmNTI1ZDhjZGJkODdmNThmMDQ0OGVmZjczYjZjYzQzMTVjNDk1YjM1YmRlZDI3YTkwOWFiMGQxN2EzMDc1OTVmIiwidGFnIjoiIn0%3D",
    },
}

# Domain aktif PNBS dan token unduhan hasil pembacaan halaman resmi 18-08-2026.
# Assignment ini menggantikan host legacy pada snapshot di atas.
PNBS_DOWNLOAD_BASE = "https://www.pdsb.co.id/about/download_ar/"
FALLBACK_URLS["PNBS"] = {
    2025: PNBS_DOWNLOAD_BASE + "eyJpdiI6IkxNbHAxRkNjbnlncmttUTVIR0hiT3c9PSIsInZhbHVlIjoiVzhLZ2tBVXZPZWlzTmkzSHlYNkNkVlhZR214ei9hWENiWjRXNWlGK0Mzcz0iLCJtYWMiOiI3MTBjZDcyZDM4NzNiMDg2OTdhYmEyZTVkOTgyYWQ1NmI3N2YzZDRmOGRlMGYyYWE3NTA0MGVlMzMzOWNlMmZkIiwidGFnIjoiIn0=",
    2024: PNBS_DOWNLOAD_BASE + "eyJpdiI6IjRSbTVhV1lFYjIxS1hzVDZwNlAweUE9PSIsInZhbHVlIjoiZUI3WGw0Uk1Ic25VemQvcFQ0UkhkL3BBWFVxZ1JzS1V6Zk5hM2NmM2FOdz0iLCJtYWMiOiI3MjJhMWNmMGQ1OGI5OTVhYTI2NmM0MWIwMGZmOGNmZDEyZmM0YzU5YjgzYjEwNTA1YmQ1NDc2MzFmYzZiZTdkIiwidGFnIjoiIn0=",
    2023: PNBS_DOWNLOAD_BASE + "eyJpdiI6IkljVDdWNGU1TVB2VWdDdVBkNTBDNmc9PSIsInZhbHVlIjoiS3cwTEh1ZFZ2NWJ1VnRmQ3pldXNlSEplcDdaYUpMQUVWbDUyRVgzQzVnVT0iLCJtYWMiOiI5YmMwYjBlMTdmNTA4NzFiYTQ5OGMyNmYyNTcwZjE5ZjZmNmQ4MGFkZTk5MzVhZTI4YmI0YjI3NDk4YWEyMGI0IiwidGFnIjoiIn0=",
    2022: PNBS_DOWNLOAD_BASE + "eyJpdiI6Ik5ISU52MnlsaDU3dytZNm9nZVJYOHc9PSIsInZhbHVlIjoibWVKNW11SXA3YXpmckJ3RlQ4MHF5blRoakJITzQ0UjAwanI1RGhZUTFzWT0iLCJtYWMiOiIwZmI1ODgzNWVjN2UwNDQzYmFhMTI0OTg4MmRhYzg2MjkyZmFlNTcwNGY5NDVhZGIxMTRmZTdhNGNkOGEyZmEzIiwidGFnIjoiIn0=",
    2021: PNBS_DOWNLOAD_BASE + "eyJpdiI6IkJXMy8yZDhEMHZ6SHVQbVlrbktkZlE9PSIsInZhbHVlIjoibGJHY0RvMXVJTE1HYlNJY1hKK3k1bTg4RGVzU3VLTVUzaWZLZlVyKyt6ND0iLCJtYWMiOiI5MzAwMjBlZDQ2ZTRjNTcxYmVmMTk5NThhZmVmYzg4N2MzN2M3ZWUzMWEzZDIyM2E4OGJmZmM0MGFlZmM0ODFlIiwidGFnIjoiIn0=",
}


def new_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/126.0 Safari/537.36 "
                "AnnualReportResearch/1.0"
            ),
            "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
            "Accept-Language": "id-ID,id;q=0.9,en;q=0.7",
        }
    )
    retry = Retry(
        total=2,
        connect=2,
        read=2,
        backoff_factor=0.7,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "HEAD"),
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.mount("http://", HTTPAdapter(max_retries=retry))
    return session


def request_with_tls_fallback(
    session: requests.Session, method: str, url: str, **kwargs
) -> requests.Response:
    """Retry khusus pdsb.co.id bila server tidak mengirim rantai CA lengkap.

    Percobaan pertama selalu memverifikasi TLS secara normal. Fallback tanpa
    verifikasi hanya berlaku untuk host resmi PNBS dan ditandai pada response.
    """
    try:
        return session.request(method, url, **kwargs)
    except requests.exceptions.SSLError:
        host = (urlparse(url).hostname or "").lower()
        if host not in {"pdsb.co.id", "www.pdsb.co.id"}:
            raise
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", InsecureRequestWarning)
            response = session.request(method, url, verify=False, **kwargs)
        setattr(response, "tls_fallback_used", True)
        return response


def fetch_html(session: requests.Session, url: str, timeout: float) -> str:
    response = request_with_tls_fallback(session, "GET", url, timeout=timeout)
    response.raise_for_status()
    ctype = response.headers.get("content-type", "").lower()
    if "html" not in ctype and "text" not in ctype:
        raise ValueError(f"respons bukan HTML ({ctype or 'tanpa content-type'})")
    return response.text


def nearest_context(anchor, max_ancestors: int = 6) -> str:
    """Cari blok kecil di sekitar tautan yang memuat judul dan tahun."""
    node = anchor
    candidate = " ".join(anchor.stripped_strings)
    for _ in range(max_ancestors):
        node = node.parent
        if node is None:
            break
        text = " ".join(node.stripped_strings)
        if len(text) <= 900:
            candidate = text
        if ANNUAL_RE.search(text) and YEAR_RE.search(text) and len(text) <= 900:
            return text
    return candidate


def reports_from_html(code: str, html: str, base_url: str) -> list[Report]:
    """Parser generik; cocok untuk BRIS dan kartu unduhan PNBS."""
    issuer = ISSUERS[code]
    soup = BeautifulSoup(html, "html.parser")
    found: dict[int, tuple[str, str]] = {}
    for anchor in soup.select("a[href]"):
        href = urljoin(base_url, anchor.get("href", "").strip())
        context = nearest_context(anchor)
        match = YEAR_RE.search(context)
        if not match or not ANNUAL_RE.search(context):
            continue
        if not (PDF_RE.search(href) or "download_ar/" in href or "storage/reports/" in href):
            continue
        year = int(match.group(1))
        # Jika satu tahun punya versi IND dan ENG, prioritaskan IND/non-ENG.
        score = 2 if re.search(r"(?i)\bIND\b|indonesia", context) else 1
        if re.search(r"(?i)\bENG\b|english", context):
            score = 0
        if year not in found or score > int(found[year][1]):
            found[year] = (href, str(score))
    return [
        Report(code, issuer.name, year, url, "live")
        for year, (url, _score) in found.items()
    ]


def reports_btpn(html: str) -> list[Report]:
    issuer = ISSUERS["BTPS"]
    soup = BeautifulSoup(html, "html.parser")
    found: dict[int, str] = {}
    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "").strip()
        if not PDF_RE.search(href):
            continue
        previous_year = anchor.find_previous(string=YEAR_EXACT_RE)
        context = nearest_context(anchor)
        match = YEAR_RE.search(previous_year.strip() if previous_year else context)
        if match:
            found[int(match.group(1))] = urljoin(issuer.page_url, href)
    return [Report("BTPS", issuer.name, year, url, "live") for year, url in found.items()]


def reports_aladin_pages(pages: Iterable[str]) -> list[Report]:
    issuer = ISSUERS["BANK"]
    found: dict[int, str] = {}
    for html in pages:
        soup = BeautifulSoup(html, "html.parser")
        for article in soup.select("article.laporan, article[class*='report_category-laporan-tahunan']"):
            text = " ".join(article.stripped_strings)
            title_match = ANNUAL_RE.search(text)
            year_match = YEAR_RE.search(text)
            if not title_match or not year_match:
                continue
            year = int(year_match.group(1))
            for anchor in article.select("a[href]"):
                href = urljoin(issuer.page_url, anchor.get("href", "").strip())
                if PDF_RE.search(href):
                    found[year] = href
                    break
    return [Report("BANK", issuer.name, year, url, "live") for year, url in found.items()]


def reports_pnbs(html: str) -> list[Report]:
    """Ambil kartu hanya dari tab Laporan Tahunan PNBS."""
    issuer = ISSUERS["PNBS"]
    soup = BeautifulSoup(html, "html.parser")
    found: dict[int, str] = {}
    for card in soup.select("#list-pertama .card"):
        year_match = YEAR_RE.search(" ".join(card.stripped_strings))
        anchor = card.select_one("a[href*='/about/download_ar/']")
        if year_match and anchor:
            found[int(year_match.group(1))] = urljoin(
                issuer.page_url, anchor.get("href", "").strip()
            )
    return [Report("PNBS", issuer.name, year, url, "live") for year, url in found.items()]


def scrape_live(session: requests.Session, code: str, timeout: float) -> list[Report]:
    issuer = ISSUERS[code]
    if code == "BANK":
        pages: list[str] = []
        for page_no in range(1, 5):
            url = issuer.page_url if page_no == 1 else f"{issuer.page_url}?page={page_no}"
            html = fetch_html(session, url, timeout)
            pages.append(html)
            if len(reports_aladin_pages(pages)) >= 5:
                break
            time.sleep(0.35)
        return reports_aladin_pages(pages)
    html = fetch_html(session, issuer.page_url, timeout)
    if code == "BTPS":
        return reports_btpn(html)
    if code == "PNBS":
        return reports_pnbs(html)
    return reports_from_html(code, html, issuer.page_url)


def combine_with_fallback(code: str, live: list[Report]) -> list[Report]:
    issuer = ISSUERS[code]
    combined = {
        year: Report(
            code,
            issuer.name,
            year,
            url.replace(
                "www.panindubaisyariah.co.id.paninbanksyariah.co.id",
                "www.paninbanksyariah.co.id",
            ),
            "snapshot resmi 18-08-2026",
        )
        for year, url in FALLBACK_URLS[code].items()
    }
    for report in live:
        combined[report.year] = report
    return sorted(combined.values(), key=lambda item: item.year, reverse=True)[:5]


def verify_link(session: requests.Session, report: Report, timeout: float) -> None:
    headers = {"Referer": ISSUERS[report.code].page_url}
    try:
        # HEAD mencegah S3/CDN mengirim seluruh berkas. Sebagian CDN menolak Range
        # tetapi menerima HEAD, sehingga ini lebih akurat untuk pengujian tautan.
        response = request_with_tls_fallback(
            session,
            "HEAD",
            report.url,
            headers=headers,
            allow_redirects=True,
            timeout=timeout,
        )
        response.raise_for_status()
        ctype = response.headers.get("content-type", "").lower()
        if "application/pdf" in ctype:
            report.link_status = "OK"
            tls_note = "; TLS fallback pdsb.co.id" if getattr(response, "tls_fallback_used", False) else ""
            report.link_detail = f"HTTP {response.status_code}; {ctype}{tls_note}"
            response.close()
            return
        if "ir.bankbsi.co.id/misc/AR/" in report.url and "html" in ctype:
            report.link_status = "OK (flipbook)"
            report.link_detail = f"HTTP {response.status_code}; {ctype}"
            response.close()
            return
        response.close()
    except Exception:
        # Beberapa WAF memblokir HEAD; lanjutkan dengan ranged GET.
        pass

    try:
        with request_with_tls_fallback(
            session,
            "GET",
            report.url,
            headers={**headers, "Range": "bytes=0-7"},
            stream=True,
            allow_redirects=True,
            timeout=timeout,
        ) as response:
            response.raise_for_status()
            first = next(response.iter_content(chunk_size=8), b"")
            ctype = response.headers.get("content-type", "").lower()
            if first.startswith(b"%PDF") or "application/pdf" in ctype:
                report.link_status = "OK"
                tls_note = "; TLS fallback pdsb.co.id" if getattr(response, "tls_fallback_used", False) else ""
                report.link_detail = (
                    f"HTTP {response.status_code}; {ctype or 'PDF signature'}{tls_note}"
                )
            else:
                report.link_status = "PERIKSA"
                report.link_detail = f"HTTP {response.status_code}; content-type={ctype or 'tidak ada'}"
    except Exception as exc:  # pesan error tetap dicatat ke JSON/Markdown
        report.link_status = "GAGAL DIAKSES"
        report.link_detail = f"{type(exc).__name__}: {exc}"


def markdown_output(all_reports: dict[str, list[Report]], live_errors: dict[str, str]) -> str:
    lines = [
        "# Perbankan Syariah — Laporan Tahunan",
        "",
        "> Hasil pengambilan 18 Agustus 2026. Tahun adalah **tahun buku laporan**, bukan tahun unggah.",
        "",
        "## Kriteria klasifikasi",
        "",
        "Emiten dimasukkan bila entitas tercatatnya sendiri menjalankan kegiatan utama sebagai bank umum syariah. "
        "Bank konvensional yang hanya memiliki Unit Usaha Syariah atau anak usaha syariah yang tidak tercatat "
        "terpisah tidak dimasukkan. Hasilnya adalah empat emiten: BRIS, BTPS, BANK, dan PNBS.",
        "",
        "- `Sumber emiten`: [Profil Perusahaan Tercatat BEI]"
        "(https://www.idx.co.id/id/perusahaan-tercatat/profil-perusahaan-tercatat/)",
        "",
        "## Tautan laporan",
        "",
    ]
    for code in ("BRIS", "BTPS", "BANK", "PNBS"):
        issuer = ISSUERS[code]
        lines.extend(
            [
                f"- **{code}** - {issuer.name} (**{issuer.technology}**)",
                f"  - `Halaman resmi`: [Annual Report]({issuer.page_url})",
            ]
        )
        for report in all_reports[code]:
            status = f" — {report.link_status}" if report.link_status != "belum diuji" else ""
            lines.append(
                f"  - `{report.year}`: [Laporan Tahunan {report.year}]({report.url}){status}"
            )
        note = ""
        if code == "BRIS" and (
            code in live_errors or any(r.discovery.startswith("snapshot") for r in all_reports[code])
        ):
            note = (
                "halaman indeks dibatasi Imperva pada koneksi otomatis; "
                "snapshot tautan dokumen resmi digunakan."
            )
        elif code == "PNBS" and (
            code in live_errors or any(r.link_status == "GAGAL DIAKSES" for r in all_reports[code])
        ):
            note = (
                "domain resmi dapat dibuka di browser, tetapi pemeriksaan sertifikat Python gagal "
                "karena rantai CA server tidak lengkap; lihat fallback TLS terbatas pada dokumentasi."
            )
        elif code in live_errors:
            note = live_errors[code]
        if note:
            lines.append(f"  - `Catatan akses`: {note}")
        if code == "PNBS" and any("TLS fallback" in r.link_detail for r in all_reports[code]):
            lines.append(
                "  - `Catatan TLS`: verifikasi normal dicoba lebih dahulu; bila rantai CA gagal, "
                "retry tanpa verifikasi hanya berlaku untuk `pdsb.co.id`, lalu respons harus terdeteksi PDF."
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="hasil_annual_report.md", help="file Markdown keluaran")
    parser.add_argument("--json", default="hasil_annual_report.json", help="file JSON keluaran")
    parser.add_argument("--timeout", type=float, default=25.0, help="timeout per permintaan (detik)")
    parser.add_argument("--no-network", action="store_true", help="gunakan snapshot resmi tanpa scraping live")
    parser.add_argument("--verify", action="store_true", help="uji signature/content-type setiap tautan")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    session = new_session()
    all_reports: dict[str, list[Report]] = {}
    live_errors: dict[str, str] = {}

    for code in ("BRIS", "BTPS", "BANK", "PNBS"):
        live: list[Report] = []
        if not args.no_network:
            try:
                live = scrape_live(session, code, args.timeout)
                if not live:
                    raise ValueError("tidak menemukan kartu laporan tahunan pada HTML")
                print(f"[{code}] live: {len(live)} laporan ditemukan", file=sys.stderr)
            except Exception as exc:
                live_errors[code] = f"{type(exc).__name__}: {exc}"
                print(f"[{code}] fallback: {live_errors[code]}", file=sys.stderr)
        all_reports[code] = combine_with_fallback(code, live)

    if args.verify:
        for reports in all_reports.values():
            for report in reports:
                verify_link(session, report, args.timeout)
                print(f"[{report.code} {report.year}] {report.link_status}", file=sys.stderr)

    Path(args.output).write_text(markdown_output(all_reports, live_errors), encoding="utf-8")
    json_data = {
        "retrieved_at": "2026-08-18",
        "scope": "emiten BEI dengan kegiatan utama bank umum syariah",
        "live_errors": live_errors,
        "issuers": {
            code: {
                "issuer": asdict(ISSUERS[code]),
                "reports": [asdict(report) for report in reports],
            }
            for code, reports in all_reports.items()
        },
    }
    Path(args.json).write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Selesai: {args.output} dan {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
