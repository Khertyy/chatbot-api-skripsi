# SIPPAT Chatbot API

SIPPAT (Sistem Informasi Pelaporan Kekerasan Terhadap Anak) Chatbot API adalah sebuah layanan backend yang dikembangkan untuk Dinas Pemberdayaan Perempuan dan Perlindungan Anak (DP3A) Sulawesi Utara. API ini menyediakan antarmuka chatbot yang membantu dalam proses pelaporan kasus kekerasan terhadap anak.

## Fitur

- Chatbot interaktif berbahasa Indonesia
- Sistem manajemen sesi chat dengan Redis
- Pengumpulan informasi laporan secara bertahap
- Integrasi dengan Google Gemini API untuk pemrosesan bahasa alami
- Sistem penyimpanan dan pengelolaan laporan
- Penyimpanan history chat dengan TTL 24 jam

## Prasyarat

Sebelum memulai, pastikan Anda telah menginstal:

- Python 3.10 atau lebih baru
- pip (Python package manager)
- Git
- Redis (untuk manajemen sesi)

### Instalasi Redis

Untuk macOS:

```bash
# Install Redis menggunakan Homebrew
brew install redis

# Start Redis service
brew services start redis

# Verifikasi Redis berjalan
redis-cli ping
# Harus mengembalikan "PONG"
```

Untuk Linux:

```bash
# Install Redis
sudo apt-get update
sudo apt-get install redis-server

# Start Redis service
sudo systemctl start redis

# Verifikasi status Redis
sudo systemctl status redis
```

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

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
SESSION_TTL=86400
```

## Menjalankan Aplikasi

1. Pastikan Redis server berjalan:

```bash
# Cek status Redis
brew services list  # untuk macOS
systemctl status redis  # untuk Linux

# Start Redis jika belum berjalan
brew services start redis  # untuk macOS
sudo systemctl start redis  # untuk Linux
```

2. Pastikan virtual environment sudah aktif
3. Jalankan server FastAPI:

```bash
uvicorn app.main:app --reload
```

Server akan berjalan di `http://localhost:8000`

## Monitoring Redis

### Menggunakan Redis CLI

```bash
# Masuk ke Redis CLI
redis-cli

# Melihat semua keys
KEYS *

# Melihat isi session tertentu
GET "session:[session_id]"

# Melihat sisa waktu TTL (dalam detik)
TTL "session:[session_id]"

# Monitor operasi Redis real-time
MONITOR
```

### Menggunakan API Endpoints

Debug endpoints untuk memonitor sesi:

- GET `/api/v1/chatbot/debug/sessions` - Melihat semua sesi aktif
- GET `/api/v1/chatbot/debug/session/{session_id}` - Melihat detail sesi tertentu

## API Documentation

Setelah server berjalan, Anda dapat mengakses:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoint Utama

- POST `/api/v1/chatbot/chat` - Endpoint untuk interaksi chatbot
- GET `/api/v1/chatbot/reports` - Endpoint untuk mengakses laporan
- GET `/api/v1/chatbot/debug/sessions` - Endpoint untuk melihat sesi aktif
- GET `/api/v1/chatbot/debug/session/{session_id}` - Endpoint untuk detail sesi

## Pengembangan

Untuk berkontribusi pada proyek ini:

1. Fork repository
2. Buat branch baru (`git checkout -b fitur-baru`)
3. Commit perubahan (`git commit -am 'Menambahkan fitur baru'`)
4. Push ke branch (`git push origin fitur-baru`)
5. Buat Pull Request

## Troubleshooting

### Masalah Umum Redis

1. Redis tidak dapat terhubung:

```bash
# Cek status Redis
brew services list  # macOS
systemctl status redis  # Linux

# Restart Redis
brew services restart redis  # macOS
sudo systemctl restart redis  # Linux
```

2. Membersihkan semua data Redis:

```bash
redis-cli FLUSHALL
```

## Lisensi

[MIT License](LICENSE)

## Kontak

Untuk pertanyaan dan dukungan, silakan hubungi:

- Email: [your-email@example.com]
- Website: [your-website.com]

## Pengakuan

Proyek ini dikembangkan sebagai bagian dari skripsi untuk Dinas Pemberdayaan Perempuan dan Perlindungan Anak (DP3A) Sulawesi Utara.
