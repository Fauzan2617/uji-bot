from dotenv import load_dotenv # Di gunakan untuk membaca .env
import os # akses variable Environment

load_dotenv ()


# Definisi fungsi 'required' yang menerima parameter 'key' (nama variabel environment)
# dan mengembalikan nilai berjenis string (tipe data teks)
def required(key: str) -> str:
    # Mengambil nilai variabel environment berdasarkan 'key'.
    # Jika variabel tidak ditemukan, gunakan string kosong "" sebagai default, lalu hapus spasi di awal/akhir dengan .strip()
    val = os.getenv(key, "").strip()

    # Mengecek apakah nilai variabel kosong ATAU masih berisi nilai bawaan/placeholder yang diawali "isi_"
    if not val or val.startswith("isi_"):
        # Memicu error (ValueError) untuk menghentikan program jika nilai variabel belum diisi dengan benar
        raise ValueError(
            # Pesan error baris pertama: Memberi tahu nama variabel environment yang wajib diisi
            f"\n❌ ENV ERROR: '{key}' wajib diisi di file .env\n"
            # Pesan error baris kedua: Memberi petunjuk lokasi dokumentasi/panduan
            f"    Lihat .env untuk panduan.\n"
        )

    # Mengembalikan nilai variabel environment yang sudah dipastikan valid (diisi)
    return val

# Fungsi yang sama dalam mengambil isi env, namun dengan fallback
def optional (key: str, fallback: str = "") -> str :
    return os.getenv(key,fallback).strip()

# kita buat kelas untuk memanage semua config
class Config :
    BOT_NAME    : str = optional("BOT_NAME", "Chevy")
    OWNER_NAME  : str = optional("OWNER_NAME", "mas")
    GEMINI_API_KEY: str = required("GEMINI_API_KEY")
    GEMINI_MODEL : str = optional("gemini-flash-latest")
    PORT : int = int(optional("PORT", "8000"))
    # Memberi komentar/label bahwa bagian kode ini berfungsi untuk fitur keamanan (pembatasan nomor WhatsApp)
# Security - whitelist nomor WA

    # Mendefinisikan variabel 'ALLOWED_NUMBERS' dengan penanda tipe data sebagai 'list' (daftar)
    ALLOWED_NUMBERS: list = [
        # Membersihkan karakter spasi di awal/akhir dari setiap nomor telepon (misal: " 62812... " menjadi "62812...")
        n.strip()
        # Mengambil nilai environment 'ALLOWED_NUMBERS' via fungsi optional() (default: string kosong ""),
        # lalu memotong/memisahkan string tersebut menjadi list berdasarkan karakter koma (",")
        for n in optional("ALLOWED_NUMBERS", "").split(",")
        # Melakukan penyaringan (filtering): hanya memasukkan nomor yang tidak kosong ke dalam list akhir
        if n.strip()
    ]
    
    # Tools
    POLLINATIONS_URL : str = optional(
        "POLLINATIONS_URL",
        "https://image.pollinations.ai/prompt"
    )
    SERPER_API_KEY : str = optional("SERPER_API_KEY", "")
    
    # fungsi dibawah untuk 
    def print_summary(self):
        print("\n CONFIG LOADED")
        print(f" BOT NAME      : {self.BOT_NAME}")
        print(f"   Owner       : {self.OWNER_NAME}")
        print(f"   Model       : {self.GEMINI_MODEL}")
        print(f"   Port        : {self.PORT}")
        print(f"   Whitelist   : {self.ALLOWED_NUMBERS or '⚠️  KOSONG (semua bisa akses)'}")
        print("")

config = Config()