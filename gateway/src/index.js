// gateway/src/index.js

// Mengimpor fungsi checkHealth dari modul bridge.js untuk memverifikasi ketersediaan Python Brain
import { checkHealth } from './bridge.js';
// Mengimpor fungsi connectWA dari modul whatsapp.js untuk menginisialisasi koneksi WhatsApp
import { connectWA }   from './whatsapp.js';
// Mengimpor objek konfigurasi utama aplikasi
import { config }      from './config.js';

// ── Banner ────────────────────────────────────────────────
// Tampilan spanduk ASCII art saat aplikasi Gateway diawali
console.log(`
╔══════════════════════════════════════════╗
║   🤖  CHEVY BOT — WhatsApp Gateway      ║
║        Powered by Python Brain           ║
╚══════════════════════════════════════════╝
`);

// ── Graceful shutdown ─────────────────────────────────────
// Menangani sinyal SIGINT (Ctrl+C di terminal) untuk mematikan aplikasi secara bersih
process.on('SIGINT',  () => { console.log('\n👋 Chevy gateway shutdown...'); process.exit(0); });
// Menangani sinyal SIGTERM (sinyal penghentian dari OS/Docker/Hosting)
process.on('SIGTERM', () => { console.log('\n👋 Chevy gateway shutdown...'); process.exit(0); });
// Menangkap dan mencatat error tak terduga yang tidak tertangani (uncaught exceptions) lalu menghentikan proses
process.on('uncaughtException',  err => { console.error('❌ Uncaught:', err); process.exit(1); });
// Menangkap promise yang ter-reject tanpa penanganan (unhandled rejections) agar aplikasi tidak crash tiba-tiba
process.on('unhandledRejection', err => { console.error('❌ Unhandled:', err); });

// ── Main ──────────────────────────────────────────────────
/**
 * Fungsi utama untuk menjalankan alur booting aplikasi Gateway.
 */
async function main() {
    // 1. Memeriksa status ketersediaan backend Python Brain
    console.log(`🔍 Cek Python brain di ${config.brainUrl}...`);
    const brainOk = await checkHealth();

    // Berikan peringatan jika Python Brain tidak merespons (misal service Uvicorn belum di-run)
    if (!brainOk) {
        console.warn(`⚠️  Python brain belum respond!`);
        console.warn(`   Pastikan uvicorn sudah jalan di port 8000\n`);
    } else {
        console.log(`✅ Python brain OK!\n`);
    }

    // 2. Menginisialisasi socket dan koneksi ke server WhatsApp
    console.log('🔌 Menghubungkan ke WhatsApp...');
    await connectWA();
}

// Mengeksekusi fungsi utama main() dan menangkap fatal error jika proses booting gagal
main().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
});