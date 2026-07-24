from datetime import datetime
import os
import threading
import time
from flask import Flask, jsonify, render_template_string, request
import requests
import telebot

TOKEN = "8914087726:AAGeuhs_0btpV97QnmgIDDGhEwHkzGtbvkM"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

trade_history = []
USER_CHAT_ID = None
price_alerts = []  # Menyimpan daftar target alert harga


@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
  json_string = request.get_data().decode("utf-8")
  update = telebot.types.Update.de_json(json_string)
  bot.process_new_updates([update])
  return "OK", 200


@app.route("/")
def index():
  return render_template_string("""
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Finbot Pro Ultimate Terminal</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', system-ui, sans-serif; }
        body { background-color: #060913; color: #f1f5f9; padding: 10px; display: flex; justify-content: center; min-height: 100vh; }
        .container { width: 100%; max-width: 480px; }
        .header { background: linear-gradient(135deg, #1e293b, #0f172a); padding: 12px; border-radius: 14px; border: 1px solid rgba(56, 189, 248, 0.2); margin-bottom: 10px; text-align: center; }
        h1 { font-size: 13px; font-weight: 800; color: #38bdf8; letter-spacing: 0.5px; }
        .sub-header { font-size: 9px; color: #94a3b8; margin-top: 2px; text-transform: uppercase; }
        .card { background: linear-gradient(180deg, #111827 0%, #0d1322 100%); padding: 12px; border-radius: 12px; margin-bottom: 10px; border: 1px solid rgba(255, 255, 255, 0.05); }
        .card-title { font-size: 10px; color: #94a3b8; text-transform: uppercase; font-weight: 700; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
        .selector-group { display: flex; gap: 6px; margin-bottom: 8px; }
        .select-symbol, .input-field { flex: 1; background: #1e293b; color: white; border: 1px solid #334155; padding: 6px; border-radius: 8px; font-size: 11px; font-weight: 600; outline: none; }
        .tradingview-widget-container { height: 220px; width: 100%; border-radius: 10px; overflow: hidden; margin-bottom: 10px; border: 1px solid rgba(255,255,255,0.05); }
        .btn-group { display: flex; gap: 6px; margin-top: 6px; }
        .btn { flex: 1; padding: 10px; border: none; border-radius: 8px; font-weight: 800; font-size: 10px; cursor: pointer; text-align: center; }
        .btn-buy { background: linear-gradient(135deg, #22c55e, #15803d); color: white; }
        .btn-sell { background: linear-gradient(135deg, #ef4444, #b91c1c); color: white; }
        .btn-calc { background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: white; margin-top: 6px; width: 100%; }
        .log-container { max-height: 100px; overflow-y: auto; font-size: 9px; font-family: monospace; background: #0b101b; padding: 6px; border-radius: 6px; color: #cbd5e1; border: 1px solid rgba(255,255,255,0.03); }
        .log-item { padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.02); }
        .calc-result { font-size: 10px; color: #38bdf8; margin-top: 6px; font-weight: bold; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ FINBOT ULTIMATE COMMAND</h1>
            <div class="sub-header">All-in-One Trading & Bot Engine</div>
        </div>
        
        <div class="card">
            <div class="card-title"><span>Grafik Market (TradingView)</span></div>
            <div class="selector-group">
                <select id="symbolSelect" class="select-symbol" onchange="changeSymbol()">
                    <option value="OANDA:XAUUSD">GOLD (XAUUSD)</option>
                    <option value="BINANCE:BTCUSDT">BITCOIN (BTCUSDT)</option>
                    <option value="BINANCE:ETHUSDT">ETHEREUM (ETHUSDT)</option>
                </select>
            </div>
            <div class="tradingview-widget-container" id="tv_chart_container"></div>
        </div>

        <div class="card">
            <div class="card-title"><span>Kalkulator Risiko & Lot</span></div>
            <div class="selector-group">
                <input type="number" id="capital" class="input-field" placeholder="Modal ($)" value="1000">
                <input type="number" id="riskPct" class="input-field" placeholder="Risiko (%)" value="1">
            </div>
            <button onclick="calculateRisk()" class="btn btn-calc">HITUNG UKURAN RISIKO</button>
            <div id="calcResult" class="calc-result"></div>
        </div>

        <div class="card">
            <div class="card-title"><span>Catat Posisi & Kirim ke Telegram</span></div>
            <div class="selector-group">
                <input type="text" id="tradeNotes" class="input-field" placeholder="Catatan/Target (Cth: TP 2450)">
            </div>
            <div class="btn-group">
                <button onclick="recordTrade('BUY')" class="btn btn-buy">🟢 BUY (AUTO PRICE)</button>
                <button onclick="recordTrade('SELL')" class="btn btn-sell">🔴 SELL (AUTO PRICE)</button>
            </div>
        </div>

        <div class="card">
            <div class="card-title"><span>Riwayat Jurnal Sesi Ini</span></div>
            <div class="log-container" id="logContainer">
                <div class="log-item">Sistem siap.</div>
            </div>
        </div>
    </div>

    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script type="text/javascript">
        let tvWidget = null;
        function loadChart(symbol) {
            document.getElementById('tv_chart_container').innerHTML = "";
            tvWidget = new TradingView.widget({
                "width": "100%", "height": "220", "symbol": symbol, "interval": "5",
                "timezone": "Asia/Jakarta", "theme": "dark", "style": "1", "locale": "id",
                "container_id": "tv_chart_container"
            });
        }
        function changeSymbol() { loadChart(document.getElementById('symbolSelect').value); }
        
        function calculateRisk() {
            const cap = parseFloat(document.getElementById('capital').value) || 0;
            const risk = parseFloat(document.getElementById('riskPct').value) || 0;
            const maxLoss = (cap * risk) / 100;
            document.getElementById('calcResult').innerText = `Maksimal Risiko Hilang: $${maxLoss.toFixed(2)}`;
        }

        function recordTrade(action) {
            const sym = document.getElementById('symbolSelect').value;
            const notes = document.getElementById('tradeNotes').value || "Tanpa Catatan";
            
            fetch('/api/journal', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: action, symbol: sym, notes: notes})
            }).then(res => res.json()).then(data => {
                const container = document.getElementById('logContainer');
                container.innerHTML = "";
                data.logs.forEach(log => {
                    let div = document.createElement('div');
                    div.className = 'log-item';
                    div.innerText = log;
                    container.appendChild(div);
                });
                document.getElementById('tradeNotes').value = "";
            });
        }
        loadChart('OANDA:XAUUSD');
        calculateRisk();
    </script>
</body>
</html>
    """)


@app.route("/api/journal", methods=["POST"])
def api_journal():
  global USER_CHAT_ID
  req = request.json
  action = req.get("action")
  symbol = req.get("symbol")
  notes = req.get("notes")
  time_str = datetime.now().strftime("%H:%M:%S - %d %b")

  current_price = "Market Price"
  try:
    if "BTC" in symbol:
      r = requests.get(
          "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=2
      )
      current_price = f"${float(r.json()['price']):,.2f}"
    elif "ETH" in symbol:
      r = requests.get(
          "https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT", timeout=2
      )
      current_price = f"${float(r.json()['price']):,.2f}"
    else:
      r = requests.get(
          "https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT", timeout=2
      )
      current_price = f"${float(r.json()['price']):,.2f} (Gold Spot)"
  except:
    pass

  log_msg = f"[{time_str}] {action} {symbol} @ {current_price} | {notes}"
  trade_history.insert(0, log_msg)

  if USER_CHAT_ID:
    try:
      emoji = "🟢" if action == "BUY" else "🔴"
      msg = (
          f"{emoji} **JURNAL TRADING TEREKAM**\n\n"
          f"🔹 **Aset:** `{symbol}`\n"
          f"🔹 **Aksi:** `{action}`\n"
          f"🔹 **Harga Saat Ini:** `{current_price}`\n"
          f"🔹 **Catatan:** `{notes}`\n"
          f"🕒 **Waktu:** `{time_str}`"
      )
      bot.send_message(USER_CHAT_ID, msg, parse_mode="Markdown")
    except Exception as e:
      print("Gagal kirim telegram:", e)

  return jsonify({"status": "success", "logs": trade_history})


# --- TELEGRAM COMMANDS ---
@bot.message_handler(commands=["start"])
def send_welcome(message):
  global USER_CHAT_ID
  USER_CHAT_ID = message.chat.id
  bot.reply_to(
      message,
      "⚡ **Finbot Ultimate Aktif!**\n\n"
      "Perintah yang tersedia:\n"
      "👉 `/price` - Cek harga emas terkini\n"
      "👉 `/alert [angka]` - Pasang alarm batas harga\n"
      "👉 `/recap` - Lihat rekap jumlah transaksi hari ini\n"
      "👉 `/meme` - Cek tren token/meme coin terbaru",
      parse_mode="Markdown",
  )


@bot.message_handler(commands=["price"])
def send_price(message):
  try:
    res = requests.get(
        "https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT", timeout=3
    )
    p = float(res.json()["price"])
    bot.reply_to(message, f"🟡 **Harga Emas Spot:** `${p:,.2f}`", parse_mode="Markdown")
  except:
    bot.reply_to(message, "Gagal mengambil data harga pasar.")


@bot.message_handler(commands=["alert"])
def set_alert(message):
  try:
    args = message.text.split()
    target_price = float(args[1])
    price_alerts.append(
        {"chat_id": message.chat.id, "target": target_price, "active": True}
    )
    bot.reply_to(
        message,
        f"🚨 **Alert Berhasil Dipasang!**\nBot akan memberitahu kamu jika harga emas menyentuh angka: `${target_price:,.2f}`",
        parse_mode="Markdown",
    )
  except:
    bot.reply_to(
        message, "Format salah. Gunakan contoh: `/alert 2450`", parse_mode="Markdown"
    )


@bot.message_handler(commands=["recap"])
def send_recap(message):
  total_trades = len(trade_history)
  buy_count = sum(1 for t in trade_history if "BUY" in t)
  sell_count = sum(1 for t in trade_history if "SELL" in t)

  recap_msg = (
      f"📊 **REKAP PERFORMA SESI INI**\n\n"
      f"• Total Transaksi: `{total_trades}`\n"
      f"• Total BUY: `{buy_count}`\n"
      f"• Total SELL: `{sell_count}`"
  )
  bot.reply_to(message, recap_msg, parse_mode="Markdown")


@bot.message_handler(commands=["meme"])
def check_meme(message):
  try:
    url = "https://api.dexscreener.com/latest/dex/search?q=SOL"
    res = requests.get(url, timeout=5).json()
    pairs = res.get("pairs", [])[:3]

    msg = "🚀 **TRENDING MEME / TOKEN TERBARU**\n\n"
    for p in pairs:
      name = p.get("baseToken", {}).get("name", "N/A")
      symbol = p.get("baseToken", {}).get("symbol", "N/A")
      price = p.get("priceUsd", "0")
      dex = p.get("dexId", "DEX")
      msg += (
          f"• **{name} ({symbol})**\n  DEX: `{dex}` | Harga: `${price}`\n\n"
      )

    bot.reply_to(message, msg, parse_mode="Markdown")
  except Exception as e:
    bot.reply_to(message, "Gagal mengambil data token.")


def background_price_checker():
  while True:
    try:
      res = requests.get(
          "https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT", timeout=3
      )
      current_p = float(res.json()["price"])

      for alert in price_alerts:
        if alert["active"] and current_p >= alert["target"]:
          bot.send_message(
              alert["chat_id"],
              f"🚨 **TARGET ALERT TERCAPAI!**\nHarga emas saat ini telah menyentuh: `${current_p:,.2f}`",
              parse_mode="Markdown",
          )
          alert["active"] = False
    except:
      pass
    time.sleep(30)


if __name__ == "__main__":
  RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
  if RENDER_URL:
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")

  t = threading.Thread(target=background_price_checker)
  t.daemon = True
  t.start()

  app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
