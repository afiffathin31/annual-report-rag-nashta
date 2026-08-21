# 🏢 Nashta AI Advisory Assistant — 10 Pillars & 5-Year Trend RAG System

Enterprise-grade Retrieval-Augmented Generation (RAG) system dan Telegram Advisory Bot yang dirancang untuk menganalisis dokumen **Laporan Tahunan (Annual Reports)** emiten publik selama **5 tahun terakhir (2021–2025)** dan menyajikan diagnosis strategis berbasis **10 Pilar Layanan PT Nashta Global Utama**.

---

## 🌟 Fitur Utama

- **📈 Analisis Tren Masalah 5 Tahun (Executive Summary):** 
  Sintesis multi-tahun yang memetakan evolusi permasalahan emiten dari waktu ke waktu (2021–2025), akar masalah menahun (*chronic issues*), dan ancaman baru (*emerging risks*).
- **💡 Strategic 3-Phase Solution Roadmap:** 
  Rekomendasi peta jalan solusi Nashta yang *actionable* (Fase 1: Quick Win 0-6 Bln, Fase 2: Enterprise Integration 6-12 Bln, Fase 3: Next-Gen AI & Automation 1-2 Thn).
- **📊 Diagnosis 10 Pilar Layanan Nashta:** 
  Diagnosis terperinci untuk tiap pilar: *Managed Service, Hybrid Infra, Business App, Cyber Security, Data & AI, Digital Platform, IoT & Edge, Consulting & Advisory, Cloud Services, dan IT Bootcamp*.
- **📖 Sitasi Sumber yang Dapat Divalidasi (*Verifiable Citations*):** 
  Menyertakan rujukan nama dokumen resmi, nomor halaman, bab, dan kutipan asli (*direct quote*).
- **🤖 Interactive Telegram Bot ([@NashBei_bot](https://t.me/NashBei_bot)):** 
  Antarmuka responsif dengan tombol inline, navigasi pagination 1 pilar per halaman, serta fitur tanya jawab bebas (Q&A).
- **🧪 Framework Evaluasi Akurasi (RAG Triad):** 
  Pengujian otomatis berbasis *LLM-as-a-Judge* dengan skor akurasi rata-rata **88.0% (Grade A-)**.

---

## 🏗️ Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────┐
│             Multi-Year PDF Annual Reports (2021-2025)       │
└──────────────────────────────┬──────────────────────────────┘
                               │ (PyMuPDF Fast Extraction)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│          Smart Heading-Aware Markdown Chunker & Parser      │
│          (Tagged with year, page_number, section_header)    │
└──────────────────────────────┬──────────────────────────────┘
                               │ (mistral-embed)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             ChromaDB Vector Store (HNSW Index)              │
└──────────────────────────────┬──────────────────────────────┘
                               │ (Temporal Vector Retrieval)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│         Temporal Trend Engine & 10 Pillars RAG Engine       │
│                  (LLM: mistral-small-latest)                │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│    SQLite3 Cache Layer      │ │   Telegram Bot Interface    │
│  (Instant 0-Sec Responses)  │ │      (@NashBei_bot)         │
└─────────────────────────────┘ └─────────────────────────────┘
```

---

## 🛠️ Tech Stack

- **Generative AI & LLM:** [Mistral AI](https://mistral.ai/) (`mistral-small-latest`)
- **Embedding Model:** [Mistral Embed](https://docs.mistral.ai/capabilities/embeddings/) (1,024 dimensions)
- **Vector Database:** [ChromaDB](https://www.trychroma.com/) with persistent HNSW index & metadata filtering
- **PDF Extraction:** [PyMuPDF](https://pymupdf.readthedocs.io/) (`fitz`)
- **Database & Caching:** SQLite3
- **Bot Framework:** [python-telegram-bot](https://python-telegram-bot.org/) (Asyncio, HTTPX connection pooling)
- **Evaluation:** Custom automated LLM-as-a-Judge benchmark framework

---

## 📊 Hasil Evaluasi Akurasi (RAG Benchmark)

| Dimensi Evaluasi | Skor | Keterangan |
| :--- | :---: | :--- |
| **Faithfulness (Anti-Halusinasi)** | **88.8%** | Kepatuhan mutlak pada fakta laporan tahunan tanpa mengarang |
| **Citation Accuracy (Validitas Sumber)** | **91.2%** | Validitas nomor halaman, bab, dan kutipan teks dokumen |
| **Solution Relevance (Portofolio Nashta)** | **94.9%** | Kesesuaian solusi Nashta dengan masalah yang dihadapi emiten |
| **Context Relevance (Pencarian Vektor)** | **77.5%** | Relevansi potongan dokumen yang ditarik dari ChromaDB |
| **⭐ Rata-Rata Skor Akurasi Keseluruhan** | **88.0%** | **Sangat Baik (Grade A-)** |

---

## 🚀 Panduan Instalasi & Menjalankan

### 1. Kloning Repositori
```bash
git clone https://github.com/afiffathin31/annual-report-rag-nashta.git
cd annual-report-rag-nashta
```

### 2. Buat Virtual Environment & Install Dependensi
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

### 3. Konfigurasi Environment Variable
Salin `.env.example` menjadi `.env` dan isi token API Anda:
```bash
cp .env.example .env
```

Isi di dalam `.env`:
```env
MISTRAL_API_KEY=your_mistral_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GDRIVE_FOLDER_ID=1DEqq-6pGl898d9SwP860tFuykcmXTpKW
```

---

## 💻 Cara Menjalankan

### 1. Jalankan Bot Telegram
```bash
python main.py --bot
```

### 2. Sinkronisasi PDF dari Google Drive
```bash
python main.py --sync --emitens KLBF SIDO BANK CARE HEAL PDSB
```

### 3. Ekstraksi & Indexing Dokumen ke ChromaDB
```bash
python main.py --index
```

### 4. Jalankan Pengujian Akurasi (RAG Benchmark)
```bash
python -m src.evaluation.evaluator
```

---

## 📂 Struktur Repositori

```
├── config.py                 # Konfigurasi global, path, model & API keys
├── main.py                   # CLI entrypoint (--bot, --sync, --index)
├── requirements.txt          # Daftar pustaka dependensi Python
├── .env.example              # Template variabel lingkungan
├── data/
│   └── eval_report.json      # Laporan hasil benchmark akurasi RAG
└── src/
    ├── bot/
    │   ├── bot_main.py       # Handler Telegram Bot & callback routing
    │   └── keyboards.py      # Keyboard layout & inline pagination
    ├── evaluation/
    │   └── evaluator.py      # LLM-as-a-Judge benchmark evaluator
    ├── ingestion/
    │   ├── gdrive_downloader.py # Google Drive multi-year PDF downloader
    │   └── parser.py         # PyMuPDF parser to structured markdown
    └── rag/
        ├── chunker.py        # Smart markdown chunker with page tracking
        ├── engine.py         # 10 Pillars RAG analysis engine
        ├── nashta_pillars.py # Definisi 10 pilar kapabilitas Nashta
        ├── trend_engine.py   # 5-Year longitudinal trend & roadmap engine
        └── vector_store.py   # ChromaDB manager with retry logic
```

---

## 📄 Lisensi
Hak Cipta © 2026 PT Nashta Global Utama. Seluruh hak cipta dilindungi undang-undang.
