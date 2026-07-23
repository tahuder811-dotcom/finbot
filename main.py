import os
import threading
import time
import requests
import pandas as pd
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

# Mengambil token dari Environment Variable Render secara aman
TOKEN = os.environ.get("TELEGRAM_TOKEN", "8914087726:AAGeuhs_0btpV97QnmgIDDGhEwHkzGtbvkM")
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}/"

active_market = "XAUUSD"

# Struktur data sekarang mencakup komponen Open, High, Low, Close (OHLC) untuk Candlestick
market_states = {
    "XAUUSD": {
        "name": "XAUUSD (Gold Spot)", 
        "price": "4050.20", 
        "candlestick_data": [
            {"x": "12:00", "o": 4044.0, "h": 4046.0, "l": 4043.5, "c": 4045.0},
            {"x": "12:30", "o": 4045.0, "h": 4047.5, "l": 4044.8, "c": 4046.5},
            {"x": "13:00", "o": 4046.5, "h": 4049.0, "l": 4046.0, "c": 4048.0},
            {"x": "13:30", "o": 4048.0, "h": 4048.5, "l": 4046.5, "c": 4047.0},
            {"x": "14:00", "o": 4047.0, "h": 4050.0, "l": 4046.8, "c": 4049.0},
            {"x": "14:30", "o": 4049.0, "h": 4051.0, "l": 4048.5, "c": 4050.2}
        ], 
        "rsi": "50.00", "sma": "4050.00", "signal": "WAIT & SEE"
    },
    "BTCUSD": {
        "name": "BTCUSD (Bitcoin)", 
        "price": "67500.00", 
        "candlestick_data": [
            {"x": "12:00", "o": 66800, "h": 67100, "l": 66750, "c": 67000},
            {"x": "12:30", "o": 67000, "h": 67300, "l": 66900, "c": 67200},
            {"x": "13:00", "o": 67200, "h": 67250, "l": 67000, "c": 67100},
            {"x": "13:30", "o": 67100, "h": 67400, "l": 67050, "c": 67300},
            {"x": "14:00", "o": 67300, "h": 67500, "l": 67200, "c": 67400},
            {"x": "14:30", "o": 67400, "h": 67600, "l": 67350, "c": 67500}
        ], 
        "rsi": "50.00", "sma": "67200.00", "signal": "WAIT & SEE"
    },
    "EURUSD": {
        "name": "EURUSD (Forex)", 
        "price": "1.0850", 
        "candlestick_data": [
            {"x": "12:00", "o": 1.0810, "h": 1.0825, "l": 1.0805, "c": 1.0820},
            {"x": "12:30", "o": 1.0820, "h": 1.0835, "l": 1.0815, "c": 1.0830},
            {"x": "13:00", "o": 1.0830, "h": 1.0832, "l": 1.0820, "c": 1.0825},
            {"x": "13:30", "o": 1.0825, "h": 1.0842, "l": 1.0822, "c": 1.0840},
            {"x": "14:00", "o": 1.0840, "h": 1.0850, "l": 1.0835, "c": 1.0845},
            {"x": "14:30", "o": 1.0845, "h": 1.0855, "l": 1.0840, "c": 1.0850}
        ], 
        "rsi": "50.00", "sma": "1.0835", "signal": "WAIT & SEE"
    }
}

last_action_log = "Belum ada aksi"
last_updated = "-"

def send_telegram_notification(message):
    try:
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

def update_market_analysis():
    global last_updated
    while True:
        try:
            # 1. Update XAUUSD (Coinbase PAXG)
            res_gold = requests.get("https://api.coinbase.com/v2/prices/PAXG-USD/spot", timeout=5)
            if res_gold.status_code == 200:
                p_gold = float(res_gold.json()["data"]["amount"])
                m = market_states["XAUUSD"]
                last_c = m["candlestick_data"][-1]["c"]
                
                # Buat candle baru berdasarkan harga real-time
                new_candle = {
                    "x": time.strftime("%H:%M"),
                    "o": last_c,
                    "h": max(last_c, p_gold) + 0.5,
                    "l": min(last_c, p_gold) - 0.5,
                    "c": p_gold
                }
                m["candlestick_data"].append(new_candle)
                if len(m["candlestick_data"]) > 20: m["candlestick_data"].pop(0)
                
                closes = [item["c"] for item in m["candlestick_data"]]
                df = pd.DataFrame(closes, columns=["close"])
                m["sma"] = f"{df['close'].rolling(window=5).mean().iloc[-1]:.2f}"
                delta = df["close"].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=5).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=5).mean()
                m["rsi"] = f"{100 - (100 / (1 + (gain/loss))):.2f}"
                m["price"] = f"{p_gold:.2f}"
                m["signal"] = "BULLISH (UPTREND)" if p_gold > float(m["sma"]) else "BEARISH (DOWNTREND)"

            # 2. Update BTCUSD (Coinbase BTC)
            res_btc = requests.get("https://api.coinbase.com/v2/prices/BTC-USD/spot", timeout=5)
            if res_btc.status_code == 200:
                p_btc = float(res_btc.json()["data"]["amount"])
                m = market_states["BTCUSD"]
                last_c = m["candlestick_data"][-1]["c"]
                
                new_candle = {
                    "x": time.strftime("%H:%M"),
                    "o": last_c,
                    "h": max(last_c, p_btc) + 10,
                    "l": min(last_c, p_btc) - 10,
                    "c": p_btc
                }
                m["candlestick_data"].append(new_candle)
                if len(m["candlestick_data"]) > 20: m["candlestick_data"].pop(0)
                
                closes = [item["c"] for item in m["candlestick_data"]]
                df = pd.DataFrame(closes, columns=["close"])
                m["sma"] = f"{df['close'].rolling(window=5).mean().iloc[-1]:.2f}"
                delta = df["close"].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=5).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=5).mean()
                m["rsi"] = f"{100 - (100 / (1 + (gain/loss))):.2f}"
                m["price"] = f"{p_btc:.2f}"
                m["signal"] = "BULLISH (UPTREND)" if p_btc > float(m["sma"]) else "BEARISH (DOWNTREND)"

            # 3. Update EURUSD (Forex Simulasi)
            m_eur = market_states["EURUSD"]
            last_c = m_eur["candlestick_data"][-1]["c"]
            p_eur = last_c + (0.0005 if time.time() % 2 == 0 else -0.0004)
            
            new_candle = {
                "x": time.strftime("%H:%M"),
                "o": last_c,
                "h": max(last_c, p_eur) + 0.0008,
                "l": min(last_c, p_eur) - 0.0008,
                "c": p_eur
            }
            m_eur["candlestick_data"].append(new_candle)
            if len(m_eur["candlestick_data"]) > 20: m_eur["candlestick_data"].pop(0)
            
            closes = [item["c"] for item in m_eur["candlestick_data"]]
            df = pd.DataFrame(closes, columns=["close"])
            m_eur["sma"] = f"{df['close'].rolling(window=5).mean().iloc[-1]:.4f}"
            delta = df["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=5).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=5).mean()
            m_eur["rsi"] = f"{100 - (100 / (1 + (gain/loss))):.2f}"
            m_eur["price"] = f"{p_eur:.4f}"
            m_eur["signal"] = "BULLISH (UPTREND)" if p_eur > float(m_eur["sma"]) else "BEARISH (DOWNTREND)"

            last_updated = time.strftime("%H:%M:%S - %d %b %Y")
        except Exception as e:
            print(f"Error background worker: {e}")
        
        time.sleep(30)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Finbot Pro - Candlestick Terminal</title>
    <!-- Memuat Chart.js dan plugin finansial khusus candlestick -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/luxon@3.4.3/build/global/luxon.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-luxon@1.3.1/dist/chartjs-adapter-luxon.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-chart-financial@0.1.1/dist/chartjs-chart-financial.min.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', system-ui, sans-serif; }
        body { background-color: #060913; color: #f1f5f9; padding: 10px; display: flex; justify-content: center; min-height: 100vh; }
        .container { width: 100%; max-width: 480px; }
        .header { background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.9)); backdrop-filter: blur(10px); padding: 14px; border-radius: 16px; border: 1px solid rgba(56, 189, 248, 0.2); margin-bottom: 10px; text-align: center; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4); }
        h1 { font-size: 15px; font-weight: 800; color: #38bdf8; margin-bottom: 6px; }
        
        .selector-form { display: flex; gap: 6px; justify-content: center; margin-bottom: 10px; }
        .asset-select { background: #1e293b; color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); padding: 8px 12px; border-radius: 10px; font-weight: bold; font-size: 12px; outline: none; cursor: pointer; flex: 1; }
        
        .card { background: linear-gradient(180deg, #111827 0%, #0d1322 100%); padding: 14px; border-radius: 14px; margin-bottom: 10px; border: 1px solid rgba(255, 255, 255, 0.05); box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
        .card-title { font-size: 10px; color: #94a3b8; text-transform: uppercase; font-weight: 700; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
        
        .live-badge { display: flex; align-items: center; gap: 5px; color: #22c55e; font-size: 10px; font-weight: 600; }
        .pulse-dot { width: 7px; height: 7px; background-color: #22c55e; border-radius: 50%; box-shadow: 0 0 8px #22c55e; animation: pulse 1.5s infinite; }
        @keyframes pulse { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(1.3); } 100% { opacity: 1; transform: scale(1); } }

        .price-display { font-size: 26px; font-weight: 800; color: #38bdf8; font-family: monospace; }
        .indicator-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 10px; }
        .indicator-box { background: rgba(15, 23, 42, 0.6); padding: 8px 10px; border-radius: 10px; border: 1px solid rgba(56, 189, 248, 0.1); text-align: center; }
        .ind-label { font-size: 9px; color: #64748b; font-weight: 600; text-transform: uppercase; }
        .ind-val { font-size: 13px; font-weight: 700; color: #fbbf24; font-family: monospace; margin-top: 2px; }

        .signal-box { font-size: 11px; font-weight: 800; color: #38bdf8; background: linear-gradient(90deg, rgba(56,189,248,0.1), rgba(15,23,42,0.8)); padding: 10px; border-radius: 10px; border-left: 3px solid #38bdf8; margin-top: 10px; text-align: center; }
        .chart-container { background: #0b101b; padding: 10px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.04); margin-bottom: 10px; }
        
        .btn-group { display: flex; gap: 10px; margin-top: 10px; }
        .btn { flex: 1; padding: 12px; border: none; border-radius: 12px; font-weight: 800; font-size: 13px; cursor: pointer; text-align: center; text-decoration: none; }
        .btn-buy { background: linear-gradient(135deg, #22c55e, #15803d); color: white; box-shadow: 0 4px 15px rgba(34, 197, 94, 0.3); }
        .btn-sell { background: linear-gradient(135deg, #ef4444, #b91c1c); color: white; box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3); }
        .footer-info { margin-top: 10px; font-size: 9px; text-align: center; color: #475569; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ CANDLESTICK TERMINAL PRO</h1>
        </div>

        <form method="GET" action="/" class="selector-form">
            <select name="asset" class="asset-select" onchange="this.form.submit()">
                <option value="XAUUSD" {% if current_asset == 'XAUUSD' %}selected{% endif %}>🟡 XAUUSD (Gold Spot)</option>
                <option value="BTCUSD" {% if current_asset == 'BTCUSD' %}selected{% endif %}>🟠 BTCUSD (Crypto)</option>
                <option value="EURUSD" {% if current_asset == 'EURUSD' %}selected{% endif %}>🔵 EURUSD (Forex)</option>
            </select>
        </form>

        <div class="card">
            <div class="card-title">
                <span>{{ current_data.name }}</span> 
                <div class="live-badge"><div class="pulse-dot"></div> LIVE</div>
            </div>
            <div class="price-display">{{ current_data.price }}</div>
            <div class="indicator-grid">
                <div class="indicator-box">
                    <div class="ind-label">RSI (5 Period)</div>
                    <div class="ind-val">{{ current_data.rsi }}</div>
                </div>
                <div class="indicator-box">
                    <div class="ind-label">SMA (Trend)</div>
                    <div class="ind-val">{{ current_data.sma }}</div>
                </div>
            </div>
            <div class="signal-box">SIGNAL: {{ current_data.signal }}</div>
        </div>

        <div class="chart-container">
            <canvas id="candlestickChart" width="400" height="200"></canvas>
        </div>

        <div class="card">
            <div class="card-title">Telegram Journal Log</div>
            <div style="font-size: 11px; color: #cbd5e1; background: rgba(15, 23, 42, 0.8); padding: 10px; border-radius: 8px; border: 1px solid rgba(56, 189, 248, 0.1); font-family: monospace;">
                {{ last_action_log }}
            </div>
        </div>

        <form method="POST" action="/execute">
            <input type="hidden" name="asset" value="{{ current_asset }}">
            <div class="btn-group">
                <button type="submit" name="action" value="BUY" class="btn btn-buy">🟢 BUY {{ current_asset }}</button>
                <button type="submit" name="action" value="SELL" class="btn btn-sell">🔴 SELL {{ current_asset }}</button>
            </div>
        </form>

        <div class="footer-info">
            Sync Time: {{ last_updated }} | Candlestick Engine Active
        </div>
    </div>

    <script>
        const ctx = document.getElementById('candlestickChart').getContext('2d');
        const rawData = {{ current_data.candlestick_data | tojson }};

        // Memetakan data agar cocok dibaca oleh plugin Chart.js Financial Candlestick
        const chartData = rawData.map(item => ({
            x: item.x,
            o: item.o,
            h: item.h,
            l: item.l,
            c: item.c
        }));

        const candlestickChart = new Chart(ctx, {
            type: 'candlestick',
            data: {
                datasets: [{
                    label: 'Price Action',
                    data: chartData,
                    color: {
                        up: '#22c55e',   // Hijau jika Close > Open
                        down: '#ef4444', // Merah jika Close < Open
                        unchanged: '#94a3b8'
                    }
                }]
            },
            options: {
                responsive: true,
                plugins: { 
                    legend: { display: false } 
                },
                scales: {
                    x: { 
                        type: 'category',
                        ticks: { color: '#64748b', font: { size: 9, family: 'monospace' } }, 
                        grid: { color: 'rgba(255, 255, 255, 0.03)' } 
                    },
                    y: { 
                        position: 'right',
                        ticks: { color: '#64748b', font: { size: 9, family: 'monospace' } }, 
                        grid: { color: 'rgba(255, 255, 255, 0.03)' } 
                    }
                }
            }
        });
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    global active_market
    selected_asset = request.args.get("asset", "XAUUSD")
    if selected_asset in market_states:
        active_market = selected_asset
    
    return render_template_string(
        HTML_TEMPLATE, 
        current_asset=active_market, 
        current_data=market_states[active_market],
        last_action_log=last_action_log,
        last_updated=last_updated
    )

@app.route("/execute", methods=["POST"])
def execute():
    global last_action_log
    asset = request.form.get("asset", "XAUUSD")
    action = request.form.get("action")
    timestamp = time.strftime('%H:%M:%S - %d %b %Y')
    
    current_price = market_states[asset]["price"]
    current_rsi = market_states[asset]["rsi"]
    current_sma = market_states[asset]["sma"]
    current_signal = market_states[asset]["signal"]

    last_action_log = f"Logged: {action} {asset} at {current_price} ({timestamp})"
    
    msg = f"📈 *FINBOT CANDLESTICK ALERT*\n\nAsset: *{asset}*\nAction: *{action}*\nPrice: `{current_price}`\nRSI: `{current_rsi}`\nSMA: `{current_sma}`\nStatus: `{current_signal}`\nTime: `{timestamp}`"
    send_telegram_notification(msg)
    
    return redirect(url_for('index', asset=asset))

if __name__ == "__main__":
    t_market = threading.Thread(target=update_market_analysis, daemon=True)
    t_market.start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
