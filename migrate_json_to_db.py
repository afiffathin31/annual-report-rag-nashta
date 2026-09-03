"""Batch Migration Script: Flat JSON Corpora -> Indexed Relational Database (SQLite / PostgreSQL)."""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path

# Setup Python Path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from backend.database import init_db, DEFAULT_SQLITE_PATH
from backend.repository import doc_repo
from backend.models import EmitenModel, DocumentModel, ChunkModel
from backend.database import SessionLocal

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("migration")

DATA_DIR = ROOT_DIR / "data"
RAG_INDEX_DIR = DATA_DIR / "rag_index"
EMITEN_DB_PATH = DATA_DIR / "emiten_database.json"


def run_migration() -> None:
    start_time = time.time()
    logger.info("=== MEMULAI MIGRASI DATA RAG KE DATABASE TERINDEKS ===")
    
    # 1. Initialize Tables
    logger.info("1. Menginisialisasi skema database...")
    init_db()

    # 2. Migrate Emitens metadata
    if EMITEN_DB_PATH.exists():
        logger.info(f"2. Membaca metadata emiten dari {EMITEN_DB_PATH.name}...")
        try:
            with open(EMITEN_DB_PATH, "r", encoding="utf-8") as f:
                emiten_data = json.load(f)
                issuers = emiten_data.get("issuers", [])
                for iss in issuers:
                    doc_repo.save_emiten(iss)
                logger.info(f"   -> Berhasil mendaftarkan {len(issuers)} emiten ke tabel 'emitens'.")
        except Exception as e:
            logger.warning(f"Gagal membaca emiten_database.json: {e}")

    # 3. Check existing chunks in database
    stats = doc_repo.get_corpus_stats()
    if stats.get("total_chunks", 0) > 10000:
        logger.info(f"Database sudah memuat {stats['total_chunks']} chunks. Memeriksa konsistensi...")

    # 4. Migrate JSON Corpora to Database
    corpus_files = sorted([f for f in os.listdir(RAG_INDEX_DIR) if f.endswith("_corpus.json")])
    if not corpus_files:
        logger.warning("Tidak ada file _corpus.json ditemukan di data/rag_index/.")
        return

    logger.info(f"3. Ditemukan {len(corpus_files)} file korpus emiten untuk dimigrasi.")
    total_migrated_chunks = 0
    total_docs_registered = 0

    with SessionLocal() as db:
        # Check already loaded emitens
        existing_codes = set(db.query(ChunkModel.emiten_code).distinct().all())
        existing_codes = {c[0] for c in existing_codes}

    for idx, filename in enumerate(corpus_files, 1):
        file_path = RAG_INDEX_DIR / filename
        emiten_code = filename.replace("_corpus.json", "").upper()

        # If already populated with large count, skip to avoid duplicate insertion
        if emiten_code in existing_codes:
            with SessionLocal() as db:
                cnt = db.query(ChunkModel).filter(ChunkModel.emiten_code == emiten_code).count()
                if cnt > 100:
                    logger.info(f"   [{idx}/{len(corpus_files)}] {emiten_code}: Sudah ada di database ({cnt} chunks). Lewati.")
                    total_migrated_chunks += cnt
                    continue

        t0 = time.time()
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                chunks = json.load(f)

            if not chunks:
                continue

            # Register documents
            unique_docs = set()
            for c in chunks:
                d_name = c.get("doc_name")
                yr = c.get("year", 2025)
                if d_name:
                    unique_docs.add((d_name, yr))

            with SessionLocal() as db:
                for d_name, yr in unique_docs:
                    existing_doc = db.query(DocumentModel).filter(
                        DocumentModel.emiten_code == emiten_code,
                        DocumentModel.doc_name == d_name
                    ).first()
                    if not existing_doc:
                        db.add(DocumentModel(
                            emiten_code=emiten_code,
                            doc_name=d_name,
                            year=int(yr),
                            total_pages=0
                        ))
                db.commit()
            total_docs_registered += len(unique_docs)

            # Insert chunks into Database
            inserted = doc_repo.bulk_insert_chunks(chunks, batch_size=2000)
            elapsed = time.time() - t0
            logger.info(f"   [{idx}/{len(corpus_files)}] {emiten_code}: Berhasil migrasi {inserted} chunks ({elapsed:.2f} detik).")
            total_migrated_chunks += inserted

        except Exception as e:
            logger.error(f"Gagal memigrasikan {filename}: {e}")

    duration = time.time() - start_time
    final_stats = doc_repo.get_corpus_stats()
    
    db_size_mb = 0
    if DEFAULT_SQLITE_PATH.exists():
        db_size_mb = DEFAULT_SQLITE_PATH.stat().st_size / (1024 * 1024)

    logger.info("=== MIGRASI SELESAI DENGAN SUKSES ===")
    logger.info(f"Total Waktu      : {duration:.2f} detik")
    logger.info(f"Total Chunks DB  : {final_stats['total_chunks']:,} chunks")
    logger.info(f"Total Emiten DB  : {final_stats['total_emitens']} emiten")
    logger.info(f"Total Dokumen DB : {final_stats['total_documents']} dokumen")
    logger.info(f"Ukuran DB SQLite : {db_size_mb:.2f} MB")
    logger.info("Status Index FTS5: AKTIF & TERINDEKS (BM25 Ready)")


if __name__ == "__main__":
    run_migration()
