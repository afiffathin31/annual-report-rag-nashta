import os
from pathlib import Path
from dotenv import load_dotenv

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_PDF_DIR = DATA_DIR / "raw_pdf"
PARSED_MD_DIR = DATA_DIR / "parsed_md"
CHROMA_DB_DIR = DATA_DIR / "chromadb"
SQLITE_DB_PATH = DATA_DIR / "app.db"

# Load environment variables from .env if present
load_dotenv(BASE_DIR / ".env")

# Create directories if they do not exist
for d in [DATA_DIR, RAW_PDF_DIR, PARSED_MD_DIR, CHROMA_DB_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# API Keys & Tokens
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")
LLAMA_API_KEY = os.environ.get("LLAMA_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# Google Drive Configuration
GDRIVE_FOLDER_ID = os.environ.get("GDRIVE_FOLDER_ID", "1DEqq-6pGl898d9SwP860tFuykcmXTpKW")

# Model Configurations
MISTRAL_EMBED_MODEL = "mistral-embed"
MISTRAL_CHAT_MODEL = "mistral-medium-latest"

# Chunking & Retrieval Configs
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200
TOP_K_CHUNKS = 5

