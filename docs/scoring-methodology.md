# Metodologi Skoring 10 Pilar & Formula Matematis

Dokumen ini memuat dasar metodologi perhitungan formal untuk **Nashta Opportunity Index**, **Skor 10 Pilar Solusi Teknologi**, dan **Grafik Radar Pemetaan Emiten vs Benchmark Industri**.

Sistem ini menganut prinsip **Pure Evidence-Driven**: setiap angka yang muncul pada antarmuka pengguna dapat ditelusuri secara transparan ke bukti kutipan kalimat asli, nama bab, serta nomor halaman laporan tahunan.

---

## 📐 Formula Matematis Formal

Perhitungan dibagi menjadi dua tingkatan utama:
1. **Skor Tiap Pilar Solusi (SkorPilar)**
2. **Nashta Opportunity Index (Indeks Peluang Keseluruhan Emiten)**

---

### 1. Rumus Skor per Pilar Solusi

Untuk setiap pilar layanan **i ∈ {1, 2, ..., 10}**:

<div class="formula-box">
  <strong>SkorPilar<sub>i</sub></strong> = MIN( 98, MAX( 50, Base + (EvidenceCount × 8) + SeverityBonus ) )
</div>

$$\text{SkorPilar}_i = \min\Big(98, \; \max\big(50, \; \text{Base} + (\text{EvidenceCount} \times 8) + \text{SeverityBonus}\big)\Big)$$

#### Definisi Variabel Penentu Skor:

| Variabel | Nilai / Rentang | Keterangan |
| :--- | :---: | :--- |
| **`Base`** | **50 Poin** | Titik acuan normal bagi emiten terbuka yang terdaftar di Bursa Efek Indonesia (BEI) dengan operasional dan tata kelola yang sehat. |
| **`EvidenceCount`** | **0 s/d 5 Bukti** | Jumlah klaster kutipan fakta dokumen nyata yang berhasil diverifikasi oleh mesin RAG. Setiap bukti menyumbang **+8 Poin** (maksimal **+40 Poin**). |
| **`SeverityBonus`** | **+8 atau 0 Poin** | **+8 Poin** jika dokumen mencatat kendala operasional, downtime, risiko kepatuhan, atau insiden keamanan (*High Severity*).<br/>**0 Poin** jika dokumen hanya mencatat inisiatif rutin (*Medium Severity*). |
| **Batas Nilai** | **50 s/d 98 Poin** | Nilai pilar dikunci (*clamped*) pada batas aman antara 50 hingga 98 poin. |

---

### 2. Rumus Nashta Opportunity Index (Agregat Emiten)

Indeks peluang keseluruhan emiten merupakan rata-rata aritmatika dari seluruh 10 pilar solusi Nashta:

<div class="formula-box">
  <strong>Nashta Opportunity Index</strong> = ( SkorPilar<sub>1</sub> + SkorPilar<sub>2</sub> + ... + SkorPilar<sub>10</sub> ) / 10
</div>

$$\text{Nashta Opportunity Index} = \frac{\sum_{i=1}^{10} \text{SkorPilar}_i}{10}$$

---

## 📊 Rincian 3 Komponen Pembentuk Skor

```
                                  SKOR PILAR (Maksimal 98 Poin)
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
- **Definisi**: Angka dasar bagi setiap emiten publik yang beroperasi normal.
- **Parameter Penentu**:
  1. Emiten aktif tercatat di BEI (bukan entitas pailit atau disuspensi).
  2. Memiliki tata kelola perusahaan yang berfungsi (Dewan Komisaris, Direksi, dan Komite Audit).
  3. Memiliki anggaran belanja modal (*capex*) atau operasional (*opex*) tahunan untuk pemeliharaan teknologi informasi.

### Komponen 2: Evidence Count Bonus (0 s/d +40 Poin)
- **Definisi**: Kenaikan skor berdasarkan volume bukti riil yang ditemukan di dalam bab-bab strategis laporan tahunan.
- **Tabel Poin Bukti**:
  - **1 Bukti Dokumen**: 50 + 8 = **58 Poin**
  - **2 Bukti Dokumen**: 50 + 16 = **66 Poin**
  - **3 Bukti Dokumen**: 50 + 24 = **74 Poin**
  - **4 Bukti Dokumen**: 50 + 32 = **82 Poin**
  - **5 Bukti Dokumen**: 50 + 40 = **90 Poin** *(Batas maksimal kejenuhan bukti)*

### Komponen 3: Severity Bonus (0 atau +8 Poin)
- **Definisi**: Insentif skor ketika sistem mendeteksi adanya risiko kritis atau kelemahan sistem yang memerlukan mitigasi segera.
- **Kata Kunci Pemicu (*Trigger Keywords*)**:
  - `"insiden"`, `"gangguan"`, `"downtime"`, `"serangan"`, `"vulnerability"`, `"temuan auditor"`, `"keterbatasan"`, `"kebocoran data"`, `"sanksi regulasi"`.
- Jika terdeteksi indikator risiko tinggi ini, skor mendapat tambahan **+8 Poin** (contoh: 90 + 8 = **98 Poin**).

---

## 🎯 Metodologi Perhitungan Radar Pemetaan 10 Pilar & Benchmark Industri

Grafik **Radar Pemetaan 10 Pilar Nashta** memvisualisasikan posisi kesiapan dan kebutuhan teknologi emiten terhadap rata-rata industri BEI secara simultan.

```
                          1. Managed Service (98)
                                    ▲
      10. Bootcamp (90) ────────────┼──────────── 2. IT Hybrid Infra (92)
                                    │
    9. Cloud Services (90) ─────────┼───────── 3. Business App (86)
               ... ──── [ RATA-RATA INDUSTRI BEI ] ──── ...
                                    │
       8. Consulting (90) ──────────┼────────── 4. Cyber Security (98)
                                    │
        7. IoT & Edge (82) ─────────┼───────── 5. Data & AI (92)
                                    ▼
                          6. Digital Platform (94)
```

### Dua Lapisan Garis pada Radar:

#### 1. 🔷 Garis Solid Cyan (Skor Peluang Emiten)
- Menunjukkan skor emiten terpilih (misal: **BRIS**) pada masing-masing 10 pilar.
- Setiap sudut dihitung langsung dari formula:
  $$\text{SkorPilar}_i = \min(98, \; 50 + \text{EvidenceBonus}_i + \text{SeverityBonus}_i)$$

#### 2. ⚪ Garis Putus-Putus Abu-abu (Rata-rata Industri BEI)
- Menunjukkan nilai acuan (*benchmark*) rata-rata industri di sektor terkait.
- Dihitung sebagai rata-rata aritmatika dari seluruh emiten terindeks di sektor tersebut:
  $$\text{IndustryAvg}_i = \frac{1}{N} \sum_{k=1}^N \text{SkorPilar}_{i, k}$$
- Di backend (`backend/scoring_engine.py`), nilai ini diagregasikan secara otomatis melalui fungsi `get_sector_benchmark()`.

---

### Tabel Perbandingan Skor Radar (Contoh Kasus: BRIS vs Industri)

| No | Nama Pilar Nashta | Skor Emiten BRIS (Garis Cyan) | Rata-rata Industri BEI (Garis Abu-abu) | Opportunity Gap (Selisih) | Status Penetrasi Nashta |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **1** | **Managed Service** | **98** | 60 | **+38 Poin** | 🔥 **Prime Target** (Kebutuhan SLA 24/7) |
| **2** | **IT Hybrid Infra** | **92** | 65 | **+27 Poin** | ⚡ High Demand (Konsolidasi Server) |
| **3** | **Business App** | **86** | 70 | **+16 Poin** | ⚡ Active Demand (Integrasi Core) |
| **4** | **Cyber Security** | **98** | 75 | **+23 Poin** | 🔥 **Prime Target** (Zero Trust & SOC) |
| **5** | **Data & AI** | **92** | 68 | **+24 Poin** | ⚡ High Demand (AI BCP & Prediktif) |
| **6** | **Digital Platform** | **94** | 62 | **+32 Poin** | 🔥 **Prime Target** (Mobile & Open API) |
| **7** | **IoT & Edge** | **82** | 55 | **+27 Poin** | 💡 Modernization (Smart Branch) |
| **8** | **Consulting** | **90** | 60 | **+30 Poin** | ⚡ High Demand (IT Master Plan) |
| **9** | **Cloud Services** | **90** | 68 | **+22 Poin** | ⚡ High Demand (Hybrid Multi-Cloud) |
| **10**| **Bootcamp** | **90** | 58 | **+32 Poin** | ⚡ High Demand (Upskilling Tim IT) |

> **Cara Membaca Radar untuk Tim Sales Nashta**:
> - Sudut di mana garis solid cyan melambung jauh ke luar melebihi garis abu-abu menandakan **Opportunity Gap Tertinggi** (kebutuhan sangat mendesak dibandingkan standar pasar).
> - Pilar dengan skor **98 Poin** (*Cyber Security* & *Managed Service*) adalah **titik masuk penawaran terbaik (*lead solution*)** untuk penyusunan draf proposal kepada jajaran C-Level.

---

## ⚡ Match Confidence (Tingkat Akurasi AI)

Pada kartu temuan bukti di setiap pilar, sistem menampilkan indikator **Match Confidence**:

| Tingkat Confidence | Nilai Persentase | Syarat & Logika Penentuan |
| :--- | :---: | :--- |
| **High Confidence** | **96%** | Paragraf dokumen memuat kata kunci spesifik solusi (contoh: *SLA, NOC, 24/7, monitoring, Zero Trust*) **DAN** memuat kata pemicu kendala (*insiden, downtime, mitigasi, risiko*). |
| **Standard Confidence** | **91%** | Paragraf dokumen memuat kata kunci solusi atau transformasi digital, namun bersifat narasi inisiatif umum tanpa menyebutkan kendala operasional secara langsung. |

---

## 🏆 Klasifikasi Tingkat Peluang (Opportunity Tiers)

Berdasarkan total skor yang diperoleh, setiap pilar dipetakan ke dalam 4 tingkatan prioritas penawaran:

| Rentang Skor | Tingkat Kesiapan (*Readiness*) | Label Peluang | Strategi Penawaran Nashta |
| :---: | :--- | :--- | :--- |
| **86 - 98 Poin** | **Urgent Need / Pain Point** | 🔴 **PRIME OPPORTUNITY** | Penetrasi segera dengan proposal solusi spesifik, POC kilat, dan presentasi level Direksi/C-Level. |
| **75 - 85 Poin** | **Active Expansion** | 🟡 **HIGH OPPORTUNITY** | Pendekatan melalui *consultative selling*, audit arsitektur eksisting, dan modernisasi sistem. |
| **65 - 74 Poin** | **Planned Modernization** | 🔵 **GROWTH OPPORTUNITY** | Penawaran program *talent upskilling* / bootcamp dan *managed service support*. |
| **50 - 64 Poin** | **Stable / Baseline** | ⚪ **FOUNDATION STAGE** | Edukasi pasar, penjajakan awal, dan penyediaan benchmark industri. |

---

## 📋 Contoh Kasus Perhitungan Nyata (PT Bank Syariah Indonesia - BRIS)

### Contoh 1: Pilar Cyber Security
- **Base Score**: **50 Poin** (Emiten aktif dan sehat di BEI)
- **Bukti Terverifikasi**: **5 Klaster Bukti Dokumen** (Hal. 283, 284, 164, 244) $\implies 5 \times 8 = \mathbf{+40\text{ Poin}}$
- **Severity Risk**: **High Severity** (Mencatat kebutuhan independensi pengawasan siber & pemulihan insiden TI) $\implies \mathbf{+8\text{ Poin}}$
- **Perhitungan**:
  <div class="formula-box">
    Skor = MIN( 98, 50 + 40 + 8 ) = <strong>98 Poin (PRIME OPPORTUNITY)</strong>
  </div>

### Contoh 2: Pilar Managed Service
- **Base Score**: **50 Poin** (Emiten aktif dan sehat di BEI)
- **Bukti Terverifikasi**: **4 Klaster Bukti Dokumen** $\implies 4 \times 8 = \mathbf{+32\text{ Poin}}$
- **Severity Risk**: **High Severity** (Kebutuhan SLA operasional cabang 24/7) $\implies \mathbf{+8\text{ Poin}}$
- **Perhitungan**:
  <div class="formula-box">
    Skor = MIN( 98, 50 + 32 + 8 ) = <strong>90 Poin (PRIME OPPORTUNITY)</strong>
  </div>
