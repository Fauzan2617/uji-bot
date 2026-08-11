# brain/main.py

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional
import base64
import logging
import asyncio

from src.config  import config
from src.gemini  import chat, analyze_image, analyze_audio, reset_chat
from src.memory  import memory

# ── Logging ──────────────────────────────────────────────────
logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)


# ── Lifespan ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🐍 Python Brain starting up...")
    config.print_summary()
    logger.info(f"✅ {config.BOT_NAME} Brain siap di port {config.PORT}")
    yield
    logger.info(f"👋 {config.BOT_NAME} Brain shutdown...")


# ── App ──────────────────────────────────────────────────────
app = FastAPI(
    title       = f"{config.BOT_NAME} Brain API",
    description = "Python AI Brain for WhatsApp Bot",
    version     = "1.0.0",
    lifespan    = lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:3000"],
    allow_methods = ["POST", "GET"],
    allow_headers = ["*"],
)


# ── Timeout Middleware ────────────────────────────────────────
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    try:
        return await asyncio.wait_for(call_next(request), timeout=60.0)
    except asyncio.TimeoutError:
        return JSONResponse(
            status_code = 504,
            content     = {"detail": "Request timeout"}
        )


# ── Schema ───────────────────────────────────────────────────
class TextRequest(BaseModel):
    sender : str
    text   : str

class ImageRequest(BaseModel):
    sender    : str
    image_b64 : str
    caption   : Optional[str] = ""

class AudioRequest(BaseModel):
    sender    : str
    audio_b64 : str


# ── Helper ───────────────────────────────────────────────────
def check_whitelist(sender: str):
    number = sender.replace("@s.whatsapp.net", "").strip()
    if config.ALLOWED_NUMBERS and number not in config.ALLOWED_NUMBERS:
        raise HTTPException(status_code=403, detail="Nomor tidak diizinkan")


# ── Endpoints ────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status" : "ok",
        "bot"    : config.BOT_NAME,
        "model"  : config.GEMINI_MODEL,
    }


@app.post("/chat")
async def handle_chat(req: TextRequest):
    logger.info(f"📨 Chat dari {req.sender}: {req.text[:50]}...")
    check_whitelist(req.sender)

    text_lower = req.text.lower().strip()

    if text_lower == "/reset":
        reply = await reset_chat(req.sender)

    elif text_lower in ["/status", "/stat"]:
        stats = memory.stats(req.sender)
        reply = (
            f"✅ *{config.BOT_NAME} Status*\n\n"
            f"🧠 Total pesan   : {stats['total_pesan']}\n"
            f"⏱️ Aktif terakhir : {stats['last_active']}\n"
            f"🤖 Model         : {config.GEMINI_MODEL}"
        )

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

    else:
        reply = await chat(req.sender, req.text)

    return { "reply": reply, "type": "text" }


@app.post("/image")
async def handle_image(req: ImageRequest):
    logger.info(f"📸 Image dari {req.sender} — size: {len(req.image_b64)} chars")
    check_whitelist(req.sender)

    try:
        image_bytes = base64.b64decode(req.image_b64)
        logger.info(f"📸 Decoded: {len(image_bytes)} bytes")

        reply = await analyze_image(req.sender, image_bytes, req.caption)
        return { "reply": reply, "type": "text" }

    except Exception as e:
        logger.error(f"❌ Image error: {e}")
        raise HTTPException(
            status_code = 500,
            detail      = f"Gagal analisa gambar: {str(e)}"
        )


@app.post("/audio")
async def handle_audio(req: AudioRequest):
    logger.info(f"🎤 Audio dari {req.sender}")
    check_whitelist(req.sender)

    try:
        audio_bytes = base64.b64decode(req.audio_b64)
        reply = await analyze_audio(req.sender, audio_bytes)
        return { "reply": reply, "type": "text" }

    except Exception as e:
        logger.error(f"❌ Audio error: {e}")
        raise HTTPException(
            status_code = 500,
            detail      = f"Gagal proses audio: {str(e)}"
        )