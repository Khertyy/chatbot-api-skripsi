# SIPPAT Chatbot API

SIPPAT (Sistem Informasi Pelaporan Kekerasan Terhadap Anak) Chatbot API adalah sebuah layanan backend yang dikembangkan untuk Dinas Pemberdayaan Perempuan dan Perlindungan Anak (DP3A) Sulawesi Utara. API ini menyediakan antarmuka chatbot yang membantu dalam proses pelaporan kasus kekerasan terhadap anak.

## Fitur

- Chatbot interaktif berbahasa Indonesia
- Sistem manajemen sesi chat
- Pengumpulan informasi laporan secara bertahap
- Integrasi dengan Google Gemini API untuk pemrosesan bahasa alami
- Sistem penyimpanan dan pengelolaan laporan

## Prasyarat

Sebelum memulai, pastikan Anda telah menginstal:

- Python 3.10 atau lebih baru
- pip (Python package manager)
- Git

## Instalasi

1. Clone repository ini menggunakan HTTPS:

```bash
git clone git@github.com:Khertyy/chatbot-api-skripsi.git
```

2. Masuk ke direktori proyek:

```bash
cd chatbot-api-skripsi
```

3. Buat virtual environment:

```bash
python -m venv venv
```

4. Aktifkan virtual environment:

Untuk Windows:

```bash
venv\Scripts\activate
```

Untuk macOS/Linux:

```bash
source venv/bin/activate
```

5. Install dependensi:

```bash
pip install -r requirements.txt
```

## Konfigurasi

1. Buat file `.env` di root direktori proyek
2. Tambahkan konfigurasi berikut:

```env
GEMINI_API_KEY=your_gemini_api_key
APP_ENV=development
```

## Menjalankan Aplikasi

1. Pastikan virtual environment sudah aktif
2. Jalankan server FastAPI:

```bash
uvicorn app.main:app --reload
```

Server akan berjalan di `http://localhost:8000`

## API Documentation

Setelah server berjalan, Anda dapat mengakses:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoint Utama

- POST `/api/v1/chatbot/chat` - Endpoint untuk interaksi chatbot
- GET `/api/v1/chatbot/reports` - Endpoint untuk mengakses laporan

## Pengembangan

Untuk berkontribusi pada proyek ini:

1. Fork repository
2. Buat branch baru (`git checkout -b fitur-baru`)
3. Commit perubahan (`git commit -am 'Menambahkan fitur baru'`)
4. Push ke branch (`git push origin fitur-baru`)
5. Buat Pull Request

## Lisensi

[MIT License](LICENSE)

## Kontak

Untuk pertanyaan dan dukungan, silakan hubungi:

- Email: [your-email@example.com]
- Website: [your-website.com]

## Pengakuan

Proyek ini dikembangkan sebagai bagian dari skripsi untuk Dinas Pemberdayaan Perempuan dan Perlindungan Anak (DP3A) Sulawesi Utara.
