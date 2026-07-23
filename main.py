import os
import threading
import time
import requests
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

TOKEN = "8914087726:AAGeuhs_0btpV97QnmgIDDGhEwHkzGtbvkM"
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}/"

# Data state sementara
app_state = {
    "last_action": "Belum ada aksi",
    "updated_at": "-"
}

def send_telegram_notification(message):
    """Fungsi agar Web bisa mengirim pesan otomatis ke Telegram"""
    try:
        # Kirim broadcast ke chat/channel yang aktif (bisa disesuaikan dengan ID Anda)
        # Untuk tes awal, kita ambil update terakhir untuk mendapatkan chat_id aktif
        res = requests.get(TELEGRAM_API + "getUpdates", timeout=10)
        data = res.json()
        if data.get("ok") and data.get("result"):
            chat_id = data["result"][-1]["message"]["chat"]["id"]
            requests.post(TELEGRAM_API + "sendMessage", json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            })
    except Exception as e:
        print(f"Gagal kirim telegram: {e}")

# HTML & CSS Dashboard dengan TradingView Widget & Desain Cakep
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Finbot Pro - Trading Dashboard & Analyzer</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background-color: #0b0f19; color: #f8fafc; padding: 12px; display: flex; justify-content: center; min-height: 100vh; }
        .container { width: 100%; max-width: 480px; }
        .header { background: linear-gradient(135deg, #1e293b, #0f172a); padding: 20px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); border: 1px solid #334155; margin-bottom: 15px; text-align: center; }
        h1 { font-size: 20px; color: #38bdf8; margin-bottom: 4px; letter-spacing: 0.5px; }
        .subtitle { font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 600; }
        
        .card { background-color: #1e293b; padding: 16px; border-radius: 14px; margin-bottom: 15px; border: 1px solid #334155; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
        .card-title { font-size: 12px; color: #94a3b8; text-transform: uppercase; font-weight: bold; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
        
        /* TradingView Widget Container */
        .tradingview-widget-container { height: 350px; width: 100%; border-radius: 10px; overflow: hidden; margin-bottom: 15px; border: 1px solid #334155; }
        
        .status-val { font-size: 14px; font-weight: bold; color: #fbbf24; background: #0f172a; padding: 10px; border-radius: 8px; border: 1px solid #334155; }
        
        .btn-group { display: flex; gap: 12px; margin-top: 15px; }
        .btn { flex: 1; padding: 14px; border: none; border-radius: 10px; font-weight: bold; font-size: 15px; cursor: pointer; text-align: center; text-decoration: none; transition: transform 0.1s, opacity 0.2s; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        .btn:active { transform: scale(0.97); }
        .btn-buy { background: linear-gradient(135deg, #22c55e, #16a34a); color: white; }
        .btn-sell { background: linear-gradient(135deg, #ef4444, #dc2626); color: white; }
        
        .footer-info { margin-top: 10px; font-size: 11px; text-align: center; color: #64748b; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 FINBOT PRO ANALYZER</h1>
            <div class="subtitle">Live Forex, Gold & Crypto Command Center</div>
        </div>
        
        <!-- TradingView Advanced Real-time Chart Widget -->
        <div class="tradingview-widget-container">
            <div class="tradingview-widget-container__widget" style="height:100%;width:100%"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
            {
              "width": "100%",
              "height": "100%",
              "symbol": "OANDA:XAUUSD",
              "interval": "15",
              "timezone": "Asia/Jakarta",
              "theme": "dark",
              "style": "1",
              "locale": "id",
              "enable_publishing": false,
              "hide_top_toolbar": false,
              "save_image": false,
              "calendar": false,
              "studies": ["RASI@tv-basicstudies", "MASimple@tv-basicstudies"],
              "support_host": "https://www.tradingview.com"
            }
            </script>
        </div>

        <div class="card">
            <div class="card-title"><span>Jurnal Aksi Terakhir</span> 🟢 Terhubung Telegram</div>
            <div class="status-val">{{ state.last_action }}</div>
        </div>

        <form method="POST" action="/execute">
            <div class="btn-group">
                <button type="submit" name="action" value="BUY XAUUSD" class="btn btn-buy">🟢 EKSEKUSI BUY</button>
                <button type="submit" name="action" value="SELL XAUUSD" class="btn btn-sell">🔴 EKSEKUSI SELL</button>
            </div>
        </form>

        <div class="footer-info">
            Server Status: Online 24/7 di Render | Update: {{ state.updated_at }}
        </div>
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, state=app_state)

@app.route("/execute", methods=["POST"])
def execute():
    action = request.form.get("action")
    timestamp = time.strftime('%H:%M:%S - %d %b %Y')
    
    app_state["last_action"] = f"Berhasil mencatat: {action} ({timestamp})"
    app_state["updated_at"] = timestamp
    
    # Kirim notifikasi otomatis langsung ke Telegram Anda
    msg = f"🚨 *PANEL KENDALI WEB*\n\nAksi Berhasil Dicatat:\n📌 *{action}*\n⏰ Waktu: `{timestamp}`"
    send_telegram_notification(msg)
    
    return redirect(url_for('index'))

def telegram_listener():
    offset = 0
    while True:
        try:
            response = requests.get(TELEGRAM_API + f"getUpdates?offset={offset}&timeout=30", timeout=35)
            data = response.json()
            if data.get("ok"):
                for result in data.get("result", []):
                    offset = result["update_id"] + 1
                    if "message" in result:
                        msg = result["message"]
                        chat_id = msg["chat"]["id"]
                        text = msg.get("text", "")
                        if text == "/start":
                            requests.post(TELEGRAM_API + "sendMessage", json={
                                "chat_id": chat_id,
                                "text": "🚀 *FINBOT PRO AKTIF*\n\nWeb Analyzer & Chart Real-time sudah siap:\n🔗 https://finbot-whro.onrender.com",
                                "parse_mode": "Markdown"
                            })
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    t = threading.Thread(target=telegram_listener, daemon=True)
    t.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
