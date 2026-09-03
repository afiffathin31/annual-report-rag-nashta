"""DocumentRepository: Production-Ready Data Access Layer with Full-Text Search (FTS5 / PostgreSQL)."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional
from sqlalchemy import text, func
from sqlalchemy.orm import Session

from backend.database import SessionLocal, engine, init_db, DATABASE_URL
from backend.models import EmitenModel, DocumentModel, ChunkModel

logger = logging.getLogger("repository")

# Financial noise terms to mark chunks automatically
FINANCIAL_NOISE_TERMS = [
    "neraca keuangan", "laporan laba rugi", "arus kas konsolidasian", "liabilitas jangka pendek",
    "aset lancar", "modal disetor", "rasio car", "npl gross", "nim", "bopo", "laba bersih per saham",
    "catatan atas laporan keuangan", "fair value", "nilai wajar", "sukuk mudharabah", "surat berharga"
]


class DocumentRepository:
    """Enterprise Data Repository providing indexed retrieval and Full-Text Search."""

    def __init__(self) -> None:
        init_db()

    def get_chunks_for_emiten(
        self,
        emiten_code: str,
        year: Optional[int] = None,
        exclude_noise: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves chunks for an emiten directly from indexed database."""
        c_code = emiten_code.upper().strip()
        with SessionLocal() as db:
            query = db.query(ChunkModel).filter(ChunkModel.emiten_code == c_code)
            if year:
                query = query.filter(ChunkModel.year == year)
            if exclude_noise:
                query = query.filter(ChunkModel.is_noise == False)
            
            query = query.order_by(ChunkModel.year.desc(), ChunkModel.printed_page.asc())
            if limit:
                query = query.limit(limit)

            rows = query.all()
            return [r.to_dict() for r in rows]

    def search_chunks(
        self,
        emiten_code: str,
        query_text: str,
        top_k: int = 5,
        year_from: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """High-performance indexed full-text search with BM25 / tokenized ranking."""
        c_code = emiten_code.upper().strip()
        if not query_text or not query_text.strip():
            return self.get_chunks_for_emiten(c_code, limit=top_k)

        # 1. Try SQLite FTS5 Match if running on SQLite
        if DATABASE_URL.startswith("sqlite"):
            # Clean search terms for FTS syntax
            clean_terms = [re.sub(r"[^\w\s]", "", w).strip() for w in query_text.lower().split()]
            stop_words = {"apa", "siapa", "dimana", "kapan", "bagaimana", "mengapa", "yang", "dan", "dari", "untuk", "pada", "dengan", "ini", "itu", "saya", "anda", "kami", "mereka"}
            valid_terms = [w for w in clean_terms if len(w) > 2 and w not in stop_words]

            if valid_terms:
                fts_query_str = " OR ".join(f'"{t}"' for t in valid_terms[:8])
                sql = text("""
                    SELECT c.*
                    FROM chunk_fts f
                    JOIN document_chunks c ON c.chunk_id = f.chunk_id
                    WHERE f.emiten_code = :emiten_code
                      AND c.is_noise = 0
                      AND chunk_fts MATCH :match_query
                    ORDER BY rank
                    LIMIT :top_k;
                """)
                try:
                    with SessionLocal() as db:
                        result = db.execute(sql, {
                            "emiten_code": c_code,
                            "match_query": fts_query_str,
                            "top_k": top_k * 2
                        }).mappings().all()

                        if result:
                            # Prioritize chunks with IT relevance
                            scored = []
                            for r in result:
                                item = dict(r)
                                text_content = (item.get("raw_paragraph", "") + " " + item.get("chapter_title", "")).lower()
                                bonus = 2 if any(it_kw in text_content for it_kw in ["teknologi", "sistem", "digital", "siber", "cloud", "data"]) else 0
                                scored.append((bonus, item))
                            scored.sort(key=lambda x: x[0], reverse=True)
                            return [item[1] for item in scored[:top_k]]
                except Exception as e:
                    logger.debug(f"FTS search fallback triggered: {e}")

        # 2. Fallback: SQL Indexed Keyword Scan
        with SessionLocal() as db:
            base_q = db.query(ChunkModel).filter(
                ChunkModel.emiten_code == c_code,
                ChunkModel.is_noise == False
            )
            if year_from:
                base_q = base_q.filter(ChunkModel.year >= year_from)

            # Extract keywords
            clean_terms = [re.sub(r"[^\w\s]", "", w).strip() for w in query_text.lower().split() if len(w.strip()) > 2]
            if not clean_terms:
                return [r.to_dict() for r in base_q.order_by(ChunkModel.year.desc()).limit(top_k).all()]

            # Fetch relevant candidate pool
            candidates = base_q.order_by(ChunkModel.year.desc()).limit(500).all()
            scored_chunks = []
            for c in candidates:
                text_content = (c.raw_paragraph + " " + (c.chapter_title or "")).lower()
                matches = sum(1 for kw in clean_terms if kw in text_content)
                if matches > 0:
                    bonus = 2 if any(it_kw in text_content for it_kw in ["teknologi", "sistem", "digital", "siber", "cloud", "data"]) else 0
                    scored_chunks.append((matches + bonus, c.to_dict()))

            if scored_chunks:
                scored_chunks.sort(key=lambda x: x[0], reverse=True)
                return [item[1] for item in scored_chunks[:top_k]]

            return [c.to_dict() for c in candidates[:top_k]]

    def bulk_insert_chunks(self, chunks_data: List[Dict[str, Any]], batch_size: int = 1500) -> int:
        """Efficiently batch-inserts chunks and syncs FTS5 index."""
        if not chunks_data:
            return 0

        inserted_count = 0
        with SessionLocal() as db:
            for i in range(0, len(chunks_data), batch_size):
                batch = chunks_data[i : i + batch_size]
                chunk_objs = []
                for c in batch:
                    raw_text = c.get("raw_paragraph", "")
                    # Auto detect noise
                    text_lower = raw_text.lower()
                    is_noise = any(nt in text_lower for nt in FINANCIAL_NOISE_TERMS) or c.get("is_noise", False)

                    chunk_objs.append(
                        ChunkModel(
                            chunk_id=c.get("chunk_id", f"{c.get('emiten_code')}_{c.get('year')}_{c.get('page_number', 1)}_{i}"),
                            emiten_code=c.get("emiten_code", "").upper().strip(),
                            doc_name=c.get("doc_name", ""),
                            year=int(c.get("year", 2025)),
                            physical_page=int(c.get("physical_page", c.get("page_number", 1))),
                            printed_page=int(c.get("printed_page", c.get("page_number", 1))),
                            page_display=c.get("page_display", f"Hal. {c.get('printed_page', 1)}"),
                            page_number=int(c.get("page_number", 1)),
                            chapter_title=c.get("chapter_title", "Laporan Tahunan"),
                            raw_paragraph=raw_text,
                            is_noise=is_noise,
                        )
                    )
                db.bulk_save_objects(chunk_objs)
                db.commit()
                inserted_count += len(chunk_objs)

        # Sync SQLite FTS5 table
        if DATABASE_URL.startswith("sqlite"):
            self._sync_fts_index()

        return inserted_count

    def _sync_fts_index(self) -> None:
        """Synchronizes the SQLite FTS5 virtual table with document_chunks."""
        try:
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT OR REPLACE INTO chunk_fts(rowid, chunk_id, emiten_code, chapter_title, raw_paragraph)
                    SELECT id, chunk_id, emiten_code, chapter_title, raw_paragraph
                    FROM document_chunks;
                """))
                conn.commit()
        except Exception as e:
            logger.debug(f"FTS sync note: {e}")

    def save_emiten(self, emiten_data: Dict[str, Any]) -> None:
        """Upserts an emiten record."""
        code = emiten_data.get("code", "").upper().strip()
        if not code:
            return
        with SessionLocal() as db:
            existing = db.query(EmitenModel).filter(EmitenModel.code == code).first()
            if existing:
                existing.name = emiten_data.get("name", existing.name)
                existing.sector = emiten_data.get("sector", existing.sector)
                existing.subsector = emiten_data.get("subsector", existing.subsector)
                existing.market_cap = emiten_data.get("market_cap", existing.market_cap)
                existing.technology_stack = emiten_data.get("technology_stack", existing.technology_stack)
            else:
                db.add(
                    EmitenModel(
                        code=code,
                        name=emiten_data.get("name", code),
                        sector=emiten_data.get("sector", "Umum"),
                        subsector=emiten_data.get("subsector", "Umum"),
                        market_cap=emiten_data.get("market_cap", "-"),
                        technology_stack=emiten_data.get("technology_stack", ""),
                    )
                )
            db.commit()

    def get_corpus_stats(self) -> Dict[str, Any]:
        """Returns high-level statistics of the corpus."""
        with SessionLocal() as db:
            total_chunks = db.query(func.count(ChunkModel.id)).scalar() or 0
            total_emitens = db.query(func.count(EmitenModel.code)).scalar() or 0
            total_docs = db.query(func.count(DocumentModel.id)).scalar() or 0
            return {
                "total_chunks": total_chunks,
                "total_emitens": total_emitens,
                "total_documents": total_docs,
            }


doc_repo = DocumentRepository()
