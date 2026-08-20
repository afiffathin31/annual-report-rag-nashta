"""Target 8 Emiten Pipeline Processor & Indexer."""

from __future__ import annotations

import logging
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Ensure project root in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.batch_indexer import extract_and_index_pdf
from backend.evidence_engine import evidence_engine
from backend.scoring_engine import scoring_engine

logger = logging.getLogger("process_target_8")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = DATA_DIR / "documents"
TMP_DIR = DATA_DIR / "gdrive_temp"

DOCS_DIR.mkdir(parents=True, exist_ok=True)

TARGET_8_CODES = ["BRIS", "BTPS", "BANK", "PNBS", "KAEF", "SIDO", "IRRA", "OMED"]

FOLDER_ALIAS_MAP = {
    "bank": "BANK",
    "bris": "BRIS",
    "btps": "BTPS",
    "pnbs": "PNBS",
    "kimiafarma": "KAEF",
    "kaef": "KAEF",
    "sidomuncul": "SIDO",
    "sido": "SIDO",
    "irra": "IRRA",
    "omed": "OMED",
}


def detect_year(filename: str) -> int:
    """Extracts the 4-digit fiscal year from filename (e.g. 2021, 2022, 2023, 2024, 2025)."""
    matches = re.findall(r"(20(?:1[89]|2[0-6]))", filename)
    if matches:
        # If multiple years, prefer the one after 'tahunan' or 'ar' or at the end
        return int(matches[-1])
    return 2024


def organize_and_index_target_8():
    logger.info("Scanning for Target 8 Emiten PDFs...")
    processed_count = 0

    # First copy all finished files from TMP_DIR to DOCS_DIR
    if TMP_DIR.exists():
        for root, dirs, files in os.walk(TMP_DIR):
            folder_name = Path(root).name.lower()
            code = FOLDER_ALIAS_MAP.get(folder_name)

            for f in files:
                if not f.lower().endswith(".pdf") or f.endswith(".part"):
                    continue

                file_code = code
                if not file_code:
                    f_low = f.lower()
                    for alias, target_code in FOLDER_ALIAS_MAP.items():
                        if alias in f_low:
                            file_code = target_code
                            break

                if file_code in TARGET_8_CODES:
                    year = detect_year(f)
                    src_file = Path(root) / f
                    target_dir = DOCS_DIR / file_code
                    target_dir.mkdir(parents=True, exist_ok=True)
                    dest_file = target_dir / f"AR_{year}_{f}"

                    shutil.copy2(src_file, dest_file)
                    logger.info(f"Organized [{file_code}] {f} -> {dest_file.name}")

    # Now index all files in DOCS_DIR
    for code in TARGET_8_CODES:
        target_dir = DOCS_DIR / code
        if not target_dir.exists():
            continue

        for pdf_file in target_dir.glob("*.pdf"):
            year = detect_year(pdf_file.name)
            logger.info(f"Indexing [{code} {year}] from {pdf_file.name} ({pdf_file.stat().st_size / (1024*1024):.2f} MB)...")
            pages, chunks = extract_and_index_pdf(pdf_file, code, year, pdf_file.name)
            logger.info(f"Indexed [{code} {year}] {pages} pages, {chunks} chunks.")
            processed_count += 1

    evidence_engine.clear_cache()
    scoring_engine.clear_cache()

    logger.info(f"Completed processing {processed_count} documents for Target 8 emiten.")


if __name__ == "__main__":
    organize_and_index_target_8()
