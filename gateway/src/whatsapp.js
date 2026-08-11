// gateway/src/whatsapp.js

// Mengimpor fungsi-fungsi utama dari library Baileys untuk manajemen koneksi WhatsApp
import {
    makeWASocket,
    useMultiFileAuthState,
    DisconnectReason,
    fetchLatestBaileysVersion,
} from '@whiskeysockets/baileys';
// Mengimpor Boom untuk penanganan error/HTTP status code
import { Boom }          from '@hapi/boom';
// Mengimpor library qrcode-terminal untuk menampilkan QR code di terminal/konsol
import qrcode            from 'qrcode-terminal';
// Mengimpor fungsi mkdir dari modul fs/promises untuk membuat direktori secara asinkron
import { mkdir }         from 'fs/promises';
// Mengimpor konfigurasi aplikasi
import { config }        from './config.js';
// Mengimpor handler utama penanganan pesan masuk
import { handleMessage } from './handler.js';

// Variabel untuk menghitung jumlah percobaan rekoneksi jika koneksi terputus
let reconnectCount = 0;

/**
 * Membuka dan mengelola koneksi socket WhatsApp secara asinkron.
 * @returns {Promise<object>} Instance socket Baileys yang aktif.
 */
export async function connectWA() {
    // Memastikan folder penyimpanan sesi dibuat jika belum ada (secara rekursif)
    await mkdir(config.sessionDir, { recursive: true });

    // Memuat atau menginisialisasi state autentikasi sesi berbasis multi-file
    const { state, saveCreds } = await useMultiFileAuthState(config.sessionDir);
    // Mengambil versi protokol WhatsApp/Baileys terbaru dari server
    const { version }          = await fetchLatestBaileysVersion();

    // Inisialisasi instance socket Baileys dengan parameter konfigurasi
    const sock = makeWASocket({
        version,                                     // Versi protokol Baileys
        auth               : state,                  // State kredensial autentikasi
        printQRInTerminal  : false,                  // Menonaktifkan QR bawaan Baileys (karena menggunakan qrcode-terminal manual)
        browser            : ['Chevy Bot', 'Chrome', '124.0'], // Identitas browser/klien saat login
        markOnlineOnConnect: true,                   // Menandai akun otomatis online saat terhubung
        syncFullHistory    : false,                  // Menonaktifkan sinkronisasi seluruh riwayat lama agar lebih cepat
    });

    // ── QR & Connection event ──────────────────────────────
    // Mendengarkan pembaruan status koneksi WhatsApp
    sock.ev.on('connection.update', async ({ connection, lastDisconnect, qr }) => {

        // Jika QR Code diterima dari WhatsApp, tampilkan ke terminal
        if (qr) {
            console.log('\n╔══════════════════════════════════════════╗');
            console.log('║   SCAN QR INI DI WHATSAPP MAS!           ║');
            console.log('╚══════════════════════════════════════════╝');
            qrcode.generate(qr, { small: true });    // Tampilkan gambar QR kecil di terminal
            console.log('📱 WA → Linked Devices → Link a Device\n');
        }

        // Jika status koneksi berhasil terbuka (online)
        if (connection === 'open') {
            reconnectCount = 0;                      // Reset hitungan rekoneksi ke angka 0
            const number   = sock.user?.id?.split(':')[0]; // Ambil nomor telepon bot dari ID penggunanya
            console.log('\n╔══════════════════════════════════════════╗');
            console.log('║   ✅  CHEVY ONLINE & SIAP!                ║');
            console.log(`║   📱  ${number?.padEnd(36)}║`);
            console.log('╚══════════════════════════════════════════╝\n');
        }

        // Jika koneksi terputus (closed)
        if (connection === 'close') {
            // Ekstrak status code dari error pemutusan hubungan
            const code = new Boom(lastDisconnect?.error)?.output?.statusCode;

            // Jika error dikarenakan sesi telah logout/dikeluarkan dari HP
            if (code === DisconnectReason.loggedOut) {
                console.error('❌ Logged out! Hapus folder session dan scan QR ulang.');
                process.exit(1);                     // Hentikan proses aplikasi
            } 
            // Jika terputus karena masalah jaringan dan percobaan kurang dari 10 kali
            else if (reconnectCount < 10) {
                reconnectCount++;                    // Tambahkan hitungan percobaan rekoneksi
                // Hitung jeda waktu tunggu bertahap (exponential backoff, maks 30 detik)
                const delay = Math.min(5000 * reconnectCount, 30000);
                console.log(`🔄 Reconnect dalam ${delay / 1000}s... (${reconnectCount}/10)`);
                // Jalankan ulang fungsi connectWA setelah waktu jeda terpenuhi
                setTimeout(connectWA, delay);
            } 
            // Jika sudah melebihi batas percobaan rekoneksi (>= 10)
            else {
                console.error('❌ Terlalu banyak reconnect. Bot berhenti.');
                process.exit(1);                     // Hentikan proses aplikasi
            }
        }
    });

    // ── Simpan session ────────────────────────────────────
    // Mendengarkan perubahan kredensial dan menyimpannya secara otomatis ke folder session
    sock.ev.on('creds.update', saveCreds);

    // ── Pesan masuk ───────────────────────────────────────
    // Mendengarkan setiap event pesan masuk/baru di WhatsApp
    sock.ev.on('messages.upsert', async (event) => {
        // Hanya proses jika jenis event adalah pesan baru/notifikasi (notify)
        if (event.type !== 'notify') return;
        // Teruskan event pesan ke handler pesan di handler.js
        await handleMessage(sock, event);
    });

    // Mengembalikan instance socket
    return sock;
}