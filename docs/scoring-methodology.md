# Metodologi Skoring 10 Pilar & Formula Matematis

Dokumen ini memuat dasar metodologi perhitungan formal untuk **Nashta Opportunity Index** dan **Skor 10 Pilar Solusi Teknologi**.

Sistem ini menganut prinsip **Pure Evidence-Driven**: setiap angka yang muncul pada antarmuka pengguna dapat ditelusuri secara transparan ke bukti kutipan kalimat asli, nama bab, serta nomor halaman laporan tahunan.

---

## 📐 Formula Matematis Formal

Perhitungan dibagi menjadi dua tingkatan utama:

1. **Skor Tiap Pilar Solusi ($\text{SkorPilar}_i$)**
2. **Nashta Opportunity Index (Indeks Peluang Keseluruhan Emiten)**

### 1. Rumus Skor per Pilar Solusi

Untuk setiap pilar layanan $i \in \{1, 2, \dots, 10\}$:

$$\text{SkorPilar}_i = \min\Big(98, \; \max\big(50, \; \text{Base} + (\text{EvidenceCount} \times 8) + \text{SeverityBonus}\big)\Big)$$

Di mana variabel penentu skor:

- **$\text{Base} = 50$**: Titik acuan normal bagi emiten terbuka yang terdaftar di Bursa Efek Indonesia (BEI).
- **$\text{EvidenceCount}$**: Jumlah klaster kutipan fakta dokumen nyata yang berhasil diverifikasi oleh mesin RAG ($0 \le \text{EvidenceCount} \le 5$). Setiap bukti memberikan kontribusi $+8$ poin.
- **$\text{SeverityBonus}$**:
  - $+8$ poin jika terdeteksi indikator kendala operasional, downtime, risiko kepatuhan regulasi, atau insiden keamanan (*High Severity*).
  - $0$ poin jika dokumen hanya mencatat inisiatif rutin tanpa kendala eksplisit (*Medium Severity*).
- **Batas Nilai**: Skor setiap pilar dibatasi secara aman pada interval $[50, 98]$ poin.

---

### 2. Rumus Nashta Opportunity Index (Agregat Emiten)

Indeks peluang keseluruhan emiten merupakan rata-rata aritmatika dari seluruh 10 pilar solusi Nashta:

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

### Komponen 2: Evidence Count Bonus ($0$ s/d $+40$ Poin)
- **Definisi**: Kenaikan skor berdasarkan volume bukti riil yang ditemukan di dalam bab-bab strategis laporan tahunan.
- **Skala Perhitungan**:
  - $1 \text{ Bukti} = +8\text{ Poin}$
  - $2 \text{ Bukti} = +16\text{ Poin}$
  - $3 \text{ Bukti} = +24\text{ Poin}$
  - $4 \text{ Bukti} = +32\text{ Poin}$
  - $5 \text{ Bukti} = +40\text{ Poin}$ (Batas maksimal kejenuhan bukti)

### Komponen 3: Severity Bonus ($0$ atau $+8$ Poin)
- **Definisi**: Insentif skor ketika sistem mendeteksi adanya risiko kritis atau kelemahan sistem yang memerlukan mitigasi segera.
- **Pemicu Deteksi (Trigger Keywords)**:
  - `"insiden"`, `"gangguan"`, `"downtime"`, `"serangan"`, `"vulnerability"`, `"temuan auditor"`, `"keterbatasan"`, `"kebocoran data"`, `"sanksi regulasi"`.

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

### Pilar 1: Cyber Security
- **Base Score**: $50$
- **Bukti Terverifikasi**: $5$ klaster bukti dokumen (Hal. 283, 284, 164, dll) $\implies 5 \times 8 = +40$
- **Severity**: *High* (Mencatat kebutuhan independensi pengawasan siber & pemulihan insiden TI) $\implies +8$
- **Perhitungan**:
  $$\text{Skor} = \min(98, \; 50 + 40 + 8) = \mathbf{98} \quad \text{(Prime Opportunity)}$$

### Pilar 6: Managed Service
- **Base Score**: $50$
- **Bukti Terverifikasi**: $4$ klaster bukti dokumen $\implies 4 \times 8 = +32$
- **Severity**: *High* (Kebutuhan SLA operasional cabang 24/7) $\implies +8$
- **Perhitungan**:
  $$\text{Skor} = \min(98, \; 50 + 32 + 8) = \mathbf{90} \quad \text{(Prime Opportunity)}$$
