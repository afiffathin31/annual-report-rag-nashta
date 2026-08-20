# 🚀 Nashta 10-Pillars Opportunity Intelligence & AI Copilot Platform

> **Enterprise AI Assistant & Executive Decision Dashboard** untuk menganalisis potensi peluang bisnis B2B berbasis **10 Pilar Layanan Nashta** dari Laporan Tahunan (*Annual Report*) 5 tahun terakhir emiten BEI sektor **Bank Syariah** dan **Healthcare** menggunakan **True RAG Document Intelligence dengan Dual Page Anchor**.

---

## 🌟 Fitur Utama

### 1. 📊 Executive Matrix & 10-Pillars Opportunity Scorecard
* Pemetaan skor peluang bisnis (skala 0–100), tingkat kesiapan implementasi (*readiness timeline*), dan estimasi nilai proyek (*deal size*) untuk 10 Pilar Layanan Nashta:
  1. **Managed Service** (24/7 Dedicated Support, Helpdesk, NOC/SOC as a Service)
  2. **IT Hybrid Infrastructure** (Modern Datacenter, SD-WAN, Network Interconnect)
  3. **Business Application** (ERP Modernization, Core App, Workflow Automation, SIMRS/EMR)
  4. **Cyber Security** (Managed SOC 24/7, VAPT, Zero Trust, UU PDP Compliance)
  5. **Data & AI** (Enterprise Data Lakehouse, BI Dashboard, Predictive AI)
  6. **Digital Business Platform** (Mobile SuperApp, Open API Hub, Ekosistem Integrasi)
  7. **IoT & Edge Computing** (Smart Facility, Cold-Chain Tracking, Telemetry Monitoring)
  8. **Consulting & Advisory** (IT Master Plan, Enterprise Architecture, COBIT/TOGAF)
  9. **Cloud Services** (Cloud Migration AWS/GCP/Azure, Sovereign Cloud, FinOps, DRaaS)
  10. **Bootcamp & Talent Enablement** (Corporate IT Upskilling, DevSecOps & AI Academy)

### 2. 🔍 True RAG Document Intelligence & Dual Page Anchor
* **Dual Page Anchor**: Menyematkan referensi ganda pada setiap sitasi:
  $$\text{Sitasi} = \textbf{Hal. [Halaman Cetak Buku] (PDF Hal. [Halaman Viewer]) — Bab [Nama Bab]}$$
* **Verbatim Evidence Quotes**: Menampilkan kutipan kalimat asli langsung dari dokumen Laporan Tahunan resmi tanpa halusinasi.
* **Context Window Inspector**: Menyajikan paragraf lengkap di sekitar kalimat bukti untuk validasi audit yang akuntabel.

### 3. 🤖 AI Business Copilot & Instant B2B Proposal Generator
* Tanya jawab interaktif berbasis konteks RAG terhadap Laporan Tahunan emiten.
* Generator otomatis dokumen penawaran solusi B2B (*Executive Pitch Deck / Solution Proposal*) dalam format Markdown yang siap diekspor.

### 4. ☁️ Google Drive Sync & Document Vault
* Integrasi unduh folder Google Drive otomatis melalui antarmuka dashboard.
* Fast In-Memory Caching (<10ms per request).

---

## 🏛️ Cakupan Target Emiten Fokus

| No | Kode | Nama Perusahaan | Sektor / Subsektor |
|:---|:---|:---|:---|
| 1 | **BRIS** | PT Bank Syariah Indonesia (Persero) Tbk | Bank Umum Syariah |
| 2 | **BTPS** | PT Bank BTPN Syariah Tbk | Bank Umum Syariah |
| 3 | **BANK** | PT Bank Aladin Syariah Tbk | Bank Digital Syariah |
| 4 | **PNBS** | PT Bank Panin Dubai Syariah Tbk | Bank Umum Syariah |
| 5 | **KAEF** | PT Kimia Farma Tbk | Healthcare / Farmasi |
| 6 | **SIDO** | PT Industri Jamu dan Farmasi Sido Muncul Tbk | Healthcare / Farmasi & Herbal |
| 7 | **IRRA** | PT Itama Ranoraya Tbk | Healthcare / Alat Medis & Lab |
| 8 | **OMED** | PT Jayamas Medica Industri Tbk | Healthcare / Alat Medis & Distribusi |

---

## 🚀 Panduan Instalasi & Menjalankan

### 1. Kloning Repositori
```bash
git clone https://github.com/afiffathin31/annual-report-rag-nashta.git
cd annual-report-rag-nashta
```

### 2. Pasang Dependensi
```bash
pip install -r requirements.txt
```

### 3. Jalankan Server Dashboard
```bash
python run_server.py
```
Buka peramban di: **`http://127.0.0.1:8000`**

### 4. Menjalankan Pengujian Otomatis
```bash
python -m unittest discover tests -v
```

---

## 📁 Struktur Direktori

```
├── backend/
│   ├── app.py                 # FastAPI Application & REST API Endpoints
│   ├── batch_indexer.py       # PyMuPDF Dual Page Anchor & Text Extractor
│   ├── catalog.py             # Katalog emiten & Taksonomi 10 Pilar
│   ├── evidence_engine.py     # Discovery Engine kelemahan & kutipan otentik
│   ├── gdrive_sync.py         # Google Drive folder synchronizer
│   ├── rag_engine.py          # AI Copilot Assistant & Proposal Generator
│   ├── rebuild_dual_rag.py    # Skrip pembangun ulang indeks Dual-Anchor RAG
│   └── scoring_engine.py      # Algoritma scoring peluang 10 pilar & benchmarking
├── frontend/
│   ├── index.html             # Executive Single-Page Dashboard UI
│   ├── css/style.css          # Design system & dark executive theme
│   └── js/
│       ├── app.js             # State management & controller
│       ├── charts.js          # Chart.js Radar & 5-year trend visualizer
│       └── ai_assistant.js    # AI Copilot drawer & modal interaktif
├── data/
│   ├── emiten_database.json   # Basis data emiten fokus & metadata laporan
│   ├── nashta_pillars.json    # Definisi 10 pilar Nashta & keyword mapping
│   ├── documents/             # Vault dokumen PDF lokal (.gitkeep)
│   └── rag_index/             # JSON lakehouse corpus chunks (.gitkeep)
├── tests/                     # 29 Automated Test Suites (Unit & Live Integration)
├── requirements.txt           # Dependensi Python
├── run_server.py              # Server Entrypoint
└── README.md
```

---

## 📄 Lisensi
Proyek ini dilindungi di bawah lisensi MIT.
