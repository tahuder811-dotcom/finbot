from datetime import datetime
import os
import threading
import time
from flask import Flask, jsonify, render_template_string, request
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

app = Flask(__name__)

# Konfigurasi Token Bot Telegram (Ambil dari Environment Variable Render atau isi langsung)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "TOKEN_BOT_KAMU_DISINI")
TELEGRAM_CHAT_ID = os.environ.get(
    "TELEGRAM_CHAT_ID", ""
)  # Opsional untuk push alert otomatis

# Database memori sementara untuk fitur terminal
trade_history = []
price_alerts = []  # List untuk menyimpan target alert harga user
active_symbol = "OANDA:XAUUSD"

# --- WEBSITE TERMINAL TRADING ---


@app.route("/")
def index():
  return render_template_string("""
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Finbot Pro Ultimate Trading Terminal</title>
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
        
        .calc-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 8px; }
        .input-group { display: flex; flex-direction: column; gap: 3px; }
        .input-label { font-size: 9px; color: #94a3b8; font-weight: 600; }
        .input-field { background: #1e293b; border: 1px solid #334155; color: white; padding: 6px; border-radius: 6px; font-size: 11px; font-family: monospace; outline: none; }
        
        .result-box { background: rgba(56, 189, 248, 0.05); border: 1px solid rgba(56, 189, 248, 0.2); padding: 8px; border-radius: 8px; font-size: 10px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
        .result-val { font-size: 12px; font-weight: 800; color: #38bdf8; font-family: monospace; }

        .btn-group { display: flex; gap: 6px; }
        .btn { flex: 1; padding: 10px; border: none; border-radius: 8px; font-weight: 800; font-size: 10px; cursor: pointer; text-align: center; transition: 0.2s; }
        .btn-buy { background: linear-gradient(135deg, #22c55e, #15803d); color: white; }
        .btn-sell { background: linear-gradient(135deg, #ef4444, #b91c1c); color: white; }
        .btn-action { background: #334155; color: white; }

        .log-container { max-height: 100px; overflow-y: auto; font-size: 9px; font-family: monospace; background: #0b101b; padding: 6px; border-radius: 6px; color: #cbd5e1; border: 1px solid rgba(255,255,255,0.03); }
        .log-item { padding: 3px 0; border-bottom: 1px solid rgba(255,255,255,0.02); }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ FINBOT ULTIMATE TERMINAL</h1>
            <div class="sub-header">Advanced Multi-Market & Risk Manager</div>
        </div>

        <div class="card">
            <div class="card-title"><span>Pilih Aset Pasar (TradingView)</span></div>
            <div class="selector-group">
                <select id="symbolSelect" class="select-symbol" onchange="changeSymbol()">
                    <option value="OANDA:XAUUSD">GOLD (XAUUSD)</option>
                    <option value="BINANCE:BTCUSDT">BITCOIN (BTCUSDT)</option>
                    <option value="BINANCE:ETHUSDT">ETHEREUM (ETHUSDT)</option>
                    <option value="FX:EURUSD">EUR/USD</option>
                </select>
            </div>
            
            <!-- TradingView Widget -->
            <div class="tradingview-widget-container" id="tv_chart_container"></div>
        </div>

        <div class="card">
            <div class="card-title"><span>Kalkulator Risiko & Ukuran Lot</span></div>
            <div class="calc-grid">
                <div class="input-group">
                    <span class="input-label">Modal Akun ($)</span>
                    <input type="number" id="accBalance" class="input-field" value="500" oninput="calculateLot()">
                </div>
                <div class="input-group">
                    <span class="input-label">Risiko (%)</span>
                    <input type="number" id="riskPercent" class="input-field" value="1" oninput="calculateLot()">
                </div>
                <div class="input-group">
                    <span class="input-label">Jarak SL (Pips)</span>
                    <input type="number" id="slPips" class="input-field" value="30" oninput="calculateLot()">
                </div>
                <div class="input-group">
                    <span class="input-label">Target Alert Harga</span>
                    <input type="number" id="alertPriceInput" class="input-field" placeholder="Cth: 2450">
                </div>
            </div>
            
            <div class="result-box">
                <div>Rekomendasi Lot Size: <span class="result-val" id="lotResult">0.03 Lot</span></div>
                <button onclick="setAlert()" class="btn btn-action" style="padding: 4px 8px; font-size: 9px;">Pasang Alert</button>
            </div>
            
            <div class="btn-group">
                <button onclick="recordTrade('BUY')" class="btn btn-buy">🟢 CATAT BUY</button>
                <button onclick="recordTrade('SELL')" class="btn btn-sell">🔴 CATAT SELL</button>
                <button onclick="clearLogs()" class="btn btn-action">RESET LOG</button>
            </div>
        </div>

        <div class="card">
            <div class="card-title"><span>Jurnal & Riwayat Aktivitas</span></div>
            <div class="log-container" id="logContainer">
                <div class="log-item">Sistem siap. Belum ada aktivitas tercatat.</div>
            </div>
        </div>
    </div>

    <!-- TradingView Script Loader -->
    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script type="text/javascript">
        let tvWidget = null;

        function loadChart(symbol) {
            document.getElementById('tv_chart_container').innerHTML = "";
            tvWidget = new TradingView.widget({
                "width": "100%",
                "height": "260",
                "symbol": symbol,
                "interval": "5",
                "timezone": "Asia/Jakarta",
                "theme": "dark",
                "style": "1",
                "locale": "id",
                "toolbar_bg": "#1e293b",
                "enable_publishing": false,
                "hide_side_toolbar": false,
                "container_id": "tv_chart_container"
            });
        }

        function changeSymbol() {
            const sym = document.getElementById('symbolSelect').value;
            loadChart(sym);
        }

        function calculateLot() {
            const balance = parseFloat(document.getElementById('accBalance').value) || 0;
            const risk = parseFloat(document.getElementById('riskPercent').value) || 0;
            const pips = parseFloat(document.getElementById('slPips').value) || 1;
            
            // Rumus sederhana kalkulasi risiko forex/gold
            const riskMoney = balance * (risk / 100);
            let lot = riskMoney / (pips * 10); // Asumsi standar $10 per pip untuk 1 lot standard
            if(lot < 0.01) lot = 0.01;
            document.getElementById('lotResult').innerText = lot.toFixed(2) + " Lot ($" + riskMoney.toFixed(2) + ")";
        }

        function recordTrade(action) {
            const sym = document.getElementById('symbolSelect').value;
            const lot = document.getElementById('lotResult').innerText;
            fetch('/api/journal', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: action, symbol: sym, details: lot})
            })
            .then(res => res.json())
            .then(data => {
                updateLogs(data.logs);
            });
        }

        function setAlert() {
            const price = document.getElementById('alertPriceInput').value;
            const sym = document.getElementById('symbolSelect').value;
            if(!price) return alert("Masukkan harga target alert!");
            
            fetch('/api/alert', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({price: price, symbol: sym})
            })
            .then(res => res.json())
            .then(data => {
                alert(data.message);
            });
        }

        function clearLogs() {
            fetch('/api/clear', {method: 'POST'})
            .then(() => updateLogs(["Riwayat dibersihkan."]));
        }

        function updateLogs(logs) {
            const container = document.getElementById('logContainer');
            container.innerHTML = "";
            logs.forEach(log => {
                let div = document.createElement('div');
                div.className = 'log-item';
                div.innerText = log;
                container.appendChild(div);
            });
        }

        // Load initial
        loadChart('OANDA:XAUUSD');
        calculateLot();
    </script>
</body>
</html>
    """)


@app.route("/api/journal", methods=["POST"])
def api_journal():
  req = request.json
  action = req.get("action")
  symbol = req.get("symbol")
  details = req.get("details")
  time_str = datetime.now().strftime("%H:%M:%S - %d %b")
  log_msg = f"[{time_str}] {action} {symbol} | Ukuran: {details}"
  trade_history.insert(0, log_msg)
  return jsonify({"status": "success", "logs": trade_history})


@app.route("/api/alert", methods=["POST"])
def api_alert():
  req = request.json
  price = req.get("price")
  symbol = req.get("symbol")
  price_alerts.append({"symbol": symbol, "price": float(price)})
  return jsonify({"status": "success", "message": f"Alert dipasang di {price}"})


@app.route("/api/clear", methods=["POST"])
def api_clear():
  trade_history.clear()
  return jsonify({"status": "success"})


# --- BAGIAN BOT TELEGRAM & BACKGROUND SCANNER ---


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_name = update.effective_user.first_name
  await update.message.reply_text(
      f"Halo {user_name}! ⚡ Finbot Ultimate siap melayani.\n\n"
      "Perintah yang tersedia:\n"
      "👉 `/price` - Cek harga emas terkini\n"
      "👉 `/status` - Cek status bot & alert aktif"
  )


async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  try:
    res = requests.get(
        "https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT", timeout=3
    )
    data = res.json()
    p = float(data["price"])
    await update.message.reply_text(
        f"🟡 **Harga Emas Spot Terkini:** `${p:,.2f}`", parse_mode="Markdown"
    )
  except:
    await update.message.reply_text("Gagal mengambil data harga pasar.")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text(
      f"🟢 Bot Aktif & Berjalan Normal.\nJumlah Price Alert aktif: {len(price_alerts)}"
  )


def run_telegram_bot():
  if TELEGRAM_TOKEN == "TOKEN_BOT_KAMU_DISINI":
    print("Token Telegram belum diatur!")
    return
  app_tg = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
  app_tg.add_handler(CommandHandler("start", start_command))
  app_tg.add_handler(CommandHandler("price", price_command))
  app_tg.add_handler(CommandHandler("status", status_command))
  print("Bot Telegram berjalan...")
  app_tg.run_polling()


if __name__ == "__main__":
  # Jalankan bot telegram di background thread
  tg_thread = threading.Thread(target=run_telegram_bot)
  tg_thread.daemon = True
  tg_thread.start()

  # Jalankan Flask Server di port utama Render
  app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
