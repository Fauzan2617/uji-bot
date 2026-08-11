// gateway/src/config.js

// Mengimpor dan mengonfigurasi pustaka 'dotenv' untuk membaca variabel lingkungan (.env)
import 'dotenv/config';

// Mengekspor objek konfigurasi utama aplikasi
export const config = {
    // URL endpoint service Python Brain (default: 'http://localhost:8000')
    brainUrl       : process.env.PYTHON_BRAIN_URL || 'http://localhost:8000',
    
    // Direktori tempat menyimpan file sesi/autentikasi WhatsApp (default: './src/auth/session')
    sessionDir     : process.env.SESSION_DIR      || './src/auth/session',
    
    // Daftar nomor telepon yang diizinkan (whitelist), dipisahkan dengan koma lalu dibersihkan dari spasi kosong
    allowedNumbers : (process.env.ALLOWED_NUMBERS || '')
                        .split(',')          // Memisah string berdasarkan tanda koma menjadi array
                        .map(n => n.trim())  // Menghapus spasi di awal/akhir tiap nomor
                        .filter(Boolean),    // Membuang elemen kosong dari array
    
    // Tingkat kedalaman pencatatan log aplikasi (default: 'info')
    logLevel       : process.env.LOG_LEVEL        || 'info',
    
    // Nomor port tempat server Gateway ini berjalan, dikonversi ke tipe data integer (default: 3000)
    port           : parseInt(process.env.PORT    || '3000'),
};