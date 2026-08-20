"""Direct Google Drive Folder Sync & Auto-Fetcher Engine."""

from __future__ import annotations

import logging
import os
import re
import shutil
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import gdown

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.batch_indexer import extract_and_index_pdf
from backend.evidence_engine import evidence_engine
from backend.scoring_engine import scoring_engine

logger = logging.getLogger("gdrive_sync")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DOCS_DIR = DATA_DIR / "documents"
TMP_DOWNLOAD_DIR = DATA_DIR / "gdrive_temp"

DOCS_DIR.mkdir(parents=True, exist_ok=True)
TMP_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

EMITEN_CODES = [
    "BRIS", "BTPS", "BANK", "PNBS", "SILO", "MIKA", "KLBF", "SIDO",
    "KAEF", "PRDA", "IRRA", "OMED", "HEAL", "SAME", "RSGK", "SRAJ",
    "BMHS", "PRIM", "INAF", "PEHA", "TSPC", "PYFA", "DVLA", "MERK",
    "HALO", "PEVE", "MEDS", "DGNS"
]


class GDriveSyncManager:
    """Manages direct Google Drive folder syncing, automatic file classification, and immediate RAG indexing."""

    def __init__(self) -> None:
        self.is_syncing: bool = False
        self.last_sync_time: Optional[str] = None
        self.sync_logs: List[str] = []
        self.synced_files_count: int = 0
        self._lock = threading.Lock()

    def log(self, message: str) -> None:
        logger.info(message)
        timestamp = time.strftime("%H:%M:%S")
        self.sync_logs.append(f"[{timestamp}] {message}")
        if len(self.sync_logs) > 100:
            self.sync_logs.pop(0)

    def get_status(self) -> Dict[str, Any]:
        # Count total documents currently on disk
        total_pdfs = 0
        emiten_counts = {}
        for root, dirs, files in os.walk(DOCS_DIR):
            for f in files:
                if f.lower().endswith(".pdf"):
                    total_pdfs += 1
                    emiten = Path(root).name.upper()
                    emiten_counts[emiten] = emiten_counts.get(emiten, 0) + 1

        return {
            "is_syncing": self.is_syncing,
            "last_sync_time": self.last_sync_time,
            "total_documents_on_disk": total_pdfs,
            "documents_by_emiten": emiten_counts,
            "recent_logs": self.sync_logs[-15:],
        }

    def detect_emiten_and_year(self, filepath: Path) -> Tuple[str, int]:
        text = str(filepath).upper()
        # Find year (2018-2026) using flexible regex
        year_matches = re.findall(r"(20(?:1[89]|2[0-6]))", text)
        year = int(year_matches[-1]) if year_matches else 2024

        # Match known emiten codes
        for code in EMITEN_CODES:
            if re.search(rf"\b{code}\b", text):
                return code, year

        # Heuristic keywords in filename
        low = text.lower()
        if "bsi" in low or "syariah indonesia" in low:
            return "BRIS", year
        if "siloam" in low:
            return "SILO", year
        if "kalbe" in low:
            return "KLBF", year
        if "mitra keluarga" in low:
            return "MIKA", year
        if "hermina" in low:
            return "HEAL", year
        if "aladin" in low:
            return "BANK", year
        if "btpn" in low:
            return "BTPS", year
        if "prodia" in low:
            return "PRDA", year
        if "kimia farma" in low:
            return "KAEF", year
        if "sido" in low:
            return "SIDO", year
        if "itama" in low:
            return "IRRA", year
        if "onemed" in low or "jayamas" in low:
            return "OMED", year

        # Default fallback to parent folder name
        parent = filepath.parent.name.upper()
        if parent in EMITEN_CODES:
            return parent, year

        return "GENERAL", year

    def sync_google_drive_folder(self, folder_url_or_id: str) -> Dict[str, Any]:
        """Downloads all PDFs from a Google Drive folder URL or ID, organises them, and indexes them."""
        with self._lock:
            if self.is_syncing:
                return {"success": False, "error": "Proses sinkronisasi sedang berjalan. Harap tunggu."}
            self.is_syncing = True

        self.sync_logs = []
        self.log(f"Memulai sinkronisasi Google Drive: {folder_url_or_id}")

        try:
            # Clean temporary download directory
            if TMP_DOWNLOAD_DIR.exists():
                shutil.rmtree(TMP_DOWNLOAD_DIR)
            TMP_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

            self.log("Menghubungi Google Drive dan mengunduh seluruh file PDF...")

            # Extract clean folder ID or URL
            folder_url = folder_url_or_id.strip()
            if not folder_url.startswith("http"):
                # Treat as folder ID
                folder_url = f"https://drive.google.com/drive/folders/{folder_url}"

            # Download folder recursively using gdown
            downloaded_files = gdown.download_folder(
                url=folder_url,
                output=str(TMP_DOWNLOAD_DIR),
                quiet=False,
                use_cookies=False,
            )

            if not downloaded_files:
                # Try single file download fallback
                self.log("Mencoba unduh sebagai single file Google Drive...")
                single_out = gdown.download(
                    url=folder_url,
                    output=str(TMP_DOWNLOAD_DIR / "downloaded_report.pdf"),
                    quiet=False,
                    fuzzy=True,
                )
                if single_out:
                    downloaded_files = [single_out]

            self.log(f"Selesai mengunduh {len(downloaded_files) if downloaded_files else 0} file dari Google Drive.")

            # Scan and organize downloaded PDFs into data/documents/
            processed_reports = []
            for root, dirs, files in os.walk(TMP_DOWNLOAD_DIR):
                for f in files:
                    if f.lower().endswith(".pdf"):
                        src_path = Path(root) / f
                        code, year = self.detect_emiten_and_year(src_path)

                        dest_dir = DOCS_DIR / code
                        dest_dir.mkdir(parents=True, exist_ok=True)
                        dest_file = dest_dir / f"AR_{year}_{f}"

                        # Move/copy file to persistent documents directory
                        shutil.copy2(src_path, dest_file)
                        self.log(f"Mengindeks dokumen: [{code}] {f} (Tahun {year})...")

                        # Immediately extract and build True RAG chunks
                        pages, chunks = extract_and_index_pdf(dest_file, code, year, dest_file.name)
                        processed_reports.append({
                            "code": code,
                            "year": year,
                            "filename": f,
                            "pages": pages,
                            "chunks": chunks,
                        })

            # Clean temp directory
            shutil.rmtree(TMP_DOWNLOAD_DIR, ignore_errors=True)

            # Clear analysis cache so dashboard displays freshly indexed findings
            evidence_engine.clear_cache()
            scoring_engine.clear_cache()

            self.last_sync_time = time.strftime("%Y-%m-%d %H:%M:%S")
            self.synced_files_count = len(processed_reports)
            self.log(f"Sukses! Total {len(processed_reports)} Laporan Tahunan berhasil diunduh & diindeks ke dalam RAG.")

            return {
                "success": True,
                "total_downloaded": len(processed_reports),
                "reports": processed_reports,
                "sync_time": self.last_sync_time,
            }

        except Exception as e:
            err_msg = f"Gagal menyinkronkan Google Drive: {str(e)}"
            self.log(f"ERROR: {err_msg}")
            return {"success": False, "error": err_msg}

        finally:
            self.is_syncing = False


gdrive_sync_manager = GDriveSyncManager()
