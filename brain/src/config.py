# brain/src/config.py

# Import fungsi load_dotenv untuk membaca environment variables dari file .env
from dotenv import load_dotenv
# Import class Path untuk penanganan path/direktori file secara lintas platform
from pathlib import Path
# Import modul os untuk mengakses environment variables sistem
import os

# Menentukan lokasi path absolut file .env yang berada 2 tingkat di atas direktori file ini (di root project)
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

# Memuat environment variables dari file .env ke dalam sistem (override=True memaksa pembaruan jika kunci sudah ada)
load_dotenv(dotenv_path=_ENV_PATH, override=True)


def required(key: str) -> str:
    """
    Fungsi helper untuk mengambil environment variable yang sifatnya wajib (mandatory).
    Jika kunci tidak ada atau bernilai kosong, fungsi akan melemparkan ValueError.
    """
    # Mengambil nilai dari environment variable dan menghapus spasi di awal/akhir
    val = os.getenv(key, "").strip()
    
    # Validasi: Jika nilai kosong, hentikan eksekusi program dan munculkan pesan kesalahan
    if not val:
        raise ValueError(f"\n❌ ENV ERROR: '{key}' wajib diisi di .env\n")
    
    # Mengembalikan nilai variable jika valid
    return val


def optional(key: str, fallback: str = "") -> str:
    """
    Fungsi helper untuk mengambil environment variable yang sifatnya opsional.
    Jika kunci tidak ditemukan, mengembalikan nilai bawaan (fallback).
    """
    # Mengambil nilai variable, jika tidak ada gunakan nilai fallback, lalu bersihkan spasi
    return os.getenv(key, fallback).strip()


class Config:
    """
    Class pusat untuk memuat, menyimpan, dan memvalidasi seluruh konfigurasi aplikasi.
    """
    def __init__(self):
        # Nama bot AI (default: "Chevy")
        self.BOT_NAME   = optional("BOT_NAME", "Chevy")
        
        # Nama pemilik/pengguna utama yang menyapa bot (default: "mas")
        self.OWNER_NAME = optional("OWNER_NAME", "mas")

        # API Key Google Gemini (Wajib ada di .env)
        self.GEMINI_API_KEY = required("GEMINI_API_KEY")
        
        # Versi/tipe model Gemini yang digunakan (default: "gemini-2.5-flash")
        self.GEMINI_MODEL   = optional("GEMINI_MODEL", "gemini-2.5-flash")

        # Port server aplikasi, dikonversi dari String ke Integer (default: 8000)
        self.PORT = int(optional("PORT", "8000"))

        # Mengubah string daftar nomor telepon yang dipisahkan koma menjadi list Python dan membuang spasi kosong
        self.ALLOWED_NUMBERS = [
            n.strip()
            for n in optional("ALLOWED_NUMBERS", "").split(",")
            if n.strip()
        ]

        # URL endpoint untuk service pembuat gambar Pollinations AI
        self.POLLINATIONS_URL = optional(
            "POLLINATIONS_URL",
            "https://image.pollinations.ai/prompt"
        )
        
        # API Key untuk Serper (pencarian Google Search API), opsional
        self.SERPER_API_KEY = optional("SERPER_API_KEY", "")

    def print_summary(self):
        """
        Mencetak ringkasan konfigurasi yang telah berhasil dimuat saat aplikasi dinyalakan.
        """
        print("\n📋 CONFIG LOADED:")
        print(f"   Bot Name  : {self.BOT_NAME}")
        print(f"   Owner     : {self.OWNER_NAME}")
        print(f"   Model     : {self.GEMINI_MODEL}")
        print(f"   Port      : {self.PORT}")
        # Menampilkan daftar nomor Whitelist atau tanda peringatan jika kosong
        print(f"   Whitelist : {self.ALLOWED_NUMBERS or '⚠️  KOSONG'}")
        print("")


# Membuat instance singleton 'config' agar bisa di-import dan digunakan secara langsung oleh modul lain
config = Config()5