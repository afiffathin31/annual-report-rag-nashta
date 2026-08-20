"""Rebuild True RAG Index with Dual Page Anchor and Chapter Tracking."""

from __future__ import annotations

import logging
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.batch_indexer import extract_and_index_pdf
from backend.evidence_engine import evidence_engine
from backend.scoring_engine import scoring_engine

logger = logging.getLogger("rebuild_dual_rag")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "data" / "documents"
INDEX_DIR = BASE_DIR / "data" / "rag_index"

TARGET_8_CODES = ["BRIS", "BTPS", "BANK", "PNBS", "KAEF", "SIDO", "IRRA", "OMED"]


def detect_year(filename: str) -> int:
    matches = re.findall(r"(20(?:1[89]|2[0-6]))", filename)
    return int(matches[-1]) if matches else 2024


def rebuild_all():
    logger.info("Cleaning previous rag_index files for target 8 issuers...")
    for code in TARGET_8_CODES:
        corpus_file = INDEX_DIR / f"{code}_corpus.json"
        if corpus_file.exists():
            corpus_file.unlink(missing_ok=True)
            logger.info(f"Removed old corpus: {corpus_file.name}")

    total_docs = 0
    total_chunks = 0

    for code in TARGET_8_CODES:
        code_dir = DOCS_DIR / code
        if not code_dir.exists():
            continue

        pdf_files = sorted(code_dir.glob("*.pdf"))
        logger.info(f"\n=======================================================")
        logger.info(f"Indexing {code} ({len(pdf_files)} PDF documents)")
        logger.info(f"=======================================================")

        for pdf_file in pdf_files:
            year = detect_year(pdf_file.name)
            logger.info(f"Processing [{code} {year}] from {pdf_file.name}...")
            pages, chunks = extract_and_index_pdf(pdf_file, code, year, pdf_file.name)
            total_docs += 1
            total_chunks += chunks
            logger.info(f"-> Indexed [{code} {year}]: {pages} pages, {chunks} chunks.")

    evidence_engine.clear_cache()
    scoring_engine.clear_cache()
    logger.info("\n=======================================================")
    logger.info(f"ALL TARGET 8 DUAL-ANCHOR INDEXING COMPLETED!")
    logger.info(f"Total Documents Processed: {total_docs} | Total Chunks: {total_chunks}")
    logger.info(f"=======================================================")


if __name__ == "__main__":
    rebuild_all()
