"""High-Performance Batch PDF Parser & True RAG Indexer with Dual Page Anchor."""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.catalog import catalog_manager

logger = logging.getLogger("batch_indexer")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DOCS_DIR = DATA_DIR / "documents"
INDEX_DIR = DATA_DIR / "rag_index"

DOCS_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)

CHAPTER_PATTERNS = [
    (r"(?i)(tata\s+kelola|good\s+corporate\s+governance|gcg|pengawasan\s+ti|komite\s+audit)", "Tata Kelola Teknologi Informasi & GCG"),
    (r"(?i)(manajemen\s+risiko|profil\s+risiko|risk\s+management|mitigasi\s+risiko)", "Laporan Profil & Manajemen Risiko"),
    (r"(?i)(tinjauan\s+operasional|tinjauan\s+bisnis|analisis\s+dan\s+pembahasan\s+manajemen|md&a)", "Tinjauan Operasional & Infrastruktur Bisnis"),
    (r"(?i)(transformasi\s+digital|strategi\s+ti|teknologi\s+informasi|digital\s+banking)", "Transformasi Digital & Strategi TI"),
    (r"(?i)(sumber\s+daya\s+manusia|human\s+capital|pengembangan\s+sdm|talenta)", "Pengembangan SDM & Talenta"),
    (r"(?i)(laporan\s+direksi|laporan\s+dewan\s+komisaris|sambutan\s+direktur)", "Laporan Dewan Direksi & Komisaris"),
    (r"(?i)(laporan\s+keuangan|neraca|laba\s+rugi|catatan\s+atas\s+laporan\s+keuangan)", "Laporan Keuangan & Akuntansi"),
]


def detect_printed_page(page: pymupdf.Page, physical_page: int, total_pages: int, prev_printed: Optional[int] = None) -> Optional[int]:
    """Detects printed page number strictly from true margins with sequential continuity."""
    rect = page.rect
    blocks = page.get_text("blocks")
    # Strict margins: top 10% or bottom 10% only (avoiding body text & tables)
    edge_blocks = [b for b in blocks if (b[1] >= rect.height * 0.90 or b[3] <= rect.height * 0.10)]

    candidates = []
    for b in edge_blocks:
        txt = b[4].strip()
        # Pattern 1: 'LAPORAN TAHUNAN 2025 11' or 'Annual Report 2023 | 45'
        m = re.search(r"(?i)(?:laporan\s+tahunan|annual\s+report)\s+\d{4}\s*[:\|\-]?\s*(\d{1,4})", txt)
        if m:
            candidates.append((int(m.group(1)), 10))

        # Pattern 2: '... TBK 10' or '... TBK\n10'
        m = re.search(r"(?i)(?:tbk|bank|persero)\s*[:\|\-]?\s*(\d{1,4})$", txt)
        if m:
            candidates.append((int(m.group(1)), 8))

        # Pattern 3: Number with pipe delimiter '... | 461' or '461 | ...'
        m = re.search(r"\|\s*(\d{1,4})|(\d{1,4})\s*\|", txt)
        if m:
            val = m.group(1) or m.group(2)
            candidates.append((int(val), 7))

        # Pattern 4: Standalone number line in footer/header
        lines = [l.strip() for l in txt.split("\n") if l.strip()]
        for l in lines:
            if l.isdigit() and 1 <= len(l) <= 4:
                candidates.append((int(l), 5))

    if not candidates:
        return None

    expected = prev_printed + 1 if prev_printed is not None else physical_page

    # Filter candidates within +/- 35 of physical page
    valid = [c for c in candidates if abs(c[0] - physical_page) <= 40 and 1 <= c[0] <= total_pages + 50]
    if not valid:
        return None

    # Sort by priority desc, then closeness to expected
    valid.sort(key=lambda x: (-x[1], abs(x[0] - expected)))
    return valid[0][0]


def detect_chapter(page_text: str, header_blocks: List[str], current_chapter: str) -> str:
    """Identifies the chapter title from header blocks or leading page text."""
    combined_header = " ".join(header_blocks).strip()
    
    # If combined header is a global navbar containing 2 or more chapter section names, inspect page body instead
    navbar_matches = sum(1 for p, _ in CHAPTER_PATTERNS if re.search(p, combined_header))
    if navbar_matches > 1:
        target_search = page_text[:400]
    else:
        target_search = combined_header if len(combined_header) > 5 else page_text[:400]

    for pattern, title in CHAPTER_PATTERNS:
        if re.search(pattern, target_search):
            return title

    return current_chapter


def extract_and_index_pdf(pdf_path: Path, emiten_code: str, year: int, doc_name: str) -> Tuple[int, int]:
    """Extracts text per page using PyMuPDF with Dual Page Anchor and Chapter Tracking."""
    if not pdf_path.exists():
        logger.warning(f"File not found: {pdf_path}")
        return 0, 0

    logger.info(f"Extracting [{emiten_code}] {doc_name} ({pdf_path.stat().st_size / (1024*1024):.2f} MB)...")
    chunks: List[Dict[str, Any]] = []

    try:
        doc = pymupdf.open(str(pdf_path))
        total_pages = len(doc)
        current_chapter = "Laporan Tahunan"
        prev_printed: Optional[int] = None
        last_offset = 0  # physical_page - printed_page

        for page_idx in range(total_pages):
            physical_page = page_idx + 1
            if physical_page % 100 == 0 or physical_page == total_pages:
                logger.info(f"[{emiten_code}] Processed {physical_page}/{total_pages} pages...")

            page = doc[page_idx]
            rect = page.rect
            blocks = page.get_text("blocks")

            # Extract header and footer blocks
            header_blocks = [b[4].strip() for b in blocks if b[3] < rect.height * 0.10]
            
            # Detect printed page number with sequential tracker
            detected_printed = detect_printed_page(page, physical_page, total_pages, prev_printed)
            if detected_printed is not None:
                printed_page = detected_printed
                prev_printed = printed_page
                last_offset = physical_page - printed_page
            else:
                printed_page = max(1, physical_page - last_offset)

            # Format Dual Page Anchor
            if printed_page == physical_page:
                page_display = f"Hal. {printed_page}"
            else:
                page_display = f"Hal. {printed_page} (PDF Hal. {physical_page})"

            full_text = page.get_text("text") or ""
            full_text = " ".join(full_text.split())
            if len(full_text) < 40:
                continue

            current_chapter = detect_chapter(full_text, header_blocks, current_chapter)

            # Split paragraphs
            sentences = re.split(r"(?<=[.!?])\s+", full_text)
            if len(sentences) >= 2:
                for s_idx in range(0, len(sentences), 2):
                    chunk_sentences = sentences[s_idx : s_idx + 3]
                    para_text = " ".join(chunk_sentences).strip()
                    if len(para_text) > 60:
                        chunk_id = f"{emiten_code}_{year}_p{printed_page}_c{s_idx+1}"
                        chunks.append({
                            "chunk_id": chunk_id,
                            "emiten_code": emiten_code.upper(),
                            "doc_name": doc_name,
                            "year": year,
                            "physical_page": physical_page,
                            "printed_page": printed_page,
                            "page_display": page_display,
                            "page_number": printed_page,
                            "chapter_title": current_chapter,
                            "raw_paragraph": para_text,
                            "sentences": [s.strip() for s in chunk_sentences if len(s.strip()) > 10],
                        })

        # Save into RAG index corpus
        out_path = INDEX_DIR / f"{emiten_code.upper()}_corpus.json"
        existing_chunks = []
        if out_path.exists():
            try:
                with open(out_path, "r", encoding="utf-8") as f:
                    existing_chunks = json.load(f)
            except Exception:
                existing_chunks = []

        chunk_dict = {c["chunk_id"]: c for c in existing_chunks}
        for c in chunks:
            chunk_dict[c["chunk_id"]] = c

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(list(chunk_dict.values()), f, indent=2, ensure_ascii=False)

        logger.info(f"[{emiten_code}] Dual-Anchor indexing complete: {len(chunks)} chunks created across {total_pages} pages.")
        return total_pages, len(chunks)

    except Exception as e:
        logger.error(f"Error processing {pdf_path}: {e}")
        return 0, 0


def scan_and_index_all_local_documents() -> Dict[str, Any]:
    """Scans data/documents/ recursively and indexes all available PDFs with Dual Page Anchor."""
    results = {}
    for root, dirs, files in os.walk(DOCS_DIR):
        for file in files:
            if file.lower().endswith(".pdf"):
                full_path = Path(root) / file
                parent_name = Path(root).name.upper()
                emiten_code = parent_name if parent_name != "DOCUMENTS" else file.split("_")[0].upper()
                year_matches = re.findall(r"(20(?:1[89]|2[0-6]))", file)
                year = int(year_matches[-1]) if year_matches else 2024

                pages, chunk_count = extract_and_index_pdf(full_path, emiten_code, year, file)
                results[f"{emiten_code}_{year}"] = {
                    "doc_name": file,
                    "pages": pages,
                    "chunks": chunk_count,
                    "emiten_code": emiten_code,
                    "year": year,
                }
    return results
