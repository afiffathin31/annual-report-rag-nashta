# Upload Annual Report ke Google Drive

Skrip `upload_reports_to_drive.py` membaca kedua hasil scraping, mengunduh semua
laporan, membuat folder berdasarkan kode emiten, lalu mengunggah dokumen ke
folder Drive berikut:

`1DEqq-6pGl898d9SwP860tFuykcmXTpKW`

Struktur yang dihasilkan:

```text
Folder target/
├── BANK/
├── BRIS/
├── BTPS/
├── PNBS/
├── CHIP/
├── HALO/
├── IRRA/
├── OMED/
└── PEVE/
```

Setiap folder berisi PDF bernama `KODE_Annual_Report_TAHUN.pdf` dan sebuah
`KODE_manifest.json` yang menyimpan URL sumber. Jika sumber hanya berupa
flipbook dan tidak menyediakan PDF, skrip mengunggah berkas `.url` agar laporan
tetap tercatat dan dapat dibuka.

## Persiapan OAuth

1. Buka Google Cloud Console dan buat/pilih sebuah project.
2. Aktifkan **Google Drive API**.
3. Konfigurasikan OAuth consent screen.
4. Buat OAuth Client ID dengan tipe **Desktop app**.
5. Unduh berkas JSON dan simpan sebagai `credentials.json` di folder proyek.
6. Pastikan akun yang dipilih saat login memiliki akses Editor ke folder target.

Pastikan isi paling luar JSON memiliki kunci `"installed"`, bukan `"web"`.
Kredensial bertipe Web application akan menghasilkan `redirect_uri_mismatch`
karena uploader memakai callback localhost dengan port dinamis.

`u/5` pada URL Drive hanya menunjukkan urutan akun di browser. Skrip menentukan
akun dari login OAuth, bukan dari angka tersebut.

Jika akun yang tersimpan salah atau hanya Viewer, hapus `token.json`, jalankan
ulang skrip, lalu pilih akun yang menjadi Editor folder target. Alternatifnya,
bagikan folder target kepada email OAuth tersebut dengan peran Editor.

Jika muncul `accessNotConfigured` atau pesan bahwa Drive API belum pernah
digunakan, aktifkan API pada project yang sama dengan OAuth Client, tunggu
beberapa menit sampai konfigurasi tersebar, lalu jalankan kembali. `token.json`
tidak perlu dihapus untuk kondisi ini.

## Menjalankan

```powershell
python -m pip install -r requirements.txt

# Lihat rencana tanpa login atau upload
python upload_reports_to_drive.py --dry-run

# Upload semua emiten
python upload_reports_to_drive.py

# Upload kode tertentu saja
python upload_reports_to_drive.py --codes IRRA OMED HALO

# Perbarui file dengan nama yang sudah ada
python upload_reports_to_drive.py --replace

# Perbaiki BTPS: unggah PDF dan pindahkan placeholder .url ke Trash
python upload_reports_to_drive.py --codes BTPS --replace

# Perbaiki PNBS: gunakan fallback TLS khusus domain resmi PNBS
python upload_reports_to_drive.py --codes PNBS --replace
```

Login pertama membuat `token.json`. Jangan membagikan atau memasukkan
`credentials.json` dan `token.json` ke repositori publik. Eksekusi berikutnya
akan memakai token tersebut. Secara default file yang sudah ada dilewati,
sehingga skrip aman dijalankan ulang tanpa membuat duplikat.
