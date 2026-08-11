// gateway/src/handler.js

// Mengimpor fungsi penunduh media dari pustaka Baileys
import { downloadMediaMessage } from '@whiskeysockets/baileys';
// Mengimpor fungsi jembatan (bridge) untuk komunikasi ke Python Brain
import { sendText, sendImage, sendAudio } from './bridge.js';
// Mengimpor objek konfigurasi aplikasi
import { config } from './config.js';

import sharp from 'sharp';

// ── Security check ────────────────────────────────────────
/**
 * Memeriksa apakah pengirim berada dalam daftar nomor yang diizinkan (whitelist).
 * @param {string} jid - JID pengirim WhatsApp (contoh: '628123456789@s.whatsapp.net')
 * @returns {boolean} True jika diizinkan, False jika ditolak.
 */
function isAllowed(jid) {
    const number = jid
        .replace('@s.whatsapp.net', '')
        .replace('@lid', '')
        .replace('@c.us', '')
        .trim();

    console.log('📌 JID masuk    :', jid);
    console.log('📌 Number parsed:', number);
    console.log('📌 Allowed list :', config.allowedNumbers);

    if (config.allowedNumbers.length === 0) return true;

    return config.allowedNumbers.some(allowed =>
        allowed === number ||
        number.endsWith(allowed.slice(-10))
    );
}

// ── Reply helper ──────────────────────────────────────────
/**
 * Helper untuk membalas pesan ke pengguna secara konsisten.
 * @param {object} sock - Socket koneksi Baileys
 * @param {string} jid - Target JID penerima
 * @param {string} text - Pesan balasan
 * @param {object} [quoted] - Objek pesan asal yang di-quote/dibalas (opsional)
 */
async function reply(sock, jid, text, quoted) {
    await sock.sendMessage(jid, {
        text,
        ...(quoted ? { quoted } : {}), // Sertakan opsi quote jika objek 'quoted' tersedia
    });
}

// ── Main handler ──────────────────────────────────────────
/**
 * Handler utama untuk memproses event pesan masuk dari WhatsApp.
 * @param {object} sock - Socket koneksi Baileys
 * @param {object} messageEvent - Objek event pesan dari Baileys
 */
export async function handleMessage(sock, messageEvent) {
    // Mengambil objek pesan pertama dari array event messages
    const msg = messageEvent.messages?.[0];

    // Abaikan jika tidak ada pesan atau jika pesan dikirim oleh bot sendiri
    if (!msg || msg.key.fromMe) return;

    // Mengambil JID pengirim/obrolan
    const jid     = msg.key.remoteJid;
    // Mengambil payload isi pesan
    const content = msg.message;

    // Abaikan jika struktur pesan tidak memiliki isi/konten
    if (!content) return;

    // Abaikan jika pesan berasal dari grup obrolan (hanya menerima pesan pribadi/DM)
    if (jid.endsWith('@g.us')) return;

    // Lakukan pemeriksaan keamanan whitelist
    if (!isAllowed(jid)) {
        console.warn(`⛔ Blocked: ${jid}`);
        return;
    }

    try {

        // ── TEKS ──────────────────────────────────────────
        // Menangani pesan berupa teks biasa atau teks percakapan panjang
        if (content.conversation || content.extendedTextMessage) {
            // Ekstrak teks pesan dari salah satu properti yang tersedia
            const text = (
                content.conversation ||
                content.extendedTextMessage?.text || ''
            ).trim();

            // Abaikan jika string teks ternyata kosong
            if (!text) return;

            // Catat log penerimaan pesan teks
            console.log(`📨 [${jid}] ${text.slice(0, 60)}`);

            // Ubah status kehadiran menjadi 'composing' (mengetik...)
            await sock.sendPresenceUpdate('composing', jid);
            // Kirim pesan teks ke Python Brain dan tunggu balasannya
            const res = await sendText(jid, text);
            // Hentikan indikator status mengetik
            await sock.sendPresenceUpdate('paused', jid);

            // Kirim balasan teks dari AI ke pengguna di WhatsApp
            await reply(sock, jid, res.reply, msg);
        }

        // ── GAMBAR ────────────────────────────────────────
        // Menangani pesan yang berisi media gambar
        else if (content.imageMessage) {
    const caption = content.imageMessage.caption || '';

    console.log(`📸 [${jid}] Gambar diterima`);
    await reply(sock, jid, `🔍 Sebentar mas, Chevy lagi analisa gambarnya...`);
    await sock.sendPresenceUpdate('composing', jid);

    try {
        const buffer = await downloadMediaMessage(msg, 'buffer', {});

        // Kompres gambar sebelum kirim ke Python
        const compressed = await sharp(buffer)
            .resize(800, 800, {
                fit               : 'inside',
                withoutEnlargement: true,
            })
            .jpeg({ quality: 80 })
            .toBuffer();

        console.log(`📸 ${buffer.length} bytes → ${compressed.length} bytes`);

        const res = await sendImage(jid, compressed, caption);

        await sock.sendPresenceUpdate('paused', jid);
        await reply(sock, jid, res.reply, msg);

    } catch (err) {
        await sock.sendPresenceUpdate('paused', jid);
        console.error('❌ Image error:', err.message);
        await reply(sock, jid, `⚠️ Gagal proses gambar mas: ${err.message}`);
    }
}

        // ── AUDIO / VOICE NOTE ────────────────────────────
        // Menangani pesan yang berisi media audio/voice note
        else if (content.audioMessage) {
            console.log(`🎤 [${jid}] Voice note diterima`);

            // Kirim pesan konfirmasi awal bahwa audio sedang diproses
            await reply(sock, jid, `🎤 Sebentar mas, Chevy lagi dengerin...`);
            // Aktifkan indikator status mengetik
            await sock.sendPresenceUpdate('composing', jid);

            // Unduh file media audio sebagai Buffer
            const buffer = await downloadMediaMessage(msg, 'buffer', {});
            // Kirim buffer audio ke Python Brain
            const res    = await sendAudio(jid, buffer);

            // Hentikan indikator status mengetik
            await sock.sendPresenceUpdate('paused', jid);
            // Kirim balasan/transkripsi AI ke pengguna
            await reply(sock, jid, res.reply, msg);
        }

        // ── DOKUMEN ───────────────────────────────────────
        // Menangani pesan yang berisi file dokumen (PDF, Docx, dll)
        else if (content.documentMessage) {
            await reply(sock, jid, `📄 Dokumen diterima mas! Fitur baca dokumen coming soon ya 🚧`);
        }

        // ── STIKER ────────────────────────────────────────
        // Menangani pesan yang berisi stiker
        else if (content.stickerMessage) {
            await reply(sock, jid, `😄 Stiker lucu mas!`);
        }

    } catch (err) {
        // Tangkap dan catat log jika terjadi kesalahan selama eksekusi
        console.error(`❌ Error:`, err.message);
        // Hentikan indikator status mengetik jika masih aktif
        await sock.sendPresenceUpdate('paused', jid);
        // Kirim pesan error ke pengguna
        await reply(sock, jid,
            `⚠️ Maaf mas, ada error. Coba lagi ya!\n_(${err.message})_`
        );
    }
}