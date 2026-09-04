# REST API Reference

Dokumentasi lengkap untuk antarmuka pemrograman aplikasi (**RESTful API**) yang disediakan oleh server backend FastAPI.

- **Base URL**: `http://localhost:8000`
- **Interactive Swagger UI**: `http://localhost:8000/docs`
- **ReDoc UI**: `http://localhost:8000/redoc`

---

## 📋 Ringkasan Endpoint

| Method | Endpoint | Deskripsi |
| :--- | :--- | :--- |
| `GET` | `/api/issuers` | Daftar seluruh emiten yang terdaftar di sistem. |
| `GET` | `/api/issuers/{code}` | Detail profil satu emiten. |
| `GET` | `/api/analyze/{code}` | Analisis peluang lengkap 10 pilar dan skor emiten. |
| `POST` | `/api/chat` | Mengirim pertanyaan konsultasi ke AI Copilot (RAG). |
| `GET` | `/api/documents/{code}` | Daftar dokumen PDF yang tersedia di vault untuk emiten. |
| `GET` | `/api/documents/{code}/{year}` | Akses berkas fisik PDF laporan tahunan asli. |
| `POST` | `/api/gdrive/sync` | Memulai sinkronisasi otomatis dari Google Drive. |
| `GET` | `/docs/system` | Portal Dokumentasi Lengkap Sistem (MkDocs Material). |

---

## 🔍 Detail Spesifikasi Endpoint

### 1. Daftar Emiten (`GET /api/issuers`)
Mengembalikan seluruh emiten yang telah diindeks beserta ringkasan skor dan status laporan tahunan.

#### Response `200 OK`:
```json
[
  {
    "code": "BRIS",
    "name": "PT Bank Syariah Indonesia (Persero) Tbk",
    "sector": "Keuangan",
    "subsector": "Perbankan Syariah",
    "overall_score": 88,
    "top_pillar": "Cyber Security",
    "annual_reports_count": 5
  }
]
```

---

### 2. Analisis 10 Pilar Emiten (`GET /api/analyze/{code}`)
Mengembalikan hasil komputasi analitik lengkap untuk satu emiten:

- Skor agregat (*Nashta Opportunity Index*).
- Skor per pilar ($1 \dots 10$) beserta status *readiness*.
- Bukti kutipan dokumen terverifikasi (*supporting citations*).
- Estimasi nilai proyek (*deal range*).

#### Parameters:
- `code` *(path, required)*: Kode emiten (contoh: `BRIS`, `BBCA`).

#### Contoh Response:
```json
{
  "issuer": {
    "code": "BRIS",
    "name": "PT Bank Syariah Indonesia (Persero) Tbk",
    "sector": "Keuangan"
  },
  "overall_opportunity_score": 88,
  "top_priority_pillars": [
    {
      "pillar_id": 1,
      "pillar_name": "Cyber Security",
      "score": 98,
      "maturity_level": "Prime Opportunity",
      "estimated_deal_range": "Rp 500 Jt - Rp 3 M+",
      "proposed_solution": "Nashta Cyber Defense Platform (SOC & Zero Trust)"
    }
  ],
  "pillar_scores": [ ... ],
  "strategic_recommendations": [ ... ]
}
```

---

### 3. AI Copilot Chat (`POST /api/chat`)
Mengirim pertanyaan pengguna untuk dijawab oleh AI Business Copilot berbasis RAG Laporan Tahunan.

#### Request Body:
```json
{
  "query": "Apa ancaman cyber yang terjadi pada tahun 2024?",
  "emiten_code": "BRIS"
}
```

#### Response `200 OK`:
```json
{
  "emiten_code": "BRIS",
  "title": "AI Copilot (MISTRAL) - BRIS",
  "reply": "### 🔍 Diagnosa Utama dari Laporan Tahunan BRIS 2024...\n\n(1) \"BSI menerapkan kebijakan pengawasan keamanan siber...\" — AR_2024_BRIS_Annual_Report_2024 (2024), Hal. 284...",
  "citations": [
    {
      "citation_index": 1,
      "title": "Transformasi Digital & Strategi TI",
      "doc_name": "AR_2024_BRIS_Annual_Report_2024.pdf",
      "page_display": "Hal. 284 (PDF Hal. 286)",
      "page_number": 284,
      "year": 2024,
      "quote": "BSI menerapkan semua kebijakan dan standar prosedur TI di Bank..."
    }
  ],
  "llm_provider": {
    "provider": "mistral",
    "model": "ministral-8b-latest",
    "has_key": true
  }
}
```

---

### 4. Daftar Dokumen Vault (`GET /api/documents/{code}`)
Mengembalikan daftar dokumen PDF resmi yang tersimpan di server lokal untuk emiten terkait.

#### Response `200 OK`:
```json
{
  "code": "BRIS",
  "count": 5,
  "documents": [
    {
      "filename": "AR_2024_BRIS_Annual_Report_2024.pdf",
      "year": 2024,
      "size_mb": 42.15,
      "view_url": "/api/documents/BRIS/2024",
      "download_url": "/api/documents/BRIS/2024"
    }
  ]
}
```

---

### 5. Google Drive Sync (`POST /api/gdrive/sync`)
Memicu proses background task untuk sinkronisasi dokumen PDF dari folder Google Drive publik.

#### Request Body:
```json
{
  "folder_url": "https://drive.google.com/drive/folders/1ABCXYZ..."
}
```

#### Response `200 OK`:
```json
{
  "status": "success",
  "message": "Sinkronisasi Google Drive telah dimulai di background.",
  "folder_url": "https://drive.google.com/drive/folders/1ABCXYZ..."
}
```
