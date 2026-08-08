# brain/main.py

# Import pustaka FastAPI untuk membangun REST API dan penanganan exception HTTP
from fastapi import FastAPI, HTTPException
# Import middleware CORS untuk mengizinkan akses domain cross-origin
from fastapi.middleware.cors import CORSMiddleware
# Import asynccontextmanager untuk mengelola lifecycle aplikasi (startup & shutdown)
from contextlib import asynccontextmanager
# Import Pydantic untuk validasi tipe data pada request body (schema)
from pydantic import BaseModel
# Import Optional untuk penanganan bidang request yang tidak wajib
from typing import Optional
# Import pustaka standar untuk pengodean data Base64 dan logging
import base64
import logging

# Import modul internal: konfigurasi, handler Gemini, dan pengelola memori
from src.config  import config
from src.gemini  import chat, analyze_image, analyze_audio, reset_chat
from src.memory  import memory

# ── Logging ──────────────────────────────────────────────────
# Konfigurasi format dan tingkat detail pencatatan log pada aplikasi
logging.basicConfig(
    level  = logging.INFO,                                 # Menampilkan log level INFO dan di atasnya
    format = "%(asctime)s | %(levelname)s | %(message)s"   # Format: [Waktu] | [Level] | [Pesan]
)
logger = logging.getLogger(__name__)                      # Inisialisasi instance logger utama


# ── Lifespan (startup & shutdown) ────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Mengelola event saat server pertama kali dinyalakan (startup)
    dan saat server dimatikan (shutdown).
    """
    # Event Startup: Log status awal dan tampilkan ringkasan konfigurasi
    logger.info("🐍 Python Brain starting up...")
    config.print_summary()
    logger.info(f"✅ {config.BOT_NAME} Brain siap di port {config.PORT}")
    
    yield  # Aplikasi berjalan dan menerima request di titik ini
    
    # Event Shutdown: Log ketika aplikasi dihentikan
    logger.info(f"👋 {config.BOT_NAME} Brain shutdown...")


# ── App ──────────────────────────────────────────────────────
# Inisialisasi aplikasi FastAPI utama beserta metadata OpenAPI/Swagger
app = FastAPI(
    title       = f"{config.BOT_NAME} Brain API",  # Judul dokumentasi API
    description = "Python AI Brain for WhatsApp Bot",# Deskripsi singkat API
    version     = "1.0.0",                           # Versi aplikasi
    lifespan    = lifespan,                          # Mendaftarkan event handler lifespan
)

# Menambahkan middleware CORS agar API dapat diakses dari Web Dashboard/Frontend lokal
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:3000"],  # Domain frontend yang diizinkan
    allow_methods = ["POST", "GET"],            # Metode HTTP yang diizinkan
    allow_headers = ["*"],                      # Mengizinkan semua header request
)


# ── Schema ───────────────────────────────────────────────────
class TextRequest(BaseModel):
    """Schema Pydantic untuk data request pesan teks."""
    sender : str  # ID / Nomor WhatsApp pengirim
    text   : str  # Teks pesan yang dikirimkan

class ImageRequest(BaseModel):
    """Schema Pydantic untuk data request analisis gambar."""
    sender    : str            # ID / Nomor WhatsApp pengirim
    image_b64 : str            # Data gambar dalam format string Base64
    caption   : Optional[str] = ""  # Teks caption/keterangan gambar (opsional)

class AudioRequest(BaseModel):
    """Schema Pydantic untuk data request analisis audio/voice note."""
    sender    : str  # ID / Nomor WhatsApp pengirim
    audio_b64 : str  # Data audio dalam format string Base64


# ── Helper ───────────────────────────────────────────────────
def check_whitelist(sender: str):
    """
    Helper untuk memeriksa apakah nomor pengirim terdaftar di daftar ALLOWED_NUMBERS.
    Melemparkan HTTPException 403 jika nomor tidak diizinkan.
    """
    # Membersihkan suffix domain WhatsApp (@s.whatsapp.net) untuk menyisakan nomor murni
    number = sender.replace("@s.whatsapp.net", "").strip()
    
    # Memeriksa whitelist jika daftar ALLOWED_NUMBERS tidak kosong
    if config.ALLOWED_NUMBERS and number not in config.ALLOWED_NUMBERS:
        raise HTTPException(status_code=403, detail="Nomor tidak diizinkan")


# ── Endpoints ────────────────────────────────────────────────
@app.get("/health")
async def health():
    """Endpoint untuk mengecek kesehatan server dan status informasi bot."""
    return {
        "status" : "ok",
        "bot"    : config.BOT_NAME,
        "model"  : config.GEMINI_MODEL,
    }


@app.post("/chat")
async def handle_chat(req: TextRequest):
    """
    Endpoint utama untuk menangani pesan teks dan perintah bot (commands).
    """
    # Mencatat log pesan masuk (dibatasi 50 karakter pertama)
    logger.info(f"📨 Chat dari {req.sender}: {req.text[:50]}...")
    # Verifikasi hak akses nomor pengirim
    check_whitelist(req.sender)

    # Mengubah teks menjadi huruf kecil dan membuang spasi kosong di awal/akhir
    text_lower = req.text.lower().strip()

    # Perintah /reset: Menghapus memori riwayat obrolan
    if text_lower == "/reset":
        reply = await reset_chat(req.sender)

    # Perintah /status atau /stat: Menampilkan statistik memori dan info model
    elif text_lower in ["/status", "/stat"]:
        stats = memory.stats(req.sender)
        reply = (
            f"✅ *{config.BOT_NAME} Status*\n\n"
            f"🧠 Total pesan   : {stats['total_pesan']}\n"
            f"⏱️ Aktif terakhir : {stats['last_active']}\n"
            f"🤖 Model         : {config.GEMINI_MODEL}"
        )

    # Perintah /help atau /bantuan: Menampilkan panduan penggunaan dan daftar perintah
    elif text_lower in ["/help", "/bantuan"]:
        reply = (
            f"🤖 *{config.BOT_NAME} — Perintah*\n\n"
            f"💬 Chat biasa → langsung ketik aja {config.OWNER_NAME}\n\n"
            f"⚙️ *Perintah:*\n"
            f"• /reset    — hapus memory\n"
            f"• /status   — cek status\n"
            f"• /help     — pesan ini\n\n"
            f"🚧 *Coming soon:*\n"
            f"• /gambar   — generate gambar\n"
            f"• /cari     — web search\n"
            f"• /ingatkan — set reminder"
        )

    # Jika bukan perintah khusus, proses pesan teks menggunakan model AI Gemini
    else:
        reply = await chat(req.sender, req.text)

    # Mengembalikan respons dalam format JSON standar
    return { "reply": reply, "type": "text" }


@app.post("/image")
async def handle_image(req: ImageRequest):
    """
    Endpoint untuk menerima dan menganalisis pesan berisi gambar.
    """
    # Mencatat log aktivitas pengiriman gambar
    logger.info(f"📸 Image dari {req.sender}")
    # Verifikasi hak akses nomor pengirim
    check_whitelist(req.sender)

    # Dekode string Base64 menjadi byte array gambar
    image_bytes = base64.b64decode(req.image_b64)
    # Proses analisis gambar melalui fungsi analyze_image
    reply = await analyze_image(req.sender, image_bytes, req.caption)
    
    # Mengembalikan teks hasil analisis gambar
    return { "reply": reply, "type": "text" }


@app.post("/audio")
async def handle_audio(req: AudioRequest):
    """
    Endpoint untuk menerima dan menganalisis pesan suara (voice note).
    """
    # Mencatat log aktivitas pengiriman audio
    logger.info(f"🎤 Audio dari {req.sender}")
    # Verifikasi hak akses nomor pengirim
    check_whitelist(req.sender)

    # Dekode string Base64 menjadi byte array audio
    audio_bytes = base64.b64decode(req.audio_b64)
    # Proses transkripsi dan analisis audio melalui fungsi analyze_audio
    reply = await analyze_audio(req.sender, audio_bytes)
    
    # Mengembalikan teks hasil transkripsi/balasan audio
    return { "reply": reply, "type": "text" }