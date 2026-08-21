# 🤖 Chevy Bot — WhatsApp AI Assistant

<div align="center">

![Chevy Bot](https://img.shields.io/badge/Chevy-Bot-1a237e?style=for-the-badge&logo=whatsapp&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-20+-339933?style=for-the-badge&logo=nodedotjs&logoColor=white)
![Gemini](https://img.shields.io/badge/Google_Gemini-AI-4285F4?style=for-the-badge&logo=google&logoColor=white)
![Azure](https://img.shields.io/badge/Microsoft_Azure-Cloud-0078D4?style=for-the-badge&logo=microsoftazure&logoColor=white)

**Bot WhatsApp AI pribadi dengan arsitektur hybrid Python + Node.js**  
Powered by Google Gemini · Deploy di Microsoft Azure · Online 24 Jam

</div>

---

## ✨ Fitur

| Fitur | Status | Keterangan |
|-------|--------|-----------|
| 💬 Chat AI | ✅ Live | Percakapan cerdas dengan memory konteks |
| 📸 Analisa Gambar | ✅ Live | Kirim foto → Chevy deskripsikan |
| 🎤 Voice Note | ✅ Live | Transkripsi & jawab voice note otomatis |
| 🧠 Memory | ✅ Live | Ingat konteks percakapan per nomor WA |
| 🎨 Generate Gambar | 🚧 Soon | `/gambar [deskripsi]` via Pollinations.ai |
| 🔍 Web Search | 🚧 Soon | `/cari [query]` via DuckDuckGo |
| ⏰ Reminder | 🚧 Soon | `/ingatkan [waktu] [pesan]` |
| 📧 Email | 🚧 Soon | Kirim email via Gmail API dari WA |
| 📊 Excel | 🚧 Soon | Buat & edit file Excel dari WA |

---

## 🏗 Arsitektur

```
📱 WA Business (User)
        │
        ▼
🟨 JS Gateway (Node.js :3000)
   Baileys · handler · bridge
        │  HTTP POST
        ▼
🐍 Python Brain (FastAPI :8000)
   Gemini · Memory · Tools
        │
        ▼
🧠 Google Gemini API
```

Project ini menggunakan **arsitektur hybrid**:
- **JS Gateway** — handle koneksi WhatsApp via Baileys (scan QR, terima/kirim pesan)
- **Python Brain** — semua logika AI, routing command, dan tools

Keduanya berjalan di **Azure VM** dan dikelola oleh **PM2** agar online 24 jam.

---

## 📁 Struktur Project

```
uji-bot/
├── 🟨 gateway/                 # Node.js — WA Gateway
│   ├── src/
│   │   ├── index.js            # Entry point
│   │   ├── config.js           # Load env variables
│   │   ├── whatsapp.js         # Koneksi WA via Baileys
│   │   ├── handler.js          # Router pesan masuk
│   │   ├── bridge.js           # HTTP client ke Python
│   │   └── auth/session/       # Session WA (gitignored)
│   ├── .env.example
│   └── package.json
│
├── 🐍 brain/                   # Python — AI Brain
│   ├── main.py                 # FastAPI endpoints
│   ├── src/
│   │   ├── config.py           # Config & env loader
│   │   ├── doktrin.py          # System prompt Chevy
│   │   ├── gemini.py           # Gemini AI integration
│   │   ├── memory.py           # Conversation history
│   │   └── tools/              # Coming soon features
│   ├── .env.example
│   └── requirements.txt
│
├── .gitignore
└── README.md
```

---

## 🚀 Setup Lokal

### Prerequisites

```bash
# Cek versi
python --version   # 3.10+
node --version     # 20+
npm --version      # 8+
```

### 1. Clone Repository

```bash
git clone https://github.com/USERNAME/uji-bot.git
cd uji-bot
```

### 2. Setup Python Brain

```bash
cd brain

# Buat virtual environment
python -m venv venv

# Aktifkan (Windows)
venv\Scripts\activate
# Aktifkan (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup config
cp .env.example .env
# Edit .env → isi GEMINI_API_KEY
```

### 3. Setup JS Gateway

```bash
cd ../gateway

# Install dependencies
npm install

# Setup config
cp .env.example .env
# Edit .env sesuai kebutuhan
```

### 4. Dapatkan Gemini API Key

1. Buka → [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Klik **Create API Key**
3. Copy dan paste ke `brain/.env`

### 5. Jalankan

Buka **2 terminal terpisah**:

```bash
# Terminal 1 — Python Brain
cd brain
uvicorn main:app --reload --port 8000

# Terminal 2 — JS Gateway
cd gateway
npm start
```

### 6. Scan QR

QR code muncul di terminal JS → buka WA → **Linked Devices** → **Link a Device** → scan.

---

## ⚙️ Environment Variables

### `brain/.env`

```env
# WAJIB
GEMINI_API_KEY=your_api_key_here

# Opsional
GEMINI_MODEL=gemini-2.0-flash-lite
BOT_NAME=Chevy
OWNER_NAME=mas
PORT=8000
ALLOWED_NUMBERS=628xxxxxxxxxx   # kosong = semua bisa akses
```

### `gateway/.env`

```env
PYTHON_BRAIN_URL=http://localhost:8000
SESSION_DIR=./src/auth/session
ALLOWED_NUMBERS=628xxxxxxxxxx
LOG_LEVEL=info
PORT=3000
```

> ⚠️ **Jangan pernah commit file `.env` ke GitHub!** File ini sudah ada di `.gitignore`.

---

## 💬 Perintah Bot

| Perintah | Fungsi |
|----------|--------|
| Chat biasa | Langsung dijawab Chevy |
| `/help` | Tampilkan daftar perintah |
| `/reset` | Hapus memory percakapan |
| `/status` | Cek status bot & model |
| Kirim foto | Chevy analisa gambar |
| Kirim voice note | Chevy transkripsi & jawab |

---

## ☁️ Deploy ke Azure

### 1. Buat VM

```
Portal Azure → Create Resource → Virtual Machine
- OS     : Ubuntu Server 22.04 LTS
- Size   : B1s (1 vCPU, 1GB RAM)
- Region : Southeast Asia
```

### 2. Install di VM

```bash
# SSH ke VM
ssh user@IP_VM

# Install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv git -y
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs -y
sudo npm install -g pm2
```

### 3. Deploy

```bash
git clone https://github.com/USERNAME/uji-bot.git
cd uji-bot

# Setup brain
cd brain && python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && nano .env

# Setup gateway
cd ../gateway && npm install
cp .env.example .env && nano .env
```

### 4. Jalankan dengan PM2

```bash
# Python Brain
pm2 start "cd ~/uji-bot/brain && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000" \
    --name "chevy-brain"

# JS Gateway
pm2 start ~/uji-bot/gateway/src/index.js \
    --name "chevy-gateway"

# Auto-start saat VM reboot
pm2 startup && pm2 save
```

### 5. Scan QR di Azure

```bash
pm2 logs chevy-gateway
# QR code muncul → scan dari WA
```

---

## 🔄 Ganti Nomor WA Chevy

```bash
# SSH ke VM
pm2 stop chevy-gateway
rm -rf ~/uji-bot/gateway/src/auth/session/*
touch ~/uji-bot/gateway/src/auth/session/.gitkeep
pm2 restart chevy-gateway
pm2 logs chevy-gateway   # scan QR baru
```

---

## 🛠 PM2 Commands

```bash
pm2 status                    # Status semua service
pm2 logs                      # Semua log realtime
pm2 logs chevy-brain          # Log Python saja
pm2 logs chevy-gateway        # Log JS saja
pm2 restart chevy-brain       # Restart Python
pm2 restart all               # Restart semua
git pull && pm2 restart all   # Update dari GitHub
```

---

## 🧰 Tech Stack

| Layer | Teknologi | Fungsi |
|-------|-----------|--------|
| WA Connection | Baileys | Connect WA tanpa Meta API |
| AI Engine | Google Gemini 2.0 | Generate response |
| Web Framework | FastAPI | REST API Python |
| Image Compress | Sharp | Kompres gambar sebelum kirim |
| Process Manager | PM2 | Keep alive 24 jam |
| Cloud | Microsoft Azure | Hosting VM |
| Version Control | GitHub | Source code + CI/CD |

---

## ⚠️ Known Issues

- Session WA bisa expired jika VM restart tanpa `pm2 startup` — solusi: jalankan `pm2 startup && pm2 save`
- Gemini free tier punya rate limit — jika kena 429, tunggu beberapa menit atau upgrade plan
- Voice note format harus `ogg/opus` — format lain belum didukung

---

## 📄 Lisensi

Private project — tidak untuk distribusi publik.

---

<div align="center">
Made with ❤️ · Powered by Google Gemini
</div>
