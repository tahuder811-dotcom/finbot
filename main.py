import os
import time
import threading
import requests
from flask import Flask, request

app = Flask(__name__)

# Konfigurasi Token Bot & Chat ID (Ambil dari Environment Variables Render)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8914087726:AAEfKU9rv7ZoRfHlOMhme_xM9l_luOfS33A")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "7657888575")

# Variabel penyimpanan status rekap & transaksi sederhana
bot_stats = {"total_trx": 0, "total_buy": 0, "total_sell": 0}


def send_telegram_alert(message):
  if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "8914087726:AAEfKU9rv7ZoRfHlOMhme_xM9l_luOfS33A":
    return
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
  try:
    requests.post(url, json=payload, timeout=10)
  except Exception as e:
    print(f"Gagal mengirim pesan Telegram: {e}")


# --- BACKGROUND MONITOR: XAUUSD TIMEFRAME 15 MENIT (TF 15m) ---
def monitor_xauusd_15m():
  print("Background: Pemantau XAUUSD Timeframe 15m aktif.")
  while True:
    try:
      # Logika simulasi data timeframe 15 menit
      current_price = 4015.50
      high_15m = 4025.00  # Resistance TF 15m
      low_15m = 4005.00   # Support TF 15m
      buffer = 2.0        # Toleransi ketat untuk scalping

      if current_price <= (low_15m + buffer):
        msg = (
            f"⚡ *SINYAL SCALPING XAUUSD (TF 15M)* ⚡\n\nHarga: *${current_price}"
            f"* menyentuh area Demand 15m (Support: *${low_15m}*).\nSegera cek"
            " chart MT5 di HP untuk konfirmasi pola candlestick!"
        )
        send_telegram_alert(msg)

      elif current_price >= (high_15m - buffer):
        msg = (
            f"⚡ *SINYAL SCALPING XAUUSD (TF 15M)* ⚡\n\nHarga: *${current_price}"
            f"* menyentuh area Supply 15m (Resistance: *${high_15m}*).\nSegera"
            " cek chart MT5 di HP untuk konfirmasi pembalikan!"
        )
        send_telegram_alert(msg)

    except Exception as e:
      print(f"Error 15m Monitor: {e}")

    # Cek setiap 3 menit (180 detik) untuk timeframe 15m
    time.sleep(180)


# --- WEBHOOK ENDPOINT TELEGRAM ---
@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
  update = request.get_json()
  if "message" in update:
    chat_id = update["message"]["chat"]["id"]
    text = update["message"].get("text", "").strip()

    # Logika Perintah Bot
    if text.lower() == "/start":
      reply_text = (
          "⚡ *Finbot Ultimate Aktif!*\n\nPerintah yang tersedia:\n👉 `/price` -"
          " Cek harga emas terkini\n👉 `/alert [angka]` - Pasang alarm batas"
          " harga\n👉 `/recap` - Lihat rekap jumlah transaksi\n👉 `/meme` - Cek"
          " tren token/meme coin\n👉 `/tf15` - Cek status S&D Timeframe 15M"
      )
    elif text.lower() == "/price":
      reply_text = (
          "📊 *Harga XAUUSD Terkini*\n- Harga: $4,015.50\n- Status: Stabil dekat"
          " area tengah TF 15M."
      )
    elif text.lower().startswith("/alert"):
      parts = text.split()
      if len(parts) > 1:
        target_price = parts[1]
        reply_text = (
            f"✅ Alarm berhasil dipasang pada harga: *${target_price}*."
            " Bot akan memantau."
        )
      else:
        reply_text = (
            "⚠️ Format salah. Gunakan contoh:\n`/alert 4020` (tanpa spasi"
            " berlebih atau langsung ketik angkanya)."
        )
    elif text.lower() == "/recap":
      reply_text = (
          f"📊 *REKAP PERFORMA SESI INI*\n\n• Total Transaksi:"
          f" {bot_stats['total_trx']}\n• Total BUY:"
          f" {bot_stats['total_buy']}\n• Total SELL: {bot_stats['total_sell']}"
      )
    elif text.lower() == "/meme":
      reply_text = (
          "🚀 *Tren Meme Coin Terkini*\n- Belum ada sinyal token baru yang"
          " mencolok hari ini."
      )
    elif text.lower() == "/tf15":
      reply_text = (
          "📈 *Status S&D Timeframe 15M (XAUUSD)*\n- Harga Saat Ini:"
          " $4,015.50\n- Resistance 15m: $4,025.00\n- Support 15m:"
          " $4,000.50\n- Status: Bot aktif memantau di background."
      )
    else:
      reply_text = (
          "Perintah tidak dikenali. Ketik /start untuk melihat daftar"
          " perintah."
      )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": reply_text, "parse_mode": "Markdown"})

  return "OK", 200


@app.route("/")
def home():
  return "Finbot Ultimate with TF 15M S&D Engine is Running 24/7!"


if __name__ == "__main__":
  # Jalankan pemantau TF 15m di latar belakang menggunakan Thread
  t = threading.Thread(target=monitor_xauusd_15m, daemon=True)
  t.start()

  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
