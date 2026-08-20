# Scraper Annual Report — Alat & Perlengkapan Medis

Skrip ini memproses **IRRA, OMED, CHIP, HALO, dan PEVE** untuk tahun buku
2021–2025. Perlu diperhatikan bahwa CHIP adalah emiten teknologi/telekomunikasi,
bukan emiten alat medis. OMED, CHIP, HALO, dan PEVE baru memiliki laporan publik
sejak tahun buku 2022.

## Menjalankan

```powershell
python -m pip install -r requirements.txt
python scrape_medical_equipment.py
```

Hasil dibuat sebagai:

- `hasil_alat_perlengkapan_medis.md` — format siap dibaca/ditempel.
- `hasil_alat_perlengkapan_medis.json` — format terstruktur untuk olah data.

Pilihan berguna:

```powershell
# Hanya emiten tertentu
python scrape_medical_equipment.py --codes IRRA OMED

# Lewati pemeriksaan seluruh URL PDF agar lebih cepat
python scrape_medical_equipment.py --skip-link-check

# Jalankan unit test parser
python -m unittest tests.test_medical_scraper -v
```

## Alur scraper

1. Mengambil HTML halaman Hubungan Investor resmi.
2. Mencari anchor PDF/Google Drive yang konteksnya menyebut laporan tahunan.
3. Menormalkan relative URL dan karakter spasi.
4. Membatasi tahun buku ke 2021–2025.
5. Mengisi tahun yang hilang dari snapshot URL resmi terverifikasi.
6. Memeriksa setiap tautan dengan unduhan parsial, sehingga PDF besar tidak
   perlu diunduh seluruhnya.
7. Mengekspor Markdown dan JSON.

Fallback tidak melewati proteksi situs. Ia hanya menyimpan URL yang memang
dipublikasikan pada halaman resmi perusahaan, sehingga proses tetap dapat
direproduksi saat firewall menolak koneksi otomatis.
