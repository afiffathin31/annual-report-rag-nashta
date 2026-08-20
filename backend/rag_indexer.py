"""Document Indexer & Semantic Chunker for True RAG Annual Report Processing."""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import pypdf

logger = logging.getLogger("rag_indexer")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
INDEX_DIR = DATA_DIR / "rag_index"
DOCS_DIR = DATA_DIR / "documents"

INDEX_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)


class DocumentChunk:
    def __init__(
        self,
        chunk_id: str,
        emiten_code: str,
        doc_name: str,
        year: int,
        page_number: int,
        chapter_title: str,
        raw_paragraph: str,
        sentences: List[str],
    ) -> None:
        self.chunk_id = chunk_id
        self.emiten_code = emiten_code
        self.doc_name = doc_name
        self.year = year
        self.page_number = page_number
        self.chapter_title = chapter_title
        self.raw_paragraph = raw_paragraph
        self.sentences = sentences

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "emiten_code": self.emiten_code,
            "doc_name": self.doc_name,
            "year": self.year,
            "page_number": self.page_number,
            "chapter_title": self.chapter_title,
            "raw_paragraph": self.raw_paragraph,
            "sentences": self.sentences,
        }


class RAGIndexer:
    """Manages document chunking, indexing, and retrieval across Annual Report documents."""

    def __init__(self) -> None:
        self._load_or_build_all_indices()

    def get_index_path(self, emiten_code: str) -> Path:
        return INDEX_DIR / f"{emiten_code.upper()}_corpus.json"

    def _load_or_build_all_indices(self) -> None:
        # Pre-seed comprehensive, authentic corpora with multi-page paragraphs and exact citations
        from data.default_corpora import DEFAULT_CORPORA
        for code, chunks_data in DEFAULT_CORPORA.items():
            index_path = self.get_index_path(code)
            if not index_path.exists():
                with open(index_path, "w", encoding="utf-8") as f:
                    json.dump(chunks_data, f, indent=2, ensure_ascii=False)

    def get_chunks_for_emiten(self, emiten_code: str) -> List[Dict[str, Any]]:
        path = self.get_index_path(emiten_code)
        if not path.exists():
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading index for {emiten_code}: {e}")
            return []

    def index_pdf_file(self, pdf_path: Path, emiten_code: str, year: int, doc_name: str) -> int:
        """Parses a real PDF file page by page, splits into paragraph chunks, and indexes it."""
        if not pdf_path.exists():
            return 0

        chunks: List[Dict[str, Any]] = []
        try:
            reader = pypdf.PdfReader(str(pdf_path))
            for page_idx, page in enumerate(reader.pages):
                page_num = page_idx + 1
                text = page.extract_text() or ""
                if not text.strip():
                    continue

                # Split text into paragraphs (double newline or line breaks)
                raw_paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 40]
                if not raw_paragraphs:
                    raw_paragraphs = [p.strip() for p in text.split("\n") if len(p.strip()) > 50]

                # Detect chapter title heuristic from top lines
                first_lines = text.strip().split("\n")[:2]
                chapter_guess = "Tinjauan Laporan Tahunan"
                for line in first_lines:
                    if len(line) < 80 and ("bab" in line.lower() or "laporan" in line.lower() or "tata kelola" in line.lower() or "risiko" in line.lower()):
                        chapter_guess = line.strip()
                        break

                for p_idx, para in enumerate(raw_paragraphs):
                    # Split paragraph into sentences
                    sentences = re.split(r"(?<=[.!?])\s+", para)
                    chunk_id = f"{emiten_code}_{year}_p{page_num}_c{p_idx+1}"
                    chunk = DocumentChunk(
                        chunk_id=chunk_id,
                        emiten_code=emiten_code.upper(),
                        doc_name=doc_name,
                        year=year,
                        page_number=page_num,
                        chapter_title=chapter_guess,
                        raw_paragraph=para,
                        sentences=[s.strip() for s in sentences if len(s.strip()) > 5],
                    )
                    chunks.append(chunk.to_dict())

            # Save / Merge with existing corpus
            existing = self.get_chunks_for_emiten(emiten_code)
            # Remove duplicates by chunk_id
            combined = {c["chunk_id"]: c for c in existing}
            for c in chunks:
                combined[c["chunk_id"]] = c

            with open(self.get_index_path(emiten_code), "w", encoding="utf-8") as f:
                json.dump(list(combined.values()), f, indent=2, ensure_ascii=False)

            return len(chunks)
        except Exception as e:
            logger.error(f"Failed to index PDF {pdf_path}: {e}")
            return 0


rag_indexer = RAGIndexer()
