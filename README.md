# 🤖 UJI Bot — WhatsApp AI Assistant

Bot WhatsApp pribadi dengan arsitektur hybrid:
- 🟨 **Gateway** (Node.js) — koneksi WhatsApp via Baileys
- 🐍 **Brain** (Python) — AI logic via Google Gemini

## Setup
Lihat masing-masing folder:
- [gateway/README.md](gateway/)
- [brain/README.md](brain/)

## Cara Jalankan
Terminal 1 (Python brain):
cd brain && uvicorn main:app --reload

Terminal 2 (JS gateway):
cd gateway && npm start
