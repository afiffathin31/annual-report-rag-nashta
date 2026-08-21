import sys
import argparse
from pathlib import Path
import config
from src.ingestion.gdrive_downloader import GDriveDownloader
from src.ingestion.parser import DocumentParser
from src.rag.chunker import DocumentChunker
from src.rag.vector_store import VectorStoreManager
from src.rag.engine import RAGEngine

def sync_data(emitens=None, max_years=1):
    """Download annual reports from Google Drive."""
    print("=== Step 1: Syncing from Google Drive ===")
    downloader = GDriveDownloader()
    synced = downloader.sync_emitens(target_emitens=emitens, max_years_per_emiten=max_years)
    print(f"Sync complete. Total files processed: {len(synced)}")
    return synced

def index_documents():
    """Parse PDFs into Markdown and index into ChromaDB."""
    print("\n=== Step 2: Parsing & Vector Indexing ===")
    parser = DocumentParser()
    chunker = DocumentChunker()
    vector_store = VectorStoreManager()

    pdf_files = list(config.RAW_PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        # Check docs folder as fallback
        docs_dir = config.BASE_DIR / "docs"
        pdf_files = list(docs_dir.glob("*.pdf"))

    print(f"Found {len(pdf_files)} PDF files to process.")

    for pdf_path in pdf_files:
        print(f"\nProcessing: {pdf_path.name}")
        # Parse PDF -> Markdown
        md_path = parser.parse_document(pdf_path)

        # Detect emiten code from filename (e.g. SIDO_AR-2024.md -> SIDO)
        emiten_code = pdf_path.stem.split("_")[0].upper()
        if not emiten_code:
            emiten_code = "UNKNOWN"

        # Chunk Markdown
        chunks = chunker.chunk_markdown_file(md_path, emiten_code=emiten_code)

        # Index to ChromaDB
        vector_store.add_chunks(chunks)

    stats = vector_store.get_stats()
    print("\n=== Vector Store Stats ===")
    print(f"Total Chunks: {stats['total_chunks']}")
    print(f"Total Emitens Indexed: {stats['emitens_count']} ({stats['emitens']})")

def run_telegram_bot():
    """Launch the Telegram bot."""
    print("\n=== Step 3: Launching Telegram Bot ===")
    from src.bot.bot_main import run_bot
    run_bot()

def main():
    parser = argparse.ArgumentParser(description="Nashta 10-Pillars RAG & Telegram Bot")
    parser.add_argument("--sync", action="store_true", help="Download PDFs from Google Drive")
    parser.add_argument("--index", action="store_true", help="Parse PDFs and build ChromaDB index")
    parser.add_argument("--bot", action="store_true", help="Run Telegram Bot")
    parser.add_argument("--all", action="store_true", help="Run sync, index, and launch bot")
    parser.add_argument("--emitens", nargs="+", default=["SIDO", "BANK", "KLBF", "HEAL", "CARE"], help="List of emiten codes to process")

    args = parser.parse_args()

    if len(sys.argv) == 1 or args.all:
        sync_data(emitens=args.emitens)
        index_documents()
        run_telegram_bot()
    elif args.sync:
        sync_data(emitens=args.emitens)
    elif args.index:
        index_documents()
    elif args.bot:
        run_telegram_bot()

if __name__ == "__main__":
    main()
