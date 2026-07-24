from datetime import datetime
import os
import threading
from flask import Flask, jsonify, render_template_string, request
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

app = Flask(__name__)
trade_history = []

# Token Telegram kamu sudah dipasang langsung di sini
TELEGRAM_TOKEN = "8914087726:AAGeuhs_0btpV97QnmgIDDGhEwHkzGtbvkM"


@app.route("/")
def index():
  return render_template_string("""
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Finbot Pro Trading Terminal</title>
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
        .select-symbol { flex: 1; background: #1e293b; color: white; border: 1px solid #334155; padding: 6px; border-radius: 8px; font-size: 11px; font-weight: 600; outline: none; }
        .tradingview-widget-container { height: 260px; width: 100%; border-radius: 10px; overflow: hidden; margin-bottom: 10px; border: 1px solid rgba(255,255,255,0.05); }
        .btn-group { display: flex; gap: 6px; }
        .btn { flex: 1; padding: 10px; border: none; border-radius: 8px; font-weight: 800; font-size: 10px; cursor: pointer; text-align: center; }
        .btn-buy { background: linear-gradient(135deg, #22c55e, #15803d); color: white; }
        .btn-sell { background: linear-gradient(135deg, #ef4444, #b91c1c); color: white; }
        .log-container { max-height: 100px; overflow-y: auto; font-size: 9px; font-family: monospace; background: #0b101b; padding: 6px; border-radius: 6px; color: #cbd5e1; border: 1px solid rgba(255,255,255,0.03); }
        .log-item { padding: 3px 0; border-bottom: 1px solid rgba(255,255,255,0.02); }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ FINBOT ULTIMATE TERMINAL</h1>
            <div class="sub-header">Advanced Multi-Market Engine</div>
        </div>
        <div class="card">
            <div class="card-title"><span>Pilih Aset Pasar (TradingView)</span></div>
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
            <div class="card-title"><span>Aksi Cepat Jurnal</span></div>
            <div class="btn-group">
                <button onclick="recordTrade('BUY')" class="btn btn-buy">🟢 CATAT BUY</button>
                <button onclick="recordTrade('SELL')" class="btn btn-sell">🔴 CATAT SELL</button>
            </div>
        </div>
        <div class="card">
            <div class="card-title"><span>Riwayat Aktivitas</span></div>
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
                "width": "100%", "height": "260", "symbol": symbol, "interval": "5",
                "timezone": "Asia/Jakarta", "theme": "dark", "style": "1", "locale": "id",
                "container_id": "tv_chart_container"
            });
        }
        function changeSymbol() { loadChart(document.getElementById('symbolSelect').value); }
        function recordTrade(action) {
            const sym = document.getElementById('symbolSelect').value;
            fetch('/api/journal', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: action, symbol: sym})
            }).then(res => res.json()).then(data => {
                const container = document.getElementById('logContainer');
                container.innerHTML = "";
                data.logs.forEach(log => {
                    let div = document.createElement('div');
                    div.className = 'log-item';
                    div.innerText = log;
                    container.appendChild(div);
                });
            });
        }
        loadChart('OANDA:XAUUSD');
    </script>
</body>
</html>
    """)


@app.route("/api/journal", methods=["POST"])
def api_journal():
  req = request.json
  action = req.get("action")
  symbol = req.get("symbol")
  time_str = datetime.now().strftime("%H:%M:%S - %d %b")
  log_msg = f"[{time_str}] {action} {symbol}"
  trade_history.insert(0, log_msg)
  return jsonify({"status": "success", "logs": trade_history})


# --- TELEGRAM BOT HANDLERS ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text(
      "⚡ Finbot Telegram Aktif!\nKetik /price untuk cek harga emas."
  )


async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  try:
    res = requests.get(
        "https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT", timeout=3
    )
    p = float(res.json()["price"])
    await update.message.reply_text(f"🟡 **Harga Emas Spot:** `${p:,.2f}`")
  except:
    await update.message.reply_text("Gagal mengambil data harga.")


def run_telegram_bot():
  application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
  application.add_handler(CommandHandler("start", start_command))
  application.add_handler(CommandHandler("price", price_command))
  print("Memulai polling bot Telegram...")
  application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
  bot_thread = threading.Thread(target=run_telegram_bot)
  bot_thread.daemon = True
  bot_thread.start()

  app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
