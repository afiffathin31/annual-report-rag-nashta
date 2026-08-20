"""Finalize Target 8 Indexing with Clean File Organization."""

from __future__ import annotations

import logging
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.batch_indexer import extract_and_index_pdf
from backend.evidence_engine import evidence_engine
from backend.scoring_engine import scoring_engine

logger = logging.getLogger("finalize_target_8")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "data" / "documents"
TMP_DIR = BASE_DIR / "data" / "gdrive_temp"

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
    matches = re.findall(r"(20(?:1[89]|2[0-6]))", filename)
    return int(matches[-1]) if matches else 2024


def clean_and_organize():
    logger.info("Cleaning and organizing all 8 target folders...")
    for code in TARGET_8_CODES:
        code_dir = DOCS_DIR / code
        if not code_dir.exists():
            code_dir.mkdir(parents=True, exist_ok=True)

        # Remove any duplicated or misnamed files
        for f in list(code_dir.glob("*.pdf")):
            if f.name.startswith("AR_2024_") and not "2024" in f.name[8:]:
                f.unlink(missing_ok=True)
            elif f.name in ["AR_2023.pdf", "AR_2024.pdf"]:
                f.unlink(missing_ok=True)

    # Re-sync precisely from TMP_DIR
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

                    if not dest_file.exists() or dest_file.stat().st_size != src_file.stat().st_size:
                        shutil.copy2(src_file, dest_file)
                        logger.info(f"Clean organized [{file_code}] {f} -> {dest_file.name}")


def index_all():
    clean_and_organize()
    total_indexed = 0

    for code in TARGET_8_CODES:
        target_dir = DOCS_DIR / code
        if not target_dir.exists():
            continue

        pdf_files = sorted(target_dir.glob("*.pdf"))
        logger.info(f"=== Indexing {code} ({len(pdf_files)} files) ===")

        for pdf_file in pdf_files:
            year = detect_year(pdf_file.name)
            logger.info(f"Indexing [{code} {year}] from {pdf_file.name} ({pdf_file.stat().st_size / (1024*1024):.2f} MB)...")
            pages, chunks = extract_and_index_pdf(pdf_file, code, year, pdf_file.name)
            logger.info(f"-> Indexed [{code} {year}]: {pages} pages, {chunks} chunks.")
            total_indexed += 1

    evidence_engine.clear_cache()
    scoring_engine.clear_cache()
    logger.info(f"ALL 8 TARGET EMITEN INDEXING COMPLETE. Total indexed documents: {total_indexed}")


if __name__ == "__main__":
    index_all()
