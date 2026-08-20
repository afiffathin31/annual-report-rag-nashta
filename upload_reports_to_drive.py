#!/usr/bin/env python3
"""Unduh hasil scraping annual report lalu unggah ke folder Google Drive.

Struktur tujuan:
  <TARGET_FOLDER>/BRIS/BRIS_Annual_Report_2025.pdf
  <TARGET_FOLDER>/BTPS/BTPS_Annual_Report_2025.pdf
  ...

Autentikasi memakai OAuth Desktop Google. Simpan credentials.json dari Google
Cloud Console di direktori ini, lalu jalankan skrip. Browser akan dibuka pada
eksekusi pertama untuk memilih akun Google yang memiliki akses ke folder target.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
import tempfile
import time
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qs, urlparse
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.exceptions import InsecureRequestWarning


TARGET_FOLDER_ID = "1DEqq-6pGl898d9SwP860tFuykcmXTpKW"
SCOPES = ["https://www.googleapis.com/auth/drive"]
FOLDER_MIME = "application/vnd.google-apps.folder"
JSON_FILES = ("hasil_annual_report.json", "hasil_alat_perlengkapan_medis.json")
SAFE_CODE_RE = re.compile(r"^[A-Z0-9]{2,12}$")
DOWNLOAD_REFERERS = {
    # Bucket S3 BTPS mengembalikan 403 bila file diminta tanpa Referer resmi.
    "BTPS": "https://www.btpnsyariah.com/laporan-tahunan",
}
TLS_FALLBACK_HOSTS = {"pdsb.co.id", "www.pdsb.co.id"}
PNBS_REPORT_PAGE = "https://www.pdsb.co.id/about/laporan_keuangan"
EXPECTED_NON_PDF = {("BRIS", 2025)}


@dataclass(frozen=True)
class ReportItem:
    code: str
    company: str
    year: int
    url: str
    source_json: str

    @property
    def pdf_name(self) -> str:
        return f"{self.code}_Annual_Report_{self.year}.pdf"

    @property
    def shortcut_name(self) -> str:
        return f"{self.code}_Annual_Report_{self.year}.url"


def load_reports(paths: Iterable[Path]) -> list[ReportItem]:
    """Baca kedua bentuk JSON scraper dan deduplikasi berdasarkan kode+tahun."""
    reports: dict[tuple[str, int], ReportItem] = {}
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for code, issuer_data in payload.get("issuers", {}).items():
            code = code.upper().strip()
            if not SAFE_CODE_RE.fullmatch(code):
                raise ValueError(f"kode emiten tidak aman pada {path}: {code!r}")
            for raw in issuer_data.get("reports", []):
                year = int(raw["year"])
                item = ReportItem(
                    code=code,
                    company=str(raw.get("company", "")).strip(),
                    year=year,
                    url=str(raw["url"]).strip(),
                    source_json=path.name,
                )
                reports[(code, year)] = item
    return sorted(reports.values(), key=lambda x: (x.code, -x.year))


def new_http_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
        ),
        "Accept": "application/pdf,text/html;q=0.8,*/*;q=0.5",
    })
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def google_drive_download_url(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.hostname not in {"drive.google.com", "docs.google.com"}:
        return None
    match = re.search(r"/file/d/([^/]+)", parsed.path)
    file_id = match.group(1) if match else parse_qs(parsed.query).get("id", [None])[0]
    if not file_id:
        return None
    return f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"


def download_headers(item: ReportItem) -> dict[str, str]:
    referer = DOWNLOAD_REFERERS.get(item.code)
    return {"Referer": referer} if referer else {}


def allow_tls_fallback(url: str) -> bool:
    return (urlparse(url).hostname or "").lower() in TLS_FALLBACK_HOSTS


def request_download(
    session: requests.Session, url: str, item: ReportItem, timeout: float
) -> requests.Response:
    is_pnbs_host = allow_tls_fallback(url)
    headers = download_headers(item)
    if is_pnbs_host:
        headers.update({"Accept-Encoding": "identity", "Connection": "close"})
    kwargs = {
        "headers": headers,
        "timeout": (30.0, timeout) if is_pnbs_host else timeout,
        "stream": True,
        "allow_redirects": True,
    }
    if is_pnbs_host:
        # Domain resmi PNBS konsisten mengirim rantai CA yang tidak lengkap.
        # Batasi bypass verifikasi secara eksplisit hanya ke allowlist host.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", InsecureRequestWarning)
            return session.get(url, verify=False, **kwargs)
    return session.get(url, **kwargs)


def current_pnbs_url(
    session: requests.Session, item: ReportItem, timeout: float
) -> str | None:
    """Ambil token unduhan PNBS terbaru dari halaman laporan resmi."""
    if item.code != "PNBS":
        return None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", InsecureRequestWarning)
            response = session.get(
                PNBS_REPORT_PAGE,
                timeout=(30.0, max(timeout, 120.0)),
                verify=False,
                headers={"Accept-Encoding": "identity", "Connection": "close"},
            )
        response.raise_for_status()
        cards = re.findall(
            r'<span[^>]*>\s*(20\d{2})\s*</span>.*?'
            r'<a\s+href="([^"]*/about/download_ar/[^"]+)"',
            response.text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        for year, href in cards:
            if int(year) == item.year:
                return urljoin(PNBS_REPORT_PAGE, href.replace("&amp;", "&"))
    except requests.RequestException:
        # Token pada JSON tetap menjadi fallback bila halaman indeks sedang gagal.
        return None
    return None


def download_pdf(session: requests.Session, item: ReportItem, destination: Path, timeout: float) -> bool:
    """Kembalikan False bila sumber adalah halaman HTML/flipbook, bukan PDF."""
    refreshed_pnbs_url = current_pnbs_url(session, item, timeout)
    candidates = [refreshed_pnbs_url or item.url]
    drive_url = google_drive_download_url(item.url)
    if drive_url:
        candidates.insert(0, drive_url)

    last_error = ""
    partial = destination.with_suffix(destination.suffix + ".part")
    partial.unlink(missing_ok=True)
    for url in candidates:
        # Endpoint PNBS kadang memutus transfer chunk di tengah file dan tidak
        # mendukung HTTP Range. Karena itu unduhan harus diulang penuh.
        attempts = 20 if allow_tls_fallback(url) else 2
        for attempt in range(1, attempts + 1):
            partial.unlink(missing_ok=True)
            try:
                with request_download(session, url, item, timeout) as response:
                    response.raise_for_status()
                    iterator = response.iter_content(chunk_size=256 * 1024)
                    first = next(iterator, b"")
                    content_type = response.headers.get("content-type", "").lower()
                    if not (first.startswith(b"%PDF") or "application/pdf" in content_type):
                        last_error = f"bukan PDF ({content_type or 'tanpa content-type'})"
                        break
                    with partial.open("wb") as handle:
                        handle.write(first)
                        for chunk in iterator:
                            if chunk:
                                handle.write(chunk)

                # Transfer chunked yang terputus bisa meninggalkan awalan PDF
                # yang tampak benar. Pastikan trailer PDF juga sudah diterima.
                with partial.open("rb") as handle:
                    handle.seek(max(0, partial.stat().st_size - 4096))
                    trailer = handle.read()
                if b"%%EOF" not in trailer:
                    raise requests.exceptions.ChunkedEncodingError(
                        "transfer selesai tanpa trailer %%EOF"
                    )
                partial.replace(destination)
                return True
            except (requests.RequestException, OSError) as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                if attempt < attempts:
                    print(
                        f"    {item.code} {item.year}: transfer terputus; "
                        f"mencoba ulang {attempt + 1}/{attempts}..."
                    )
                    time.sleep(min(attempt * 2, 10))
            finally:
                partial.unlink(missing_ok=True)
    if (item.code, item.year) in EXPECTED_NON_PDF:
        return False
    raise RuntimeError(
        f"gagal mengunduh PDF {item.code} {item.year}: {last_error}. "
        "Placeholder .url tidak dibuat karena sumber ini seharusnya PDF."
    )


def authorize(credentials_path: Path, token_path: Path):
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            "Dependensi Google Drive belum terpasang. Jalankan: "
            "python -m pip install -r requirements.txt"
        ) from exc

    credentials = None
    if token_path.exists():
        credentials = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    if not credentials or not credentials.valid:
        if not credentials_path.exists():
            raise FileNotFoundError(
                f"{credentials_path} belum ada. Unduh OAuth Client tipe Desktop App "
                "dari Google Cloud Console dan simpan dengan nama credentials.json."
            )
        credential_config = json.loads(credentials_path.read_text(encoding="utf-8"))
        if "installed" not in credential_config:
            detected = "Web application" if "web" in credential_config else "tidak dikenal"
            raise ValueError(
                f"Tipe OAuth pada {credentials_path} adalah {detected}, bukan Desktop app. "
                "Buat OAuth Client baru dengan Application type = Desktop app, unduh JSON, "
                "lalu ganti credentials.json. Jangan menambahkan localhost secara manual "
                "pada Web application karena skrip memakai port lokal dinamis."
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
        credentials = flow.run_local_server(port=0, open_browser=True)
    token_path.write_text(credentials.to_json(), encoding="utf-8")
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def escape_query(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def find_child(service, parent_id: str, name: str, mime_type: str | None = None) -> dict[str, Any] | None:
    clauses = [
        f"name = '{escape_query(name)}'",
        f"'{escape_query(parent_id)}' in parents",
        "trashed = false",
    ]
    if mime_type:
        clauses.append(f"mimeType = '{escape_query(mime_type)}'")
    response = service.files().list(
        q=" and ".join(clauses),
        fields="files(id,name,mimeType,md5Checksum,size,parents)",
        pageSize=10,
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
    ).execute()
    files = response.get("files", [])
    return files[0] if files else None


def ensure_folder(service, parent_id: str, code: str) -> str:
    existing = find_child(service, parent_id, code, FOLDER_MIME)
    if existing:
        return existing["id"]
    created = service.files().create(
        body={"name": code, "mimeType": FOLDER_MIME, "parents": [parent_id]},
        fields="id,name,parents",
        supportsAllDrives=True,
    ).execute()
    return created["id"]


def upload_file(service, parent_id: str, name: str, local_path: Path, replace: bool) -> tuple[str, str]:
    from googleapiclient.http import MediaFileUpload

    existing = find_child(service, parent_id, name)
    media = MediaFileUpload(
        str(local_path),
        mimetype=mimetypes.guess_type(name)[0] or "application/octet-stream",
        resumable=True,
        chunksize=8 * 1024 * 1024,
    )
    if existing and not replace:
        return existing["id"], "skip (sudah ada)"
    if existing:
        result = service.files().update(
            fileId=existing["id"], media_body=media, fields="id,name,size,md5Checksum",
            supportsAllDrives=True,
        ).execute()
        return result["id"], "diperbarui"
    result = service.files().create(
        body={"name": name, "parents": [parent_id]}, media_body=media,
        fields="id,name,size,md5Checksum", supportsAllDrives=True,
    ).execute()
    return result["id"], "diunggah"


def upload_bytes(service, parent_id: str, name: str, data: bytes, mime_type: str, replace: bool) -> tuple[str, str]:
    from googleapiclient.http import MediaInMemoryUpload

    existing = find_child(service, parent_id, name)
    if existing and not replace:
        return existing["id"], "skip (sudah ada)"
    media = MediaInMemoryUpload(data, mimetype=mime_type, resumable=False)
    if existing:
        result = service.files().update(
            fileId=existing["id"], media_body=media, fields="id,name,size",
            supportsAllDrives=True,
        ).execute()
        return result["id"], "diperbarui"
    result = service.files().create(
        body={"name": name, "parents": [parent_id]}, media_body=media,
        fields="id,name,size", supportsAllDrives=True,
    ).execute()
    return result["id"], "diunggah"


def trash_existing_child(service, parent_id: str, name: str) -> bool:
    """Pindahkan placeholder lama ke Trash; dapat dipulihkan dari Google Drive."""
    existing = find_child(service, parent_id, name)
    if not existing:
        return False
    service.files().update(
        fileId=existing["id"],
        body={"trashed": True},
        fields="id,trashed",
        supportsAllDrives=True,
    ).execute()
    return True


def verify_target(service, folder_id: str) -> dict[str, Any]:
    from googleapiclient.errors import HttpError

    about = service.about().get(
        fields="user(displayName,emailAddress,permissionId)"
    ).execute()
    active_user = about.get("user", {})
    active_email = active_user.get("emailAddress", "akun tidak diketahui")
    try:
        metadata = service.files().get(
            fileId=folder_id,
            fields="id,name,mimeType,capabilities(canAddChildren),owners(displayName,emailAddress)",
            supportsAllDrives=True,
        ).execute()
    except HttpError as exc:
        detail = str(exc)
        if exc.resp.status == 403 and "accessNotConfigured" in detail:
            raise RuntimeError(
                "Google Drive API belum aktif pada project OAuth. Aktifkan di "
                "https://console.cloud.google.com/apis/library/drive.googleapis.com, "
                "tunggu beberapa menit, lalu jalankan ulang skrip."
            ) from exc
        raise
    if metadata.get("mimeType") != FOLDER_MIME:
        raise ValueError("ID target bukan folder Google Drive")
    if not metadata.get("capabilities", {}).get("canAddChildren", False):
        owners = metadata.get("owners", [])
        owner_text = ", ".join(
            owner.get("emailAddress") or owner.get("displayName", "") for owner in owners
        ) or "tidak ditampilkan"
        raise PermissionError(
            f"akun OAuth {active_email} tidak memiliki izin menambah file ke folder target. "
            f"Pemilik folder: {owner_text}. Berikan akses Editor kepada {active_email}, "
            "atau hapus token.json dan login ulang memakai akun yang sudah menjadi Editor."
        )
    metadata["authenticated_user"] = active_user
    return metadata


def make_manifest(code: str, reports: list[ReportItem]) -> bytes:
    payload = {
        "code": code,
        "company": reports[0].company if reports else "",
        "reports": [
            {"year": item.year, "source_url": item.url, "source_json": item.source_json}
            for item in reports
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-folder-id", default=TARGET_FOLDER_ID)
    parser.add_argument("--credentials", type=Path, default=Path("credentials.json"))
    parser.add_argument("--token", type=Path, default=Path("token.json"))
    parser.add_argument("--json", nargs="+", type=Path, default=[Path(x) for x in JSON_FILES])
    parser.add_argument("--codes", nargs="+", help="opsional: hanya kode tertentu")
    parser.add_argument("--replace", action="store_true", help="perbarui file yang namanya sudah ada")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    missing = [str(path) for path in args.json if not path.exists()]
    if missing:
        raise FileNotFoundError("JSON hasil scraping tidak ditemukan: " + ", ".join(missing))
    reports = load_reports(args.json)
    if args.codes:
        selected = {code.upper() for code in args.codes}
        reports = [item for item in reports if item.code in selected]
    grouped: dict[str, list[ReportItem]] = {}
    for item in reports:
        grouped.setdefault(item.code, []).append(item)

    print(f"Ditemukan {len(reports)} laporan dari {len(grouped)} emiten.")
    if args.dry_run:
        for code, items in grouped.items():
            print(f"{code}/: " + ", ".join(item.pdf_name for item in items))
        return 0

    service = authorize(args.credentials, args.token)
    target = verify_target(service, args.target_folder_id)
    active_email = target.get("authenticated_user", {}).get("emailAddress", "tidak diketahui")
    print(f"Akun OAuth: {active_email}")
    print(f"Target terverifikasi: {target['name']} ({target['id']})")
    http = new_http_session()
    summary: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="annual-report-upload-") as temp_dir:
        temp_root = Path(temp_dir)
        for code, items in grouped.items():
            folder_id = ensure_folder(service, args.target_folder_id, code)
            print(f"\n[{code}] folder siap")
            for item in items:
                destination = temp_root / item.pdf_name
                is_pdf = download_pdf(http, item, destination, args.timeout)
                if is_pdf:
                    file_id, status = upload_file(
                        service, folder_id, item.pdf_name, destination, args.replace
                    )
                    uploaded_name = item.pdf_name
                    if args.replace and trash_existing_child(
                        service, folder_id, item.shortcut_name
                    ):
                        status += "; placeholder .url dipindahkan ke Trash"
                else:
                    shortcut = f"[InternetShortcut]\r\nURL={item.url}\r\n".encode("utf-8")
                    file_id, status = upload_bytes(
                        service, folder_id, item.shortcut_name, shortcut,
                        "application/internet-shortcut", args.replace,
                    )
                    uploaded_name = item.shortcut_name
                print(f"  {item.year}: {status} -> {uploaded_name}")
                summary.append({
                    "code": code, "year": item.year, "name": uploaded_name,
                    "drive_file_id": file_id, "status": status, "source_url": item.url,
                })

            upload_bytes(
                service, folder_id, f"{code}_manifest.json", make_manifest(code, items),
                "application/json", args.replace,
            )

    Path("upload_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nSelesai. Ringkasan lokal: {Path('upload_summary.json').resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
