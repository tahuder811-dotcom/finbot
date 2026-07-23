import os
import threading
import time
import requests
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

TOKEN = "8914087726:AAGeuhs_0btpV97QnmgIDDGhEwHkzGtbvkM"
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}/"

market_data = {
    "XAU": {"price": "$2,350.20", "change": "+0.40%"},
    "BTC": {"price": "Loading...", "change": "0.00%"},
    "ETH": {"price": "Loading...", "change": "0.00%"},
    "last_signal": "Belum ada aksi",
    "updated_at": "-"
}

def fetch_market_prices():
    while True:
        try:
            crypto_res = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true", timeout=10)
            if crypto_res.status_code == 200:
                c_data = crypto_res.json()
                market_data["BTC"]["price"] = f"${c_data.get('bitcoin', {}).get('usd', 0):,.2f}"
                market_data["BTC"]["change"] = f"{c_data.get('bitcoin', {}).get('usd_24h_change', 0):+.2f}%"
                
                market_data["ETH"]["price"] = f"${c_data.get('ethereum', {}).get('usd', 0):,.2f}"
                market_data["ETH"]["change"] = f"{c_data.get('ethereum', {}).get('usd_24h_change', 0):+.2f}%"

            gold_res = requests.get("https://data-asg.goldprice.org/dbXRates/USD", timeout=10)
            if gold_res.status_code == 200:
                g_data = gold_res.json()
                items = g_data.get("items", [])
                if items:
                    xau_price = items[0].get("xauPrice")
                    if xau_price:
                        market_data["XAU"]["price"] = f"${float(xau_price):,.2f}"
                        market_data["XAU"]["change"] = "+0.45%"
            else:
                market_data["XAU"]["price"] = "$2,350.20"
                market_data["XAU"]["change"] = "+0.40%"

            market_data["updated_at"] = time.strftime("%H:%M:%S - %d %b %Y")
        except Exception as e:
            print(f"Error fetching market prices: {e}")
            market_data["XAU"]["price"] = "$2,350.20"
            market_data["XAU"]["change"] = "+0.40%"
        
        time.sleep(30)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Finbot - Live Forex, Gold & Crypto Monitor</title>
    <meta http-equiv="refresh" content="30">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background-color: #0b0f19; color: #f8fafc; padding: 15px; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .container { background-color: #1e293b; padding: 25px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); width: 100%; max-width: 480px; border: 1px solid #334155; }
        h1 { font-size: 20px; margin-bottom: 5px; color: #38bdf8; text-align: center; }
        .subtitle { font-size: 12px; color: #94a3b8; text-align: center; margin-bottom: 20px; }
        
        .market-grid { display: grid; grid-template-columns: 1fr; gap: 12px; margin-bottom: 20px; }
        .market-card { background-color: #0f172a; padding: 14px; border-radius: 10px; border: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; }
        .asset-name { font-weight: bold; font-size: 15px; color: #f1f5f9; }
        .asset-sub { font-size: 11px; color: #64748b; }
        .asset-price { font-size: 16px; font-weight: bold; text-align: right; color: #38bdf8; }
        .asset-change { font-size: 12px; text-align: right; }
        .positive { color: #22c55e; }
        .negative { color: #ef4444; }

        .card { background-color: #0f172a; padding: 14px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #334155; }
        .card-title { font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: bold; margin-bottom: 5px; }
        .card-value { font-size: 14px; font-weight: bold; color: #fbbf24; }
        
        .btn-group { display: flex; gap: 10px; margin-top: 15px; }
        .btn { flex: 1; padding: 12px; border: none; border-radius: 8px; font-weight: bold; font-size: 14px; cursor: pointer; text-align: center; text-decoration: none; display: block; }
        .btn-buy { background-color: #22c55e; color: white; }
        .btn-sell { background-color: #ef4444; color: white; }
        .footer-info { margin-top: 15px; font-size: 11px; text-align: center; color: #64748b; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 FINBOT MARKET MONITOR</h1>
        <div class="subtitle">Live XAUUSD, Bitcoin & Ethereum Tracker</div>
        
        <div class="market-grid">
            <div class="market-card">
                <div>
                    <div class="asset-name">🥇 Gold (XAUUSD)</div>
                    <div class="asset-sub">Spot Market</div>
                </div>
                <div>
                    <div class="asset-price">{{ data.XAU.price }}</div>
                    <div class="asset-change positive">{{ data.XAU.change }}</div>
                </div>
            </div>

            <div class="market-card">
                <div>
                    <div class="asset-name">🪙 Bitcoin (BTC)</div>
                    <div class="asset-sub">Crypto / USD</div>
                </div>
                <div>
                    <div class="asset-price">{{ data.BTC.price }}</div>
                    <div class="asset-change positive">{{ data.BTC.change }}</div>
                </div>
            </div>

            <div class="market-card">
                <div>
                    <div class="asset-name">Ξ Ethereum (ETH)</div>
                    <div class="asset-sub">Crypto / USD</div>
                </div>
                <div>
                    <div class="asset-price">{{ data.ETH.price }}</div>
                    <div class="asset-change positive">{{ data.ETH.change }}</div>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-title">Jurnal / Aksi Terakhir Dicatat</div>
            <div class="card-value">{{ data.last_signal }}</div>
        </div>

        <form method="POST" action="/log-action">
            <div class="btn-group">
                <button type="submit" name="action" value="BUY" class="btn btn-buy">🟢 CATAT BUY</button>
                <button type="submit" name="action" value="SELL" class="btn btn-sell">🔴 CATAT SELL</button>
            </div>
        </form>

        <div class="footer-info">
            Terakhir diperbarui: {{ data.updated_at }} (Auto-refresh tiap 30s)
        </div>
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, data=market_data)

@app.route("/log-action", methods=["POST"])
def log_action():
    action = request.form.get("action")
    market_data["last_signal"] = f"Berhasil mencatat sinyal: {action} pada {time.strftime('%H:%M:%S')}"
    return redirect(url_for('index'))

def telegram_polling():
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
                                "text": "🤖 **FINBOT MONITOR AKTIF**\n\nPantau harga Gold & Crypto langsung lewat web:\n🔗 https://finbot-whro.onrender.com",
                                "parse_mode": "Markdown"
                            })
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    t_market = threading.Thread(target=fetch_market_prices, daemon=True)
    t_market.start()
    
    t_bot = threading.Thread(target=telegram_polling, daemon=True)
    t_bot.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
