# Panduan Deployment Chatbot API SIPPAT

Dokumen ini menjelaskan langkah-langkah deployment aplikasi Chatbot API untuk sistem SIPPAT DP3A Sulut.

## 1. Persiapan Server

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git
```

**Penjelasan:**

- Update paket sistem untuk memastikan keamanan dan kompatibilitas
- Install dependency dasar:
  - `python3-pip`: Package manager Python
  - `python3-venv`: Virtual environment Python
  - `git`: Version control system

## 2. Install dan Konfigurasi Redis

```bash
sudo apt install -y redis-server
sudo nano /etc/redis/redis.conf
```

**Parameter penting di redis.conf:**

```ini
maxmemory 256mb           # Batas memori untuk prevent memory leak
maxmemory-policy allkeys-lru  # Strategi penghapusan data saat memori penuh
requirepass your_secure_password  # Sesuai dengan REDIS_PASSWORD di .env
bind 127.0.0.1            # Hanya izinkan akses lokal
```

```bash
sudo systemctl restart redis
sudo systemctl enable redis
```

**Alasan Konfigurasi:**

- Membatasi penggunaan memori untuk mencegah overutilization
- Autentikasi password meningkatkan keamanan
- Binding lokal mengurangi exposure ke jaringan publik

## 3. Setup Aplikasi

```bash
cd ~/chatbot-api-skripsi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
```

**Isi .env yang penting:**

```ini
APP_ENV=production
GEMINI_API_KEY="your_api_key"
REDIS_HOST="localhost"
REDIS_PASSWORD="your_redis_password"
REDIS_DB=0
```

**Best Practices:**

- Gunakan environment terpisah untuk development/production
- Simpan secret key di environment variables, bukan di codebase
- Jangan commit file .env ke version control

## 4. Systemd Service Setup

Buat file `/etc/systemd/system/chatbot-api.service`:

```ini
[Unit]
Description=SIPPAT Chatbot API Service
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/chatbot-api-skripsi
Environment="PATH=/home/ubuntu/chatbot-api-skripsi/venv/bin"
ExecStart=/home/ubuntu/chatbot-api-skripsi/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**Aktifkan service:**

```bash
sudo systemctl daemon-reload
sudo systemctl start chatbot-api
sudo systemctl enable chatbot-api
```

**Keuntungan Systemd:**

- Auto-restart saat crash
- Log management terintegrasi
- Kemampuan berjalan di background
- Mudah monitoring dengan `journalctl`

## 5. Konfigurasi Keamanan

```bash
sudo ufw allow 8000
sudo ufw allow 22
sudo ufw enable
```

**Pertimbangan Keamanan:**

- Hanya buka port yang diperlukan
- Pertimbangkan reverse proxy dengan Nginx/Apache
- Gunakan HTTPS dengan Let's Encrypt
- Batasi akses Redis hanya dari localhost

## 6. Verifikasi Deployment

```bash
# Cek status service
sudo systemctl status chatbot-api

# Test API endpoint
curl -X POST http://localhost:8000/api/v1/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Halo"}'

# Cek koneksi Redis
redis-cli -a your_redis_password PING
```

## 7. Maintenance Rutin

**Backup Strategy:**

1. **Redis:**
   ```bash
   redis-cli SAVE
   cp /var/lib/redis/dump.rdb /path/to/backup
   ```
2. **Codebase:** Lakukan git pull secara berkala
3. **Environment:** Simpan salinan .env di tempat aman

**Update Aplikasi:**

```bash
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart chatbot-api
```

## Troubleshooting Umum

**Masalah: API tidak merespon**

```bash
# Cek log aplikasi
journalctl -u chatbot-api -f

# Cek koneksi Redis
redis-cli -a your_password INFO clients
```

**Masalah: Memory Usage Tinggi**

```bash
# Identifikasi proses
top -o %MEM

# Flush Redis cache
redis-cli -a your_password FLUSHALL
```
