import os
import threading
import time
import requests
import pandas as pd
import pandas_ta as ta
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

TOKEN = "8914087726:AAGeuhs_0btpV97QnmgIDDGhEwHkzGtbvkM"
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}/"

# Menyimpan data pasar & hasil kalkulasi indikator teknikal
market_data = {
    "labels": [],
    "prices": [],
    "xau_price": "$2,350.20",
    "rsi": "50.00",
    "sma": "2,350.00",
    "signal": "WAIT & SEE",
    "last_action": "Belum ada aksi",
    "updated_at": "-"
}

def send_telegram_notification(message):
    """Mengirim pesan otomatis ke Telegram"""
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
    """Mengambil harga pasar real-time & menghitung indikator teknikal dengan pandas-ta"""
    # Inisialisasi data historis dummy agar indikator langsung bisa dihitung
    history_prices = [2340.0, 2341.5, 2343.0, 2342.0, 2345.0, 2348.0, 2347.5, 2350.2]
    history_times = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"]

    while True:
        try:
            # Ambil data harga emas real-time dari API publik
            gold_res = requests.get("https://data-asg.goldprice.org/dbXRates/USD", timeout=10)
            if gold_res.status_code == 200:
                g_data = gold_res.json()
                items = g_data.get("items", [])
                if items:
                    current_price = float(items[0].get("xauPrice", 2350.0))
                    
                    # Masukkan ke riwayat
                    history_prices.append(current_price)
                    history_times.append(time.strftime("%H:%M"))
                    
                    # Batasi jumlah riwayat maksimal 20 data terakhir
                    if len(history_prices) > 20:
                        history_prices.pop(0)
                        history_times.pop(0)

                    # Konversi ke Pandas DataFrame untuk perhitungan indikator profesional
                    df = pd.DataFrame(history_prices, columns=["close"])
                    
                    # Hitung indikator RSI (Relative Strength Index) periode 7/14
                    rsi_series = ta.rsi(df["close"], length=5)
                    current_rsi = rsi_series.iloc[-1] if rsi_series is not None and not rsi_series.empty else 50.0

                    # Hitung indikator Moving Average (SMA) periode 5
                    sma_series = ta.sma(df["close"], length=5)
                    current_sma = sma_series.iloc[-1] if sma_series is not None and not sma_series.empty else current_price

                    # Logika Sinyal Berdasarkan Indikator Teknikal Asli
                    if current_rsi < 30:
                        signal = "STRONG BUY (OVERSOLD)"
                    elif current_rsi > 70:
                        signal = "STRONG SELL (OVERBOUGHT)"
                    elif current_price > current_sma:
                        signal = "BULLISH (UPTREND)"
                    else:
                        signal = "BEARISH (DOWNTREND)"

                    # Perbarui state global
                    market_data["labels"] = history_times
                    market_data["prices"] = history_prices
                    market_data["xau_price"] = f"${current_price:,.2f}"
                    market_data["rsi"] = f"{current_rsi:.2f}"
                    market_data["sma"] = f"${current_sma:,.2f}"
                    market_data["signal"] = signal

            market_data["updated_at"] = time.strftime("%H:%M:%S - %d %b %Y")
        except Exception as e:
            print(f"Error pada background worker teknikal: {e}")
        
        time.sleep(30)

# Template HTML Dashboard Modern & Chart.js
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Finbot Pro - Technical Analyzer</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background-color: #0b0f19; color: #f8fafc; padding: 12px; display: flex; justify-content: center; min-height: 100vh; }
        .container { width: 100%; max-width: 480px; }
        .header { background: linear-gradient(135deg, #1e293b, #0f172a); padding: 18px; border-radius: 16px; border: 1px solid #334155; margin-bottom: 12px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        h1 { font-size: 18px; color: #38bdf8; margin-bottom: 4px; }
        .subtitle { font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 600; }
        
        .card { background-color: #1e293b; padding: 14px; border-radius: 14px; margin-bottom: 12px; border: 1px solid #334155; }
        .card-title { font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: bold; margin-bottom: 6px; display: flex; justify-content: space-between; }
        
        .price-display { font-size: 22px; font-weight: bold; color: #38bdf8; }
        .indicator-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 8px; }
        .indicator-box { background: #0f172a; padding: 10px; border-radius: 8px; border: 1px solid #334155; text-align: center; }
        .ind-label { font-size: 10px; color: #94a3b8; }
        .ind-val { font-size: 14px; font-weight: bold; color: #fbbf24; margin-top: 2px; }
        
        .signal-box { font-size: 13px; font-weight: bold; color: #22c55e; background: #0f172a; padding: 10px; border-radius: 8px; border: 1px solid #334155; margin-top: 8px; text-align: center; }
        
        .chart-container { background: #0f172a; padding: 10px; border-radius: 10px; border: 1px solid #334155; margin-bottom: 12px; }
        
        .btn-group { display: flex; gap: 10px; margin-top: 10px; }
        .btn { flex: 1; padding: 12px; border: none; border-radius: 10px; font-weight: bold; font-size: 14px; cursor: pointer; text-align: center; text-decoration: none; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        .btn-buy { background: linear-gradient(135deg, #22c55e, #16a34a); color: white; }
        .btn-sell { background: linear-gradient(135deg, #ef4444, #dc2626); color: white; }
        
        .footer-info { margin-top: 10px; font-size: 10px; text-align: center; color: #64748b; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 FINBOT TECHNICAL ANALYZER</h1>
            <div class="subtitle">Python Pandas-TA & Chart.js Engine</div>
        </div>

        <!-- Kartu Harga & Indikator Teknikal -->
        <div class="card">
            <div class="card-title"><span>XAUUSD Spot Market</span> 🟢 Live Server</div>
            <div class="price-display">{{ data.xau_price }}</div>
            
            <div class="indicator-grid">
                <div class="indicator-box">
                    <div class="ind-label">RSI (5 Period)</div>
                    <div class="ind-val">{{ data.rsi }}</div>
                </div>
                <div class="indicator-box">
                    <div class="ind-label">SMA (Trend)</div>
                    <div class="ind-val">{{ data.sma }}</div>
                </div>
            </div>

            <div class="signal-box">Rekomendasi Sinyal: {{ data.signal }}</div>
        </div>

        <!-- Grafik Interaktif Mandiri -->
        <div class="chart-container">
            <canvas id="techChart" width="400" height="200"></canvas>
        </div>

        <!-- Jurnal Aksi -->
        <div class="card">
            <div class="card-title">Jurnal & Integrasi Telegram</div>
            <div style="font-size: 12px; color: #e2e8f0; background: #0f172a; padding: 8px; border-radius: 6px; border: 1px solid #334155;">
                {{ data.last_action }}
            </div>
        </div>

        <!-- Tombol Eksekusi -->
        <form method="POST" action="/execute">
            <div class="btn-group">
                <button type="submit" name="action" value="BUY XAUUSD" class="btn btn-buy">🟢 CATAT BUY</button>
                <button type="submit" name="action" value="SELL XAUUSD" class="btn btn-sell">🔴 CATAT SELL</button>
            </div>
        </form>

        <div class="footer-info">
            Pembaruan Terakhir: {{ data.updated_at }} | Render Server Active
        </div>
    </div>

    <script>
        const ctx = document.getElementById('techChart').getContext('2d');
        const techChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: {{ data.labels | tojson }},
                datasets: [{
                    label: 'XAUUSD Price',
                    data: {{ data.prices | tojson }},
                    borderColor: '#38bdf8',
                    backgroundColor: 'rgba(56, 189, 248, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.2
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: '#94a3b8', font: { size: 9 } }, grid: { color: '#1e293b' } },
                    y: { ticks: { color: '#94a3b8', font: { size: 9 } }, grid: { color: '#1e293b' } }
                }
            }
        });
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, data=market_data)

@app.route("/execute", methods=["POST"])
def execute():
    action = request.form.get("action")
    timestamp = time.strftime('%H:%M:%S - %d %b %Y')
    
    market_data["last_action"] = f"Berhasil mencatat: {action} ({timestamp})"
    
    # Kirim laporan lengkap dengan indikator teknikal ke Telegram
    msg = f"📈 *SINYAL TEKNIKAL TERKINI*\n\nAksi: *{action}*\nHarga: `{market_data['xau_price']}`\nRSI: `{market_data['rsi']}`\nSMA: `{market_data['sma']}`\nSinyal: `{market_data['signal']}`\nWaktu: `{timestamp}`"
    send_telegram_notification(msg)
    
    return redirect(url_for('index'))

if __name__ == "__main__":
    t_market = threading.Thread(target=update_market_analysis, daemon=True)
    t_market.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
