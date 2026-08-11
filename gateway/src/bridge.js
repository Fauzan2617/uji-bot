// gateway/src/bridge.js

// Mengimpor objek konfigurasi untuk mendapatkan URL endpoint Python Brain
import { config } from './config.js';

/**
 * Helper privat untuk mengirim HTTP POST Request ke service Python Brain.
 * @param {string} endpoint - Path endpoint API (misal: '/chat', '/image')
 * @param {object} body - Payload data dalam bentuk objek JavaScript
 */
async function post(endpoint, body) {
    const controller = new AbortController();
    const timeout    = setTimeout(() => controller.abort(), 30000);

    try {
        const res = await fetch(`${config.brainUrl}${endpoint}`, {
            method  : 'POST',
            headers : { 'Content-Type': 'application/json' },
            body    : JSON.stringify(body),
            signal  : controller.signal,
        });

        clearTimeout(timeout);

        if (!res.ok) {
            const err = await res.text();
            throw new Error(`Brain error ${res.status}: ${err}`);
        }

        return res.json();

    } catch (err) {
        clearTimeout(timeout);
        if (err.name === 'AbortError') {
            throw new Error('Request timeout — Python brain terlalu lama respond');
        }
        throw err;
    }
}

/**
 * Mengirimkan pesan teks ke Python Brain.
 * @param {string} sender - JID / Nomor WhatsApp pengirim
 * @param {string} text - Isi pesan teks
 */
export async function sendText(sender, text) {
    // Memanggil endpoint '/chat' dengan payload pengirim dan teks pesan
    return post('/chat', { sender, text });
}

/**
 * Mengirimkan berkas gambar ke Python Brain.
 * @param {string} sender - JID / Nomor WhatsApp pengirim
 * @param {Buffer} imageBuffer - Buffer data gambar mentah
 * @param {string} [caption=''] - Caption/keterangan gambar opsional
 */
export async function sendImage(sender, imageBuffer, caption = '') {
    // Mengonversi data Buffer gambar menjadi string berformat Base64
    const image_b64 = imageBuffer.toString('base64');
    
    // Memanggil endpoint '/image' dengan payload pengirim, string gambar Base64, dan caption
    return post('/image', { sender, image_b64, caption });
}

/**
 * Mengirimkan pesan suara (audio) ke Python Brain.
 * @param {string} sender - JID / Nomor WhatsApp pengirim
 * @param {Buffer} audioBuffer - Buffer data audio mentah
 */
export async function sendAudio(sender, audioBuffer) {
    // Mengonversi data Buffer audio menjadi string berformat Base64
    const audio_b64 = audioBuffer.toString('base64');
    
    // Memanggil endpoint '/audio' dengan payload pengirim dan string audio Base64
    return post('/audio', { sender, audio_b64 });
}

/**
 * Memeriksa status kesehatan/keterhubungan ke Python Brain.
 * @returns {Promise<boolean>} Return true jika server Brain aktif, false jika mati/terjadi error.
 */
export async function checkHealth() {
    try {
        // Mengirim permintaan HTTP GET ke endpoint '/health'
        const res = await fetch(`${config.brainUrl}/health`);
        // Mengembalikan nilai boolean berdasarkan status HTTP (200 OK)
        return res.ok;
    } catch {
        // Mengembalikan false jika koneksi gagal atau server Brain offline
        return false;
    }
}