# brain/src/gemini.py

# Import pustaka standar Python untuk pengodean data Base64 dan logging
import base64
import logging

# Import Google GenAI SDK (versi SDK baru 'google-genai')
from google import genai
from google.genai import types

# Import konfigurasi internal, instruksi sistem (doktrin), dan pengelola memori
from src.config  import config
from src.doktrin import get_doktrin
from src.memory  import memory

# Inisialisasi instance logger untuk pencatatan log pada modul ini
logger = logging.getLogger(__name__)

# Inisialisasi Klien SDK Gemini menggunakan API Key dari file konfigurasi
client = genai.Client(api_key=config.GEMINI_API_KEY)


def _get_config():
    """
    Fungsi privat untuk membuat dan mengembalikan objek konfigurasi GenerateContentConfig.
    Mengatur sistem instruksi, batas maksimum token output, dan kreativitas respons (temperature).
    """
    return types.GenerateContentConfig(
        system_instruction = get_doktrin(), # Mengambil kepribadian/aturan utama bot dari modul doktrin
        max_output_tokens  = 1024,          # Batasi panjang jawaban maksimum hingga 1024 token
        temperature        = 0.8,           # Menentukan tingkat kreativitas respons (0.0 = deterministik, 1.0 = sangat kreatif)
    )


async def chat(sender: str, text: str) -> str:
    """
    Mengelola sesi obrolan teks interaktif secara asinkron dengan mempertahankan riwayat pesan.
    """
    try:
        # Mengambil riwayat percakapan sebelumnya untuk pengguna 'sender' dari memori
        history = memory.get(sender)

        # Memuat sesi percakapan asinkron (aio.chats) dengan model, konfigurasi, dan riwayat obrolan
        chat_session = client.aio.chats.create(
            model   = config.GEMINI_MODEL, # Menentukan ID model (contoh: models/gemini-2.5-flash)
            config  = _get_config(),                   # Mengaplikasikan parameter konfigurasi generasi
            history = history,                          # Memuat riwayat obrolan yang sudah ada
        )

        # Mengirim pesan teks baru ke model secara asinkron dan menunggu balasan
        response = await chat_session.send_message(text)
        reply    = response.text

        # Menyimpan input dari pengguna ke riwayat memori lokal
        memory.add(sender, "user",  text)
        # Menyimpan jawaban dari AI ke riwayat memori lokal
        memory.add(sender, "model", reply)

        # Mengembalikan teks balasan AI ke pemanggil fungsi
        return reply

    except Exception as e:
        # Catat log kesalahan jika proses obrolan gagal
        logger.error(f"Error chat Gemini: {e}")
        # Lempar ulang pengecualian agar penanganan error di layer atas dapat menangkapnya
        raise


async def analyze_image(sender: str, image_bytes: bytes, caption: str = "") -> str:
    """
    Menganalisis file gambar (dalam bentuk bytes) beserta caption opsional secara asinkron.
    """
    try:
        # Mengonversi bytes gambar mentah menjadi objek Part dari SDK google-genai
        image_part = types.Part.from_bytes(
            data      = image_bytes,  # Data bytes dari gambar
            mime_type = "image/jpeg", # Format MIME type gambar (misal: image/jpeg)
        )

        # Gunakan teks caption pengguna jika ada, atau gunakan instruksi analisis standar
        prompt = caption if caption else "Tolong analisa gambar ini dan deskripsikan apa yang kamu lihat."

        # Mengirimkan teks prompt dan objek gambar ke model AI menggunakan API asinkron
        response = await client.aio.models.generate_content(
            model    = config.GEMINI_MODEL, # Menentukan target model Gemini
            contents = [prompt, image_part],            # Mengirimkan prompt dan gambar sebagai kontens multimodal
            config   = _get_config(),                   # Menerapkan konfigurasi generasi
        )
        reply = response.text

        # Simpan riwayat pengiriman gambar dan respons jawaban AI ke memori
        memory.add(sender, "user",  f"[User mengirim gambar] {prompt}")
        memory.add(sender, "model", reply)

        # Mengembalikan teks hasil analisis gambar
        return reply

    except Exception as e:
        # Catat log kesalahan jika proses analisis gambar gagal
        logger.error(f"Error analyze image: {e}")
        raise


async def analyze_audio(sender: str, audio_bytes: bytes) -> str:
    """
    Mengirimkan dan menganalisis berkas suara/voice note (dalam bytes) secara asinkron.
    """
    try:
        # Mengonversi bytes audio mentah menjadi objek Part dengan tipe MIME audio/ogg
        audio_part = types.Part.from_bytes(
            data      = audio_bytes,             # Data bytes dari rekaman audio
            mime_type = "audio/ogg; codecs=opus", # Tipe MIME audio (format standar WhatsApp voice note)
        )

        # Menyusun prompt konteks untuk menginstruksikan bot mentranskripsi dan merespons isi audio
        prompt = (
            f"Kamu adalah {config.BOT_NAME}. "
            f"Transkripsi audio dari '{config.OWNER_NAME}' ini. "
            f"Kalau ada pertanyaan di dalamnya, jawab juga dengan hangat."
        )

        # Mengirimkan teks prompt instruksi dan data audio ke model AI secara asinkron
        response = await client.aio.models.generate_content(
            model    = config.GEMINI_MODEL, # Menentukan target model Gemini
            contents = [prompt, audio_part],            # Mengirim konteks teks dan payload audio
            config   = _get_config(),                   # Menerapkan konfigurasi generasi
        )
        reply = response.text

        # Menyimpan log aktivitas voice note dan balasan AI ke memori
        memory.add(sender, "user",  "[User mengirim voice note]")
        memory.add(sender, "model", reply)

        # Mengembalikan teks hasil transkripsi dan jawaban AI
        return reply

    except Exception as e:
        # Catat log kesalahan jika analisis audio mengalami kendala
        logger.error(f"Error analyze audio: {e}")
        raise


async def reset_chat(sender: str) -> str:
    """
    Menghapus seluruh riwayat percakapan pengguna tertentu di memori.
    """
    # Menghapus data histori pesan berdasarkan ID/nama pengirim
    memory.clear(sender)
    
    # Mengembalikan konfirmasi teks bahwa memori obrolan telah berhasil dibersihkan
    return f"Oke {config.OWNER_NAME}, memory {config.BOT_NAME} sudah direset. Mulai fresh lagi ya 😊"