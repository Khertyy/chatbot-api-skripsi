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

### Prasyarat

- Docker Desktop ([Download untuk Windows](https://www.docker.com/products/docker-desktop/))
- Git ([Download](https://git-scm.com/))

### Langkah-langkah Deployment dengan Docker

1. Clone repository:

```bash
git clone git@github.com:Khertyy/chatbot-api-skripsi.git
cd chatbot-api-skripsi
```

2. Buat file environment:

```bash
cp .env.example .env
```

Edit file `.env` dan isi nilai yang diperlukan:

```env
GEMINI_API_KEY="your_api_key_here"
REDIS_PASSWORD="your_secure_password_here"
```

3. Build dan jalankan container:

```bash
docker-compose up --build
```

4. Aplikasi akan berjalan di:

- API: http://localhost:8000
- Redis: localhost:6379

5. Untuk menghentikan:

```bash
docker-compose down
```

### Instalasi Redis di Windows

1. **Menggunakan Docker (Direkomendasikan)**:

   - Ikuti langkah deployment dengan Docker di atas
   - Redis akan otomatis terinstall dalam container

2. **Menggunakan WSL (Windows Subsystem for Linux)**:

   ```bash
   # Install WSL
   wsl --install

   # Install Ubuntu
   wsl --install -d Ubuntu

   # Di lingkungan Ubuntu:
   sudo apt-get update
   sudo apt-get install redis-server
   sudo service redis-server start
   ```

3. **Windows Native (Tidak Direkomendasikan)**:
   - Download Redis untuk Windows dari [Microsoft Archive](https://github.com/microsoftarchive/redis/releases)
   - Ekstrak dan jalankan `redis-server.exe`

## Menjalankan Aplikasi

### Metode 1: Menggunakan Docker (Direkomendasikan)

```bash
docker-compose up --build
```

### Metode 2: Traditional Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Jalankan Redis (Linux/Mac/WSL)
redis-server

# Jalankan aplikasi
uvicorn app.main:app --reload
```

## Verifikasi Instalasi

1. Cek status container:

```bash
docker-compose ps
```

2. Test koneksi Redis:

```bash
docker exec -it chatbot-api-skripsi-redis-1 redis-cli -a your_secure_password_here PING
# Harus merespon "PONG"
```

3. Akses dokumentasi API:

- Swagger UI: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc

## Environment Variables

| Variable       | Required | Default     | Description                       |
| -------------- | -------- | ----------- | --------------------------------- |
| GEMINI_API_KEY | Yes      | -           | API key untuk Google Gemini       |
| REDIS_PASSWORD | No       | ""          | Password untuk koneksi Redis      |
| APP_ENV        | No       | development | Environment aplikasi (production) |

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

## Pengakuan

Proyek ini dikembangkan sebagai bagian dari skripsi untuk Dinas Pemberdayaan Perempuan dan Perlindungan Anak (DP3A) Sulawesi Utara.
