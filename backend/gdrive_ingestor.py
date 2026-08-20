"""Google Drive and Local Drive Batch Ingestor for Annual Reports."""

from __future__ import annotations

import argparse
import logging
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.batch_indexer import extract_and_index_pdf, scan_and_index_all_local_documents
from backend.evidence_engine import evidence_engine
from backend.scoring_engine import scoring_engine

logger = logging.getLogger("gdrive_ingestor")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DOCS_DIR = DATA_DIR / "documents"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

EMITEN_CODES = [
    "BRIS", "BTPS", "BANK", "PNBS", "SILO", "MIKA", "KLBF", "SIDO",
    "KAEF", "PRDA", "IRRA", "OMED", "HEAL", "SAME", "RSGK", "SRAJ",
    "BMHS", "PRIM", "INAF", "PEHA", "TSPC", "PYFA", "DVLA", "MERK",
    "HALO", "PEVE", "MEDS", "DGNS"
]


def detect_emiten_and_year(filename_or_path: str) -> Tuple[str, int]:
    """Infers the stock code (e.g. BRIS, SILO) and year (e.g. 2024) from filename or folder path."""
    text = filename_or_path.upper()

    # Detect year (2018-2026)
    year_match = re.search(r"\b(20(?:1[89]|2[0-6]))\b", text)
    year = int(year_match.group(1)) if year_match else 2024

    # Detect emiten code
    for code in EMITEN_CODES:
        if re.search(rf"\b{code}\b", text):
            return code, year

    # Fallback to parent directory name if matching code
    parts = Path(filename_or_path).parts
    for part in parts:
        p_up = part.upper()
        if p_up in EMITEN_CODES:
            return p_up, year

    # Default fallback
    return "UNKNOWN", year


def import_from_local_folder(source_folder: Path) -> Dict[str, Any]:
    """Imports all PDF files from a local directory / Google Drive Desktop sync folder."""
    if not source_folder.exists():
        logger.error(f"Source folder not found: {source_folder}")
        return {"success": False, "error": f"Folder not found: {source_folder}"}

    imported_files = []
    logger.info(f"Scanning for PDF reports in: {source_folder}")

    for root, dirs, files in os.walk(source_folder):
        for f in files:
            if f.lower().endswith(".pdf"):
                src_path = Path(root) / f
                code, year = detect_emiten_and_year(str(src_path))
                if code == "UNKNOWN":
                    # Check if filename contains recognizable keywords
                    f_low = f.lower()
                    if "bsi" in f_low or "syariah indonesia" in f_low:
                        code = "BRIS"
                    elif "siloam" in f_low:
                        code = "SILO"
                    elif "kalbe" in f_low:
                        code = "KLBF"
                    elif "mitra keluarga" in f_low:
                        code = "MIKA"
                    elif "hermina" in f_low:
                        code = "HEAL"
                    elif "aladin" in f_low:
                        code = "BANK"
                    elif "btpn" in f_low:
                        code = "BTPS"
                    elif "prodia" in f_low:
                        code = "PRDA"
                    elif "kimia farma" in f_low:
                        code = "KAEF"
                    elif "sido" in f_low:
                        code = "SIDO"

                dest_dir = DOCS_DIR / code
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_file = dest_dir / f"AR_{year}_{f}"

                # Copy file if not already existing
                shutil.copy2(src_path, dest_file)
                logger.info(f"Imported [{code} {year}] -> {dest_file.name}")

                # Index the PDF immediately
                pages, chunks = extract_and_index_pdf(dest_file, code, year, dest_file.name)
                imported_files.append({
                    "code": code,
                    "year": year,
                    "filename": f,
                    "pages": pages,
                    "chunks": chunks,
                })

    # Clear cache to refresh scoring
    evidence_engine.clear_cache()
    scoring_engine.clear_cache()

    logger.info(f"Successfully imported and indexed {len(imported_files)} documents.")
    return {
        "success": True,
        "total_imported": len(imported_files),
        "files": imported_files,
    }


def download_from_gdrive_url(url: str, output_code: Optional[str] = None, output_year: Optional[int] = None) -> Dict[str, Any]:
    """Downloads a public Google Drive file or folder into data/documents/."""
    file_id_match = re.search(r"/d/([a-zA-Z0-9_-]+)", url) or re.search(r"id=([a-zA-Z0-9_-]+)", url)
    if not file_id_match:
        return {"success": False, "error": "Invalid Google Drive link. Could not extract file ID."}

    file_id = file_id_match.group(1)
    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"

    session = requests.Session()
    resp = session.get(download_url, stream=True)

    # Check for virus warning confirmation page
    for k, v in resp.cookies.items():
        if k.startswith("download_warning"):
            download_url = f"https://drive.google.com/uc?export=download&confirm={v}&id={file_id}"
            resp = session.get(download_url, stream=True)
            break

    code = output_code or "IMPORTED"
    year = output_year or 2024
    dest_dir = DOCS_DIR / code
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / f"AR_{year}_GDrive_{file_id[:8]}.pdf"

    with open(dest_file, "wb") as f:
        for chunk in resp.iter_content(chunk_size=32768):
            if chunk:
                f.write(chunk)

    logger.info(f"Downloaded Google Drive file to: {dest_file}")
    pages, chunks = extract_and_index_pdf(dest_file, code, year, dest_file.name)

    evidence_engine.clear_cache()
    scoring_engine.clear_cache()

    return {
        "success": True,
        "code": code,
        "year": year,
        "file": dest_file.name,
        "pages": pages,
        "chunks": chunks,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import Annual Reports from Drive / Local Folder")
    parser.add_argument("--folder", type=str, help="Path to local folder or Google Drive synced folder containing PDFs")
    parser.add_argument("--gdrive-url", type=str, help="Public Google Drive file URL")
    parser.add_argument("--code", type=str, help="Emiten stock code (e.g. BRIS, SILO)")
    parser.add_argument("--year", type=int, default=2024, help="Report fiscal year")

    args = parser.parse_args()

    if args.folder:
        res = import_from_local_folder(Path(args.folder))
        print("Import Results:", res)
    elif args.gdrive_url:
        res = download_from_gdrive_url(args.gdrive_url, output_code=args.code, output_year=args.year)
        print("Download Results:", res)
    else:
        print("Please provide --folder <path> or --gdrive-url <url>")
