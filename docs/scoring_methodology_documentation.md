# DOKUMENTASI RESMI METODOLOGI PERHITUNGAN
## Nashta Opportunity Index & Skor 10 Pilar Solusi Teknologi
**Dokumen Referensi Sistem: Pure Evidence-Driven RAG Scoring Framework**  
**Versi:** 2.0 (Transparan, Audit-Ready, & Scalable)

---

## 1. Filosofi & Prinsip Dasar Sistem

Sistem penilaian peluang Nashta dibangun di atas prinsip **"Pure Evidence-Driven / Fakta Dokumen Murni"**.  
Tujuannya adalah menghilangkan *black-box scoring* atau asumsi subjektif, sehingga setiap angka dapat dipertanggungjawabkan langsung di hadapan *decision maker*, auditor, maupun jajaran direksi emiten.

### 3 Pilar Transparansi:
1. **100% Explainable AI**: Setiap poin kenaikan skor memiliki bukti kutipan kalimat asli, nama bab, dan nomor halaman PDF laporan tahunan resmi.
2. **Tanpa Variabel Tersembunyi**: Seluruh variabel penentu skor tercetak jelas pada kartu tampilan antarmuka (UI).
3. **Skalabilitas Penuh (Zero-Manual Setup)**: Ketika sistem membaca ribuan halaman PDF dari ratusan emiten baru di BEI, sistem menghitung sendiri skornya secara otomatis tanpa perlu penyetelan tabel manual.

---

## 2. Struktur Rumus Matematis Formal

Perhitungan dibagi menjadi dua tingkatan: **Skor Tiap Pilar Solusi (Pillar Score)** dan **Indeks Peluang Keseluruhan (Nashta Opportunity Index)**.

### A. Rumus Skor per Pilar Solusi
Untuk setiap pilar $i \in \{1, 2, \dots, 10\}$:

$$\text{SkorPilar}_i = \min\Big(98, \; \max\big(50, \; \text{Base} + (\text{EvidenceCount} \times 8) + \text{SeverityBonus}\big)\Big)$$

Di mana:
- $\text{Base} = 50$ (Titik netral operasional normal)
- $\text{EvidenceCount} =$ Jumlah bukti dokumen nyata terverifikasi di kartu ($0 \le \text{EvidenceCount} \le 5$)
- $\text{SeverityBonus} = 8$ jika berstatus **High Severity** (ada insiden/regulasi ketat), atau $0$ jika berstatus **Medium Severity**
- Batas nilai pilar berada pada rentang **50 hingga 98 poin**.

### B. Rumus Nashta Opportunity Index (Indeks Keseluruhan Emiten)
Indeks keseluruhan adalah rata-rata aritmatika terbobot dari seluruh 10 pilar Nashta:

$$\text{Nashta Opportunity Index} = \frac{\sum_{i=1}^{10} \text{SkorPilar}_i}{10}$$

---

## 3. Rincian 3 Komponen Pembentuk Skor

```
                                  SKOR PILAR (Maks 98)
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         ▼                                 ▼                                 ▼
   [ KOMPONEN 1 ]                    [ KOMPONEN 2 ]                    [ KOMPONEN 3 ]
     Base Score                      Evidence Bonus                    Severity Bonus
      (50 Poin)                    (Hingga +40 Poin)                  (0 atau +8 Poin)
         │                                 │                                 │
Titik Netral Emiten             +8 Poin per Bukti Dokumen            +8 Poin jika Dokumen
  Tbk Sehat di BEI               Nyata Terverifikasi RAG           Mencatat Insiden Kritis
```

### Komponen 1: Base Score (50 Poin)
- **Definisi**: Angka dasar untuk seluruh emiten terbuka yang terdaftar di Bursa Efek Indonesia (BEI).
- **Parameter Kelayakan ("Beroperasi Normal")**:
  1. **Listing Aktif di BEI**: Bukan entitas pailit, memiliki Dewan Komisaris, Direksi, dan Komite Audit.
  2. **Infrastruktur IT Dasar Wajib**: Memiliki sistem buku besar (*General Ledger/ERP*), email korporasi, jaringan workstation, dan sistem pelaporan elektronik OJK/BEI.
  3. **Opini Audit WTP (*Going Concern*)**: Laporan keuangan tahunan diaudit independen dan dinyatakan memiliki kelangsungan usaha yang sehat.
- **Arti Skala 50**: Rentang 0–49 diperuntukkan bagi perusahaan bermasalah/mati suri yang tidak memiliki anggaran IT. Emiten aktif dimulai dari titik netral 50.

### Komponen 2: Evidence Volume Bonus (Maksimal +40 Poin)
- Mesin RAG memindai ratusan halaman Laporan Tahunan emiten menggunakan algoritma pencarian teks terindeks (BM25) dan deduplikasi sitasi.
- Setiap kutipan fakta kalimat dokumen yang valid memberikan kontribusi **+8 poin**:
  $$\text{Evidence Bonus} = \min(\text{Jumlah Bukti Terverifikasi} \times 8, \; 40)$$
  - 1 Bukti Terverifikasi = $+8$ Poin
  - 2 Bukti Terverifikasi = $+16$ Poin
  - 3 Bukti Terverifikasi = $+24$ Poin
  - 4 Bukti Terverifikasi = $+32$ Poin
  - 5 Bukti Terverifikasi = $+40$ Poin

### Komponen 3: Severity Risk Bonus (+8 Poin atau +0 Poin)
- Sistem memindai apakah kutipan dokumen memuat kata kunci berisiko tinggi / insiden operasional, seperti:
  `["insiden", "siber", "pdp", "gangguan", "kegagalan", "kritis", "tinggi", "serangan", "kebocoran", "ransomware", "sanksi", "audit"]`
- **Ketentuan Nilai**:
  - **High Severity (+8 Poin)**: Jika terdapat riwayat insiden nyata, kegagalan sistem, kerentanan keamanan, atau kewajiban audit regulasi mendesak.
  - **Medium Severity (+0 Poin)**: Jika kutipan berfokus pada rencana peremajaan rutin, efisiensi operasional, atau ekspansi standar.

### Komponen 4: Batas Atas Cap (98 Poin)
- Nilai dibatasi maksimal di angka **98** untuk mempertahankan asas kepatuhan audit tata kelola IT (*Good Corporate Governance* / COBIT), mencerminkan bahwa tidak ada sistem TI yang 100% kebal risiko tanpa ruang peningkatan.

---

## 4. Matriks Tingkat Kematangan & Estimasi Deal Size

Berdasarkan perolehan skor pilar, sistem secara otomatis mengklasifikasikan urgensi bisnis dan estimasi nilai kontrak pengadaan proyek (*Deal Size*):

| Rentang Skor | Tingkat Kematangan (*Maturity Level*) | Urgensi Bisnis | Estimasi Kesiapan (*Readiness*) | Estimasi Nilai Proyek (*Est. Deal Range*) |
| :---: | :--- | :---: | :---: | :---: |
| **85 – 98** | **Critical / Prime Opportunity** 🔥 | **High** | Immediate (0 – 6 Bulan) | **Rp 1.5 Miliar – Rp 5.0 Miliar** |
| **70 – 84** | **High / Active Demand** ⚡ | **Medium-High** | Q1 – Q2 (6 – 12 Bulan) | **Rp 750 Juta – Rp 2.5 Miliar** |
| **55 – 69** | **Moderate / Exploring Potential** 💡 | **Medium** | Mid-Term (1 Tahun) | **Rp 350 Juta – Rp 1.2 Miliar** |
| **50 – 54** | **Emerging / Incubation** ⏳ | **Low** | Long-Term (1 – 2 Tahun) | **Rp 150 Juta – Rp 600 Juta** |

---

## 5. Studi Kasus Nyata Perhitungan BRIS (97.2)

Berikut adalah pembuktian matematis lengkap per pilar pada **PT Bank Syariah Indonesia Tbk (BRIS)**:

| No | Pilar Solusi Nashta | Base | Bukti RAG | Severity | Kalkulasi Matematis | Skor Akhir | Status Kematangan |
| :---: | :--- | :---: | :---: | :---: | :--- | :---: | :---: |
| **1** | **Managed Service** | 50 | 5 ($+40$) | High ($+8$) | $50 + 40 + 8 = 98$ | **98** | Prime Opportunity |
| **2** | **IT Hybrid Infrastructure** | 50 | 5 ($+40$) | High ($+8$) | $50 + 40 + 8 = 98$ | **98** | Prime Opportunity |
| **3** | **Business Application** | 50 | 5 ($+40$) | High ($+8$) | $50 + 40 + 8 = 98$ | **98** | Prime Opportunity |
| **4** | **Cyber Security** | 50 | 5 ($+40$) | High ($+8$) | $50 + 40 + 8 = 98$ | **98** | Prime Opportunity |
| **5** | **Data & AI** | 50 | 5 ($+40$) | High ($+8$) | $50 + 40 + 8 = 98$ | **98** | Prime Opportunity |
| **6** | **Digital Business Platform**| 50 | 5 ($+40$) | High ($+8$) | $50 + 40 + 8 = 98$ | **98** | Prime Opportunity |
| **7** | **IoT & Edge Computing** | 50 | 5 ($+40$) | Med ($+0$) | $50 + 40 + 0 = 90$ | **90** | Prime Opportunity |
| **8** | **Consulting & Advisory** | 50 | 5 ($+40$) | High ($+8$) | $50 + 40 + 8 = 98$ | **98** | Prime Opportunity |
| **9** | **Cloud Services** | 50 | 5 ($+40$) | High ($+8$) | $50 + 40 + 8 = 98$ | **98** | Prime Opportunity |
| **10**| **Bootcamp (Upskilling)** | 50 | 5 ($+40$) | High ($+8$) | $50 + 40 + 8 = 98$ | **98** | Prime Opportunity |
| | **TOTAL AKUMULASI** | | | | | **972 Poin** | |
| | **NASHTA OPPORTUNITY INDEX** | | | | $\mathbf{\frac{972}{10} = 97.2}$ | **97.2** | 🔥 **PRIME OPPORTUNITY** |

> **Catatan Analisis Pilar 7 (IoT)**: Pada Pilar 7 (IoT & Edge Computing), BRIS memperoleh skor **90** karena tidak ditemukan rekam jejak insiden fisik/kritis pada kalimat dokumen (kategori Medium / $+0$), sedangkan 9 pilar lainnya mendapatkan skor **98** karena memuat rekam jejak insiden siber, tantangan core banking, atau kepatuhan regulasi OJK (kategori High / $+8$).

---

## 6. Standar Format Bukti Dokumen (Audit Trail)

Setiap bukti yang memperkuat skor pilar wajib menyertakan atribut metadata lengkap:
1. **Index Urutan Sitasi**: (1), (2), (3), dst.
2. **Kutipan Kalimat Asli (*Evidence Quote*)**: Kalimat verbatim tanpa parafrase bebas dari laporan resmi.
3. **Halaman Fisik PDF & Halaman Cetak**: Contoh: `Hal. 283 (PDF Hal. 285)`.
4. **Nama Bab Dokumen**: Contoh: `'Tata Kelola Teknologi Informasi & GCG'`.
5. **Nama File Laporan**: Contoh: `AR_2024_BRIS_Annual_Report.pdf`.
