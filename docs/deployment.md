# Panduan Deployment Docker untuk Chatbot API SIPPAT

Dokumen ini menjelaskan langkah-langkah deployment aplikasi Chatbot API untuk sistem SIPPAT DP3A Sulut menggunakan Docker dan Docker Compose.

## 1. Prasyarat

- Docker dan Docker Compose sudah terinstall di server
- Git sudah terinstall

Jika belum terinstall, silakan install Docker terlebih dahulu menggunakan panduan resmi Docker untuk sistem operasi Anda.

## 2. Persiapan Proyek

```bash
# Clone repository (asumsikan baru saja melakukan clone)
git clone https://github.com/username/chatbot-api-skripsi.git
cd chatbot-api-skripsi

# Buat file .env dari contoh
cp .env.example .env
nano .env
```

## 3. Konfigurasi Environment

Isi file `.env` dengan konfigurasi berikut:

```ini
# API Configuration
APP_ENV=production
GEMINI_API_KEY=your_gemini_api_key_here

# Redis Configuration
REDIS_PASSWORD=strong_password_here
```

**Penting:** Gunakan password Redis yang kuat dan API key yang valid untuk Gemini API.

## 4. Build dan Jalankan dengan Docker Compose

```bash
# Build dan jalankan container dalam mode detached
sudo docker compose up --build -d

# Verifikasi container berjalan
sudo docker compose ps
```

**Penjelasan:**

- Flag `--build` memastikan image dibangun ulang jika ada perubahan
- Flag `-d` menjalankan container di background (detached mode)

## 5. Konfigurasi Firewall (UFW)

```bash
# Buka port 8000 untuk API
sudo ufw allow 8000/tcp

# Pastikan SSH tetap bisa diakses
sudo ufw allow ssh

# Aktifkan firewall jika belum aktif
sudo ufw enable

# Verifikasi status firewall
sudo ufw status
```

**Keamanan Tambahan:**

- Idealnya, gunakan reverse proxy seperti Nginx untuk mengekspos API ke internet
- Jika perlu, batasi akses berdasarkan IP dengan: `sudo ufw allow from your_ip_address to any port 8000`

## 6. Verifikasi Deployment

```bash
# Cek container logs
sudo docker compose logs -f

# Test API endpoint
curl -X POST http://localhost:8000/api/v1/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Halo"}'

# Cek Redis container
sudo docker compose exec redis redis-cli -a ${REDIS_PASSWORD} PING
```

## 7. Manajemen Deployment

### Update Aplikasi

```bash
# Pull perubahan terbaru
git pull origin main

# Rebuild dan restart container
sudo docker compose down
sudo docker compose up --build -d
```

### Backup Data Redis

```bash
# Buat direktori backup
mkdir -p ~/backups/redis

# Backup data Redis
sudo docker compose exec redis redis-cli -a ${REDIS_PASSWORD} SAVE
sudo docker cp chatbot-api-skripsi-redis-1:/data/dump.rdb ~/backups/redis/dump.rdb.$(date +%Y%m%d)
```

### Restart Service

```bash
# Restart semua service
sudo docker compose restart

# Restart service tertentu
sudo docker compose restart web
```

## 8. Monitoring & Logging

```bash
# Lihat logs dari semua container
sudo docker compose logs

# Lihat logs dari container FastAPI
sudo docker compose logs web

# Lihat logs realtime
sudo docker compose logs -f web

# Cek resource usage
sudo docker stats
```

## 9. Troubleshooting Umum

### Masalah: Container tidak berjalan

```bash
# Cek status container
sudo docker compose ps

# Lihat logs untuk error
sudo docker compose logs

# Restart container
sudo docker compose down
sudo docker compose up -d
```

### Masalah: Redis Error

```bash
# Periksa logs Redis
sudo docker compose logs redis

# Pastikan variabel REDIS_PASSWORD ada di .env dan format command redis-server benar
# Coba masuk ke container Redis
sudo docker compose exec redis sh
redis-cli -a ${REDIS_PASSWORD} PING
```

### Masalah: API Error

```bash
# Periksa logs API
sudo docker compose logs web

# Pastikan konfigurasi .env benar
# Coba restart container
sudo docker compose restart web
```

## 10. Penanganan Maintenance

```bash
# Maintenance tanpa downtime (saat update minor)
sudo docker compose up -d --no-deps --build web

# Maintenance dengan downtime
sudo docker compose down
# Lakukan perubahan yang diperlukan
sudo docker compose up -d
```

## 11. Rekomendasi Production

1. **Container Registry**: Gunakan private registry untuk image Docker
2. **Health Checks**: Tambahkan health check di docker-compose.yml
3. **Reverse Proxy**: Gunakan Nginx sebagai reverse proxy dengan HTTPS
4. **Persistent Volumes**: Pastikan volume Redis dikonfigurasi dengan benar
5. **CI/CD Pipeline**: Otomatisasi deployment dengan GitHub Actions
6. **Monitoring**: Integrasikan dengan Prometheus dan Grafana untuk monitoring
7. **Secrets Management**: Gunakan Docker Secrets untuk menyimpan kredensial

---

Dengan mengikuti panduan ini, aplikasi FastAPI Chatbot API akan berjalan dengan Docker di server production dengan konfigurasi yang aman dan efisien.
