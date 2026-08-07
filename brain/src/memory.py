# brain/src/memory.py

from collections import defaultdict
from datetime import datetime, timedelta

# Batas maksimum riwayat pesan yang disimpan per pengirim
MAX_HISTORY = 20

# Durasi inaktif dalam jam sebelum riwayat dianggap kedaluwarsa
EXPIRED_HOURS = 2


class Memory:
    """Mengelola riwayat percakapan dan status aktivitas pengirim."""

    def __init__(self):
        """Inisialisasi penyimpanan riwayat dan waktu aktivitas terakhir.

        `_history`: Menyimpan list riwayat percakapan per pengirim.
        `_last_active`: Menyimpan timestamp aktivitas terakhir per pengirim (default: waktu instansiasi dipanggil).
        """
        self._history = defaultdict(list)
        self._last_active = defaultdict(datetime.now)

    def _is_expired(self, sender: str) -> bool:
        """Memeriksa apakah masa aktif pengirim telah kedaluwarsa.

        Args:
            sender (str): ID/nama pengirim.

        Returns:
            bool: True jika durasi inaktif melebihi EXPIRED_HOURS, False jika tidak.
        """
        last = self._last_active[sender]
        return datetime.now() - last > timedelta(hours=EXPIRED_HOURS)

    def get(self, sender: str) -> list:
        """Mengambil riwayat percakapan pengirim.

        Jika riwayat sudah kedaluwarsa, riwayat akan direset terlebih dahulu.

        Args:
            sender (str): ID/nama pengirim.

        Returns:
            list: Daftar pesan percakapan yang tersimpan.
        """
        if self._is_expired(sender):
            self.clear(sender)
        return self._history[sender]

    def add(self, sender: str, role: str, text: str):
        """Menambahkan pesan baru ke riwayat percakapan pengirim.

        Juga memperbarui timestamp aktivitas terakhir dan memotong riwayat
        jika melebihi MAX_HISTORY.

        Args:
            sender (str): ID/nama pengirim.
            role (str): Peran pengirim pesan (misal: 'user', 'model').
            text (str): Isi pesan.
        """
        # Perbarui timestamp aktivitas terakhir
        self._last_active[sender] = datetime.now()

        # Tambahkan pesan dengan format struktur Gemini API
        self._history[sender].append({
            "role": role,
            "parts": [{"text": text}]
        })

        # Pangkas riwayat jika melebihi batas maksimum (ambil MAX_HISTORY pesan terakhir)
        if len(self._history[sender]) > MAX_HISTORY:
            self._history[sender] = self._history[sender][-MAX_HISTORY:]

    def clear(self, sender: str):
        """Menghapus riwayat percakapan pengirim dan mereset timestamp aktivitas.

        Args:
            sender (str): ID/nama pengirim.
        """
        self._history[sender] = []
        self._last_active[sender] = datetime.now()

    def stats(self, sender: str) -> dict:
        """Mengambil ringkasan statistik percakapan pengirim.

        Args:
            sender (str): ID/nama pengirim.

        Returns:
            dict: Ringkasan berisi total pesan, waktu aktivitas terakhir, dan status kedaluwarsa.
        """
        return {
            "total_pesan": len(self._history[sender]),
            "last_active": self._last_active[sender].strftime("%H:%M:%S"),
            "expired": self._is_expired(sender),
        }


# Instansiasi global untuk digunakan di modul lain
memory = Memory()