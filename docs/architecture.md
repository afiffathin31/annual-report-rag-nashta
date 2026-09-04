# Arsitektur Sistem

Dokumen ini menjelaskan arsitektur perangkat lunak, komponen inti, dan alur data *end-to-end* dari sistem **Nashta Annual Report RAG & AI Copilot**.

---

### 📐 Arsitektur Sistem RAG Terintegrasi (4-Tier Enterprise Architecture)

Sistem dibangun menggunakan arsitektur modular berlapis (*4-tier layered architecture*) berbasis backend **Python (FastAPI)** dan antarmuka web responsif berbasis **Vanilla JavaScript & Tailwind CSS** tanpa beban framework monolitik yang berat.

Diagram interaktif berikut merepresentasikan aliran pemrosesan hibrida secara terstruktur dari dokumen mentah hingga konsumsi oleh pengguna akhir:

```mermaid
flowchart TD
    %% Global Theme & Colors
    classDef inputStyle fill:#0284c7,stroke:#38bdf8,stroke-width:2px,color:#ffffff;
    classDef ingestStyle fill:#065f46,stroke:#34d399,stroke-width:2px,color:#ffffff;
    classDef routeStyle fill:#1e1b4b,stroke:#818cf8,stroke-width:2px,color:#ffffff;
    classDef storeStyle fill:#1e293b,stroke:#38bdf8,stroke-width:2px,color:#ffffff;
    classDef ragStyle fill:#1e3a8a,stroke:#60a5fa,stroke-width:2px,color:#ffffff;
    classDef llmStyle fill:#7c2d12,stroke:#fb923c,stroke-width:2px,color:#ffffff;
    classDef clientStyle fill:#14532d,stroke:#4ade80,stroke-width:2px,color:#ffffff;

    subgraph TIER1 ["TIER 1: PIPELINE INGESTI & PARSING HIBRIDA (3-WAY HYBRID INGESTION)"]
        direction TB
        PDF["📄 Berkas PDF Laporan Tahunan Resmi (2021–2025)<br/><i>(KLBF, SIDO, BANK, HEAL, CARE, PGAS, dll.)</i>"]:::inputStyle
        ROUTER["🔀 Page Profiler & Hybrid Router<br/><code>src.ingestion.hybrid_router</code>"]:::ingestStyle

        subgraph ROUTES ["Tiga Jalur Pemrosesan Dokumen (3-Way Routing)"]
            direction LR
            R_PYMUPDF["⚡ Route 1: PyMuPDF Fast<br/><i>Teks Naratif & Profil Bisnis Terurut</i>"]:::routeStyle
            R_DOCLING["📊 Route 2: Docling CUDA<br/><i>Tabel Finansial Multi-Kolom & Markdown</i>"]:::routeStyle
            R_VISION["🖼️ Route 3: Vision (Qwen-VL)<br/><i>Bagan Visual & Struktur Organisasi</i>"]:::routeStyle
        end

        CHUNKER["🧩 Table-Aware Chunker (src.rag.chunker)<br/><i>Preservasi Kolom Tabel & Tag Halaman Fisik &lt;!-- PAGE_BREAK X --&gt;</i>"]:::ingestStyle
    end

    subgraph TIER2 ["TIER 2: ARSITEKTUR PENYIMPANAN INDEKS GANDA (DUAL-INDEX STORAGE)"]
        direction LR
        VEC_STORE[("🧠 ChromaDB Vector Store<br/><i>28.702 Vektor 1024-dim | Mistral Embeddings<br/>Dense Semantic Search Multi-Tahun</i>")]:::storeStyle
        BM25_STORE[("🔍 Okapi BM25 Lexical Index<br/><i>Inverted Index In-Memory per Emiten<br/>Pencocokan Istilah Finansial & Regulasi Eksak</i>")]:::storeStyle
        SQLITE_STORE[("🗄️ SQLite3 Relational DB<br/><i>Metadata Halaman Fisik/Cetak, Bab, & Noise Filter<br/>Master Katalog 10 Pilar Nashta</i>")]:::storeStyle
    end

    subgraph TIER3 ["TIER 3: NASHTA CORE RAG ENGINE & STRATEGIC ADVISORY"]
        direction TB
        FUSION["🎯 Reciprocal Rank Fusion (RRF)<br/><i>Table Boost (+35%) • Docling Boost (+20%) • Recency-First 2025 Strategy</i>"]:::ragStyle
        GROUNDING["🛡️ Automated Citation Grounding Resolver<br/><i>Verifikasi Bab & Halaman PDF Fisik Asli • Protokol Anti-Halusinasi</i>"]:::ragStyle
        LLM_GW["☁️ Multi-Provider LLM Gateway<br/><i>Mistral Large (Chat) • Gemini • Deterministic Fallback</i>"]:::llmStyle
    end

    subgraph TIER4 ["TIER 4: ANTARMUKA PENGGUNA & KANAL PENGIRIMAN (CLIENT DELIVERY)"]
        direction LR
        DASHBOARD["💻 Web Dashboard Interaktif<br/><i>Executive Opportunity Radar • Diagnosis 10 Pilar • Estimasi Proyek</i>"]:::clientStyle
        COPILOT["🤖 AI Business Copilot<br/><i>Mode Riset Bebas • Analisis Temporal • Pitch Proposal Generator</i>"]:::clientStyle
        TELEGRAM["📱 Telegram Bot (@NashBei_bot)<br/><i>Mobile Advisory • Safe 3-Part Message Delivery (&lt;3.500 kar/part)</i>"]:::clientStyle
    end

    %% Relasi Ingestion
    PDF --> ROUTER
    ROUTER --> R_PYMUPDF
    ROUTER --> R_DOCLING
    ROUTER --> R_VISION
    R_PYMUPDF --> CHUNKER
    R_DOCLING --> CHUNKER
    R_VISION --> CHUNKER

    %% Relasi Storage Distribution
    CHUNKER -->|Vektor Dense Embeddings| VEC_STORE
    CHUNKER -->|Token Sparse Keywords| BM25_STORE
    CHUNKER -->|Metadata Halaman & Bab| SQLITE_STORE

    %% Relasi Storage ke RAG
    VEC_STORE -->|Top Semantic Chunks| FUSION
    BM25_STORE -->|Top Lexical Chunks| FUSION
    SQLITE_STORE -->|Metadata Partisi & Validasi| FUSION

    %% Relasi RAG Reasoning
    FUSION --> GROUNDING
    GROUNDING <-->|Prompt Terstruktur & Sitasi Fakta| LLM_GW

    %% Relasi Client Delivery
    GROUNDING -->|Visualisasi Skor Radar & Bukti| DASHBOARD
    GROUNDING -->|Jawaban Terstruktur & Footnote Sitasi| COPILOT
    GROUNDING -->|Executive Briefing Mobile| TELEGRAM
```

---

### 🌐 Diagram Konteks Sistem (System Context Diagram)

```mermaid
flowchart LR
    classDef actorClass fill:#1e40af,stroke:#1d4ed8,stroke-width:2px,color:#ffffff;
    classDef systemClass fill:#0284c7,stroke:#0369a1,stroke-width:3px,color:#ffffff;
    classDef extClass fill:#334155,stroke:#475569,stroke-width:2px,color:#ffffff;

    USER["👤 Tim Nashta<br/><i>(Solution Architect, Sales, Analis)</i>"]:::actorClass
    SYSTEM["🏢 Nashta Annual Report RAG & AI Copilot<br/><i>(FastAPI Backend, True RAG, 10-Pillars Engine)</i>"]:::systemClass
    GDRIVE["☁️ Google Drive & Dokumen Vault<br/><i>(PDF Laporan Tahunan 500-1200 Hal)</i>"]:::extClass
    LLM_EXT["🤖 Multi-Provider LLM Gateway<br/><i>(Mistral AI, Google Gemini, OpenAI)</i>"]:::extClass

    USER <-->|Kueri Analisis, Dialog Copilot & Radar| SYSTEM
    GDRIVE -->|Sinkronisasi Otomatis Berkas PDF| SYSTEM
    SYSTEM <-->|Prompt Terstruktur & Sitasi Footnote| LLM_EXT
```

---

## ⚡ Model Indexing Hibrida & Pipeline Penelusuran (Hybrid Indexing Pipeline)

Dokumen Laporan Tahunan memiliki karakteristik data yang heterogen: perpaduan antara **terminologi regulasi formal**, **akronim teknis industri spesifik** (seperti *SOC*, *VAPT*, *SIEM*, *DRP*, *ISO 27001*, *BI-FAST*), tabel finansial padat, serta narasi umum rencana kerja transformasi digital.

Model Indexing Hibrida Nashta membagi proses ke dalam dua fase terpadu: **Fase 1: Triple-Track Indexing** saat ingesti dokumen, dan **Fase 2: Hybrid Retrieval & Fusion Engine** saat mengeksekusi kueri pengguna.

```mermaid
flowchart TD
    %% Styling Classes
    classDef rawDoc fill:#0369a1,stroke:#38bdf8,stroke-width:2px,color:#ffffff;
    classDef trackA fill:#065f46,stroke:#34d399,stroke-width:2px,color:#ffffff;
    classDef trackB fill:#78350f,stroke:#fbbf24,stroke-width:2px,color:#ffffff;
    classDef trackC fill:#312e81,stroke:#818cf8,stroke-width:2px,color:#ffffff;
    classDef storeClass fill:#1e293b,stroke:#38bdf8,stroke-width:2px,color:#ffffff;
    classDef gateClass fill:#4c1d95,stroke:#a78bfa,stroke-width:2px,color:#ffffff;
    classDef fuseClass fill:#831843,stroke:#f472b6,stroke-width:2px,color:#ffffff;
    classDef outClass fill:#14532d,stroke:#4ade80,stroke-width:2px,color:#ffffff;

    subgraph PHASE1 ["FASE 1: PROSES TRIPLE-TRACK INDEXING (INGESTION TIME)"]
        direction TB
        RAW["📄 Potongan Paragraf Terverifikasi<br/><i>(Hasil Ekstraksi PyMuPDF & Docling)</i>"]:::rawDoc

        subgraph TRACKS ["3 Jalur Indexing Hibrida (Triple-Track Indexing)"]
            direction LR
            subgraph TR_A ["Jalur A: Structured Metadata"]
                A1["Partisi Emiten & Tahun<br/>(2021-2025)"]:::trackA
                A2["Dual-Page Indexing<br/>(Physical & Printed)"]:::trackA
                A3["Hierarki Bab Laporan<br/>(TI, GCG, Direksi)"]:::trackA
            end

            subgraph TR_B ["Jalur B: Lexical & Exact Acronym"]
                B1["Domain Tokenizer<br/>& Normalizer"]:::trackB
                B2["Kamus Akronim Teknis<br/>(SOC, VAPT, SIEM, DRP)"]:::trackB
                B3["Okapi BM25 Index<br/>(Scoring Relevansi Eksak)"]:::trackB
            end

            subgraph TR_C ["Jalur C: Semantic & Relevance"]
                C1["Bilingual Expansion<br/>(cyber ↔ siber)"]:::trackC
                C2["Contextual Booster<br/>(+3 Bab TI, +4 Cyber)"]:::trackC
                C3["Dense Vector Embeddings<br/>(1024-dim Mistral)"]:::trackC
            end
        end

        RAW --> TR_A
        RAW --> TR_B
        RAW --> TR_C

        STORE_UNIFIED[("🗄️ Penyimpanan Indeks Terpadu<br/><i>(SQLite Metadata DB + Okapi BM25 Lexical + ChromaDB Vectors)</i>")]:::storeClass

        TR_A --> STORE_UNIFIED
        TR_B --> STORE_UNIFIED
        TR_C --> STORE_UNIFIED
    end

    subgraph PHASE2 ["FASE 2: HYBRID RETRIEVAL & FUSION ENGINE (QUERY TIME)"]
        direction TB
        QUERY["🔍 Pertanyaan Pengguna<br/><i>(Contoh: 'Apa ancaman cyber BRIS pada tahun 2024?')</i>"]:::rawDoc

        subgraph ROUTING ["Temporal Query Routing"]
            direction LR
            T_GATE{"🔀 Deteksi Target Tahun?"}:::gateClass
            T_STRICT["🎯 Strict Temporal Filter<br/><code>WHERE year = target_year</code>"]:::gateClass
            T_DEFAULT["📅 Default Recency Filter<br/><code>WHERE year = max(year)</code>"]:::gateClass
        end

        QUERY --> T_GATE
        T_GATE -->|Tahun Disebutkan| T_STRICT
        T_GATE -->|Tanpa Tahun| T_DEFAULT

        subgraph EXECUTION ["Penelusuran Hibrida & Skoring Fusi"]
            direction TB
            SEARCH_MULTI["⚡ Multi-Track Search Execution<br/><i>Pencarian Simultan: BM25 Lexical + ChromaDB Semantic pada Partisi Terpilih</i>"]:::fuseClass
            
            FUSION_CALC["📐 Reciprocal Rank Fusion & Composite Scoring<br/><b>S_hybrid = S_lexical + S_semantic + Δ_chapter(+3) + Δ_cyber(+4)</b>"]:::fuseClass
            
            TOP_EVIDENCE["📋 Top-K Relevant Chunks Terverifikasi<br/><i>(Kutipan Kalimat Asli + Bab + Nomor Halaman Fisik/Cetak)</i>"]:::outClass
        end

        T_STRICT --> SEARCH_MULTI
        T_DEFAULT --> SEARCH_MULTI
        STORE_UNIFIED -.->|Akses Data Indeks Terpartisi| SEARCH_MULTI

        SEARCH_MULTI --> FUSION_CALC
        FUSION_CALC --> TOP_EVIDENCE

        LLM_OUTPUT["🤖 Context Window True RAG (LLM Gateway)<br/><i>Diagnosa Eksekutif, Rekomendasi Solusi, & Sitasi Footnote Terverifikasi</i>"]:::outClass

        TOP_EVIDENCE --> LLM_OUTPUT
    end
```


### 🔬 Rincian Tiga Jalur Indexing:

1. **Jalur A — Structured Metadata Partitioning**:
   - Memastikan pengelompokan partisi ketat (*hard partition*) berdasarkan `emiten_code` dan `year`.
   - Mengaitkan penomoran halaman ganda (`physical_page` dan `printed_page`) agar sitasi dapat langsung diverifikasi pada salinan cetak maupun PDF reader.
   - Mengindeks konteks hierarki bab (`chapter_title`) untuk memberikan konteks semantik makro.

2. **Jalur B — Lexical & Exact Acronym Indexing (BM25)**:
   - Menangani istilah teknis perbankan yang tidak boleh berubah maknanya melalui pencocokan kabur (*fuzzy*) (contoh: *BI-FAST*, *SKNBI*, *RTGS*, *PA-DSS*, *ISO 27001*).
   - Memastikan istilah-istilah sertifikasi kepatuhan dan audit memiliki presisi pencocokan eksak 100%.

3. **Jalur C — Semantic & Category Relevance Indexing**:
   - Mendukung pencocokan konsep dwibahasa (*bilingual expansion*), misalnya pengguna bertanya menggunakan istilah bahasa Inggris (*"cyber threat"*), sistem mampu mencocokkan dokumen berbahasa Indonesia (*"ancaman siber"*).
   - Melakukan pembobotan khusus (*contextual boosting*) bila paragraf berasal dari bab TI atau mengandung indikasi *pain point* operasional.

### 📐 Formula Matematis Skor Fusi Relevansi:
Setiap potongan paragraf $c$ dihitung skor relevansinya terhadap kueri $q$ menggunakan rumus komposit:

$$S_{\text{hybrid}}(c, q) = S_{\text{lexical}}(c, q) + S_{\text{semantic}}(c, q) + \Delta_{\text{chapter}}(c) + \Delta_{\text{cyber}}(c)$$

Di mana:
- $S_{\text{lexical}}(c, q)$: Skor kecocokan frekuensi istilah kata kunci kueri.
- $S_{\text{semantic}}(c, q)$: Skor relevansi kategori dan sinonim dwibahasa (*cyber* $\longleftrightarrow$ *siber*).
- $\Delta_{\text{chapter}}(c) = +3$: Tambahan poin jika chunk berasal dari bab TI, Transformasi Digital, atau Manajemen Risiko.
- $\Delta_{\text{cyber}}(c) = +4$: Tambahan poin jika chunk memuat terminologi ancaman kritis (*keamanan siber, insiden, VAPT, mitigasi, ransomware*).

---

## 🧩 Komponen Utama Sistem

### 1. Ingestion & PDF Pipeline (`backend/pdf_processor.py`, `backend/gdrive_sync.py`)
- **PyMuPDF (`fitz`)**: Mengekstrak teks dari setiap halaman PDF dengan menjaga nomor halaman fisik dokumen (*physical page*) dan nomor halaman tercetak (*printed page*).
- **Noise Gatekeeper**: Menyingkirkan teks non-substantif seperti daftar isi (*Table of Contents*), kata pengantar berulang, disclaimer auditor standar, serta header/footer nomor registrasi.
- **Chapter Identification**: Mendeteksi bab laporan tahunan (contoh: *Transformasi Digital & Strategi TI*, *Tata Kelola Perusahaan*, *Laporan Manajemen*) untuk memberikan konteks pada setiap potongan teks.

### 2. Document Store & Indexer (`backend/repository.py`, `backend/database.py`)
- **Tabel `document_chunks` (SQLite)**: Menyimpan setiap paragraf dengan metadata lengkap:
  - `chunk_id`: Identifier unik (format: `{EMITEN}_{YEAR}_p{PAGE}_{IDX}`).
  - `emiten_code`: Kode saham (contoh: `BRIS`, `BBCA`).
  - `year`: Tahun laporan (2021 s/d 2025).
  - `chapter_title`: Bab dokumen tempat teks ditemukan.
  - `printed_page` & `page_number`: Penomoran halaman laporan.
  - `raw_paragraph`: Teks asli paragraf.
  - `is_noise`: Status filter noise.

### 3. Scoring & Evidence Engine (`backend/scoring_engine.py`, `backend/evidence_engine.py`)
- Menganalisis kebutuhan emiten terhadap 10 Pilar Solusi Nashta secara deterministik.
- Menghasilkan **Nashta Opportunity Index (0-100)**, daftar prioritas solusi, estimasi nilai proyek (*deal size*), dan mengidentifikasi bukti kutipan kalimat konkret.

### 4. RAG Engine & Temporal Router (`backend/rag_engine.py`)
- Menangani dialog konsultasi dengan pengguna.
- Dilengkapi **Temporal Router**: mendeteksi tahun yang ditanyakan pengguna dan secara ketat membatasi pencarian hanya pada dokumen tahun tersebut.
- Mengirimkan konteks dokumen asli ke Generative LLM untuk merumuskan diagnosa eksekutif dan rekomendasi arsitektur.

### 5. Multi-Provider LLM Gateway (`backend/llm_provider.py`)
- Mendukung berbagai provider AI secara dinamis melalui file konfigurasi `.env`:
  - **Mistral AI**: `ministral-8b-latest` (default).
  - **Google Gemini**: `gemini-1.5-flash`.
  - **OpenAI**: `gpt-4o-mini` atau model kustom.
  - **Groq**: `llama-3.3-70b-versatile`.
  - **Ollama**: Model lokal offline (misal: `qwen2.5:7b`).
  - **Offline Fallback**: Generator berbasis aturan murni jika tidak ada koneksi internet / API key.

---

## 🔄 Alur Eksekusi Permintaan Pengguna (Runtime Flow)

Berikut urutan proses ketika pengguna mengajukan pertanyaan di AI Copilot:

```mermaid
sequenceDiagram
    autonumber
    actor User as "Pengguna (Browser)"
    participant UI as "AI Copilot UI"
    participant API as "FastAPI Server"
    participant RAG as "AIAssistantRAGEngine"
    participant Repo as "DocumentRepository (SQLite)"
    participant LLM as "Mistral AI / Gemini API"

    User->>UI: Input pertanyaan ("ancaman cyber 2024?")
    UI->>API: POST /api/chat {query, emiten_code: "BRIS"}
    API->>RAG: process_chat(query, "BRIS")
    
    RAG->>RAG: Ekstraksi tahun target: 2024
    RAG->>Repo: search_chunks(BRIS, query, target_year=2024)
    Repo->>Repo: Filter SQL: year == 2024
    Repo-->>RAG: 5 Top Chunks Dokumen 2024
    
    RAG->>RAG: Susun Prompt dengan Bukti Dokumen Asli
    RAG->>LLM: generate(prompt, system_prompt)
    LLM-->>RAG: Jawaban terstruktur dengan sitasi footnote
    
    RAG-->>API: JSON Response (reply, citations)
    API-->>UI: HTTP 200 OK
    UI->>User: Tampilkan Diagnosa, Bukti Dokumen, & Solusi
```
