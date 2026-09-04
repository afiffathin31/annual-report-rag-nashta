# Nashta Annual Report RAG & AI Copilot

Selamat datang di Portal Dokumentasi Teknis resmi untuk **Nashta 10-Pillars Opportunity Radar & AI Assistant (True RAG)**.

Sistem ini adalah platform kecerdasan buatan (*Artificial Intelligence*) dan *Retrieval-Augmented Generation* (RAG) kelas enterprise yang dirancang khusus untuk membedah ribuan halaman **Laporan Tahunan (Annual Report)** resmi dari emiten yang tercatat di **Bursa Efek Indonesia (BEI)**.

---

## 🎯 Nilai Bisnis & Tujuan Sistem

Bagi jajaran direksi, *business development*, konsultan, dan *sales architect* di **PT Nashta Global Nusantara**, membaca dan menganalisis laporan tahunan setebal 500 hingga 1.000+ halaman per emiten secara manual memakan waktu berhari-hari. 

Sistem ini mentransformasikan proses tersebut menjadi instan dan akurat:

1. **Pure Evidence-Driven**: Seluruh temuan masalah, inisiatif TI, dan celah kepatuhan diselaraskan langsung dengan kutipan fakta dokumen, bab, serta nomor halaman fisik laporan tahunan asli.
2. **10-Pillars Opportunity Radar**: Menghitung skor kesiapan (*readiness*) dan potensi pasar (*deal size*) secara transparan untuk **10 Pilar Layanan Nashta**.
3. **AI Copilot Presisi Tinggi**: Asisten konsultasi interaktif yang didukung *Temporal Query Filtering* (mampu mengisolasi data tahun spesifik seperti 2024 atau 2025) serta sintesis multi-LLM (Mistral, Google Gemini, OpenAI, Groq, atau model lokal Ollama).
4. **Direct Google Drive Synchronization**: Sinkronisasi otomatis dokumen PDF laporan tahunan langsung dari Google Drive folder korporat ke dalam SQLite chunk store lokal.

---

## 🏛️ 10 Pilar Layanan Solusi Nashta

Sistem memetakan seluruh kebutuhan teknologi emiten ke dalam portofolio komprehensif Nashta:

| No | Pilar Layanan | Fokus Solusi | Estimasi Nilai Proyek |
| :---: | :--- | :--- | :--- |
| **1** | **Cyber Security** | Zero Trust Architecture, SOC 24/7, VAPT, SIEM/SOAR, Data Privacy | Rp 500 Jt - Rp 3 M+ |
| **2** | **Digital Business Platform** | Microservices Architecture, Core Banking/ERP Modernization, Open API | Rp 750 Jt - Rp 5 M+ |
| **3** | **Cloud Services** | Hybrid Cloud Migration, FinOps, Multi-cloud Infrastructure (AWS/GCP/Azure) | Rp 400 Jt - Rp 2.5 M+ |
| **4** | **Data & AI** | Enterprise Data Warehouse, Lakehouse, Predictive AI, BI & Analytics | Rp 600 Jt - Rp 3.5 M+ |
| **5** | **IT Hybrid Infrastructure** | Disaster Recovery Center (DRC), HCI, Network Modernization, High Availability | Rp 500 Jt - Rp 3 M+ |
| **6** | **Managed Service** | 24/7 NOC/SOC Operations, SLA Management, Infrastructure Monitoring | Rp 300 Jt - Rp 1.5 M/thn |
| **7** | **Digital Workplace** | Collaboration Tools, Secure Remote Work, VDI, Endpoint Security | Rp 200 Jt - Rp 1 M+ |
| **8** | **Digital Experience Platform (DXP)**| Omni-channel Mobile App, Super App, Customer Portal & Onboarding | Rp 400 Jt - Rp 2.5 M+ |
| **9** | **Bootcamp** | IT Talent Upskilling, Cybersecurity Training, Cloud Certification | Rp 150 Jt - Rp 800 Jt |
| **10**| **Consulting** | IT Master Plan (ITMP), Enterprise Architecture, ISO 27001 / NIST Audit | Rp 300 Jt - Rp 1.5 M+ |

---

## 🚀 Panduan Navigasi Dokumentasi

Dokumentasi ini disusun secara modular dengan prinsip *Docs-as-Code*:

- [**Arsitektur Sistem**](architecture.md): Membahas arsitektur teknis sistem, data flow, dan komponen perangkat lunak.
- [**Metodologi Skoring 10 Pilar**](scoring-methodology.md): Penjabaran rumus matematis formal, bobot base score, bonus evidence, serta tingkat akurasi (Match Confidence).
- [**RAG Engine & Temporal Filter**](rag-engine.md): Mekanisme pengambilan dokumen (*retrieval*), pembersihan noise, dan penanganan pertanyaan spesifik tahun.
- [**Pipeline Ingestion & GDrive**](ingestion-pipeline.md): Alur ekstraksi PDF multi-halaman dengan PyMuPDF dan sinkronisasi cloud.
- [**Panduan AI Copilot**](copilot-guide.md): Cara menggunakan antarmuka percakapan, membuat draf proposal otomatis, dan verifikasi sitasi.
- [**REST API Reference**](api-reference.md): Spesifikasi lengkap endpoint HTTP FastAPI.
