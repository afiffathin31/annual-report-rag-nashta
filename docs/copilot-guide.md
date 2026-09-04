# Panduan AI Copilot & Pitch Proposal

Dokumen ini memandu konsultan bisnis, account executive, dan sales engineer dalam memanfaatkan **AI Business Copilot Nashta** untuk eksplorasi kebutuhan klien dan pembuatan draf penawaran otomatis.

---

## 💬 Mode Interaksi AI Copilot

AI Copilot terintegrasi di pojok kanan bawah antarmuka web dan dapat diakses kapan saja. Copilot memiliki beberapa *intent routing* cerdas:

### 1. Pertanyaan Bebas & Diagnosa Dokumen
Pengguna dapat menanyakan topik apa saja seputar inisiatif TI, kepatuhan regulasi, atau masalah operasional emiten:
- *"Apa kelemahan operasional dan risiko TI di BRIS?"*
- *"Bagaimana arsitektur cloud eksisting yang digunakan bank?"*
- *"Apa inisiatif transformasi digital terbaru yang dianggarkan?"*

### 2. Pertanyaan Spesifik Tahun (Temporal Inquiries)
Sistem secara otomatis mengisolasi dokumen sesuai tahun yang disebut:
- *"Apa ancaman cyber yang terjadi pada tahun 2024?"* $\to$ Hanya mengutip Laporan Tahunan 2024.
- *"Bagaimana kinerja TI pada laporan tahun 2023?"* $\to$ Mengutip Laporan Tahunan 2023.

### 3. Eksplorasi Pilar Solusi Spesifik
Jika pengguna ingin mendalami pilar tertentu:
- *"Jelaskan tentang Cyber Security untuk BRIS"*
- *"Bagaimana kesiapan Data & AI di perusahaan ini?"*
- *"Apakah mereka membutuhkan 24/7 Managed Services?"*

### 4. Analisis dari Tombol Kartu Bukti (*Deep-Dive Findings*)
Setiap kartu bukti pada dashboard memiliki tombol **"🔍 Analisis dengan AI Copilot"**. 
Ketika diklik, copilot langsung membedah kutipan kalimat tersebut dan menyajikan:
- Diagnosa celah operasional.
- Rekomendasi paket pilar Nashta yang relevan.
- Perkiraan nilai proyek (*deal size*) dan durasi implementasi.

---

## 📄 Pembuatan Draf Proposal Eksekutif Otomatis

Salah satu fitur paling berharga untuk tim sales adalah generator proposal otomatis. 

### Cara Mengaktifkan:
Cukup ketik salah satu perintah berikut di kolom chat AI Copilot:
- `Buat proposal`
- `Tolong buatkan proposal penawaran untuk BRIS`
- `Pitch deck`

### Struktur Proposal yang Dihasilkan:
Sistem akan memunculkan jendela modal (*modal popup*) yang menyajikan proposal bisnis formal:

1. **Executive Summary**: Profil emiten, sektor industri, dan skor kesiapan digital.
2. **Kebutuhan Mendesak & Temuan Bukti**: Diagnosa kesenjangan teknologi yang didukung bukti halaman dan bab laporan tahunan.
3. **Solusi Rekomendasi Nashta**: Solusi terintegrasi yang menggabungkan 3-5 pilar prioritas tertinggi.
4. **Tabel Estimasi Nilai Investasi**: Rincian perkiraan anggaran per pilar.
5. **Roadmap Implementasi 4 Tahap**:
   - Bulan 1: *Discovery & IT Assessment*
   - Bulan 2-3: *Solution Architecture & PoC*
   - Bulan 4-6: *Enterprise Deployment & Integration*
   - Bulan 7+: *24/7 SLA Managed Operations*
6. **Informasi Kontak Resmi Nashta**: Email dan website representatif.

---

## 🔍 Cara Membaca Footnote Sitasi

Setiap jawaban RAG dilengkapi tautan sitasi:
```
(1) "Bank memastikan ketahanan dan keamanan siber Bank secara independen..."
    — AR_2024_BRIS_Annual_Report_2024 (2024), Hal. 284
```
Pengguna dapat mengklik atau mencocokkan nomor halaman tersebut secara langsung ke berkas PDF fisik yang tersimpan di tab **"Document Vault"**.
