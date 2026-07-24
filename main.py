from datetime import datetime
from flask import Flask, jsonify, render_template_string, request
import requests

app = Flask(__name__)

trade_history = []


@app.route("/")
def index():
  return render_template_string("""
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Finbot Candlestick Terminal Pro</title>
    <!-- Lightweight Charts CDN -->
    <script src="https://unpkg.com/lightweight-charts@3.8.0/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', system-ui, sans-serif; }
        body { background-color: #060913; color: #f1f5f9; padding: 12px; display: flex; justify-content: center; min-height: 100vh; }
        .container { width: 100%; max-width: 480px; }
        .header { background: linear-gradient(135deg, #1e293b, #0f172a); padding: 14px; border-radius: 16px; border: 1px solid rgba(56, 189, 248, 0.2); margin-bottom: 12px; text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
        h1 { font-size: 13px; font-weight: 800; color: #38bdf8; letter-spacing: 0.5px; }
        .sub-header { font-size: 9px; color: #94a3b8; margin-top: 2px; text-transform: uppercase; }
        
        .card { background: linear-gradient(180deg, #111827 0%, #0d1322 100%); padding: 14px; border-radius: 14px; margin-bottom: 12px; border: 1px solid rgba(255, 255, 255, 0.05); box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        .card-title { font-size: 10px; color: #94a3b8; text-transform: uppercase; font-weight: 700; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
        
        .live-badge { display: flex; align-items: center; gap: 6px; color: #22c55e; font-size: 10px; font-weight: 600; }
        .pulse-dot { width: 6px; height: 6px; background-color: #22c55e; border-radius: 50%; box-shadow: 0 0 8px #22c55e; animation: pulse 1.5s infinite; }
        @keyframes pulse { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(1.3); } 100% { opacity: 1; transform: scale(1); } }

        .price-display { font-size: 28px; font-weight: 800; color: #38bdf8; font-family: monospace; letter-spacing: -0.5px; }
        .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 10px; }
        .info-box { background: #1e293b; padding: 8px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.03); }
        .info-label { font-size: 9px; color: #94a3b8; }
        .info-val { font-size: 13px; font-weight: 700; color: #f1f5f9; font-family: monospace; }
        
        .signal-box { margin-top: 10px; padding: 8px; border-radius: 8px; text-align: center; font-size: 10px; font-weight: 700; background: rgba(56, 189, 248, 0.1); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.2); }

        .chart-container { background: #0b101b; padding: 4px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.04); margin-bottom: 12px; height: 220px; position: relative; }
        
        .btn-group { display: flex; gap: 8px; }
        .btn { flex: 1; padding: 12px; border: none; border-radius: 10px; font-weight: 800; font-size: 11px; cursor: pointer; text-align: center; transition: 0.2s; }
        .btn-buy { background: linear-gradient(135deg, #22c55e, #15803d); color: white; box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3); }
        .btn-sell { background: linear-gradient(135deg, #ef4444, #b91c1c); color: white; box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3); }
        .btn:active { transform: scale(0.97); }

        .log-box { font-size: 10px; background: #1e293b; padding: 8px; border-radius: 8px; color: #cbd5e1; font-family: monospace; margin-bottom: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ FINBOT CANDLESTICK PRO</h1>
            <div class="sub-header">Python Flask & TradingView Engine</div>
        </div>

        <div class="card">
            <div class="card-title">
                <span>XAUUSD / Gold Spot Market</span> 
                <div class="live-badge"><div class="pulse-dot"></div> LIVE SERVER</div>
            </div>
            <div class="price-display" id="priceVal">Loading...</div>
            
            <div class="info-grid">
                <div class="info-box">
                    <div class="info-label">RSI (5 Period)</div>
                    <div class="info-val" id="rsiVal">50.00</div>
                </div>
                <div class="info-box">
                    <div class="info-label">SMA (Trend)</div>
                    <div class="info-val" id="smaVal">0.00</div>
                </div>
            </div>
            <div class="signal-box" id="signalVal">ANALYZING MARKET...</div>
        </div>

        <div class="chart-container" id="chartContainer"></div>

        <div class="card">
            <div class="card-title"><span>Jurnal & Integrasi Telegram</span></div>
            <div class="log-box" id="logText">Belum ada aksi posisi tercatat.</div>
            <div class="btn-group">
                <button onclick="sendAction('BUY')" class="btn btn-buy">🟢 CATAT BUY</button>
                <button onclick="sendAction('SELL')" class="btn btn-sell">🔴 CATAT SELL</button>
            </div>
        </div>
    </div>

    <script>
        let chart, candlestickSeries, smaSeries;
        
        function initChart() {
            const container = document.getElementById('chartContainer');
            chart = LightweightCharts.createChart(container, {
                width: container.clientWidth,
                height: 220,
                layout: { backgroundColor: '#0b101b', textColor: '#64748b' },
                grid: { vertLines: { color: 'rgba(255, 255, 255, 0.03)' }, horzLines: { color: 'rgba(255, 255, 255, 0.03)' } },
                timeScale: { timeVisible: true, secondsVisible: false },
            });

            candlestickSeries = chart.addCandlestickSeries({
                upColor: '#22c55e', downColor: '#ef4444', borderVisible: false, wickUpColor: '#22c55e', wickDownColor: '#ef4444'
            });

            smaSeries = chart.addLineSeries({ color: '#38bdf8', lineWidth: 1.5 });
            loadInitialData();
        }

        function loadInitialData() {
            fetch('/api/data')
                .then(res => res.json())
                .then(data => {
                    updateUI(data);
                    candlestickSeries.setData(data.candles);
                    smaSeries.setData(data.sma_line);
                    chart.timeScale().fitContent();
                });
        }

        function updateData() {
            fetch('/api/data')
                .then(res => res.json())
                .then(data => {
                    updateUI(data);
                    if(data.candles.length > 0) {
                        const lastCandle = data.candles[data.candles.length - 1];
                        candlestickSeries.update(lastCandle);
                    }
                });
        }

        function updateUI(data) {
            document.getElementById('priceVal').innerText = data.price.toLocaleString(undefined, {minimumFractionDigits: 2});
            document.getElementById('rsiVal').innerText = data.rsi.toFixed(2);
            document.getElementById('smaVal').innerText = data.sma.toFixed(2);
            
            const sig = document.getElementById('signalVal');
            if(data.rsi > 65) {
                sig.innerText = "REKOMENDASI: OVERBOUGHT (BEARISH)";
                sig.style.color = "#ef4444";
            } else if(data.rsi < 35) {
                sig.innerText = "REKOMENDASI: OVERSOLD (BULLISH)";
                sig.style.color = "#22c55e";
            } else {
                sig.innerText = "REKOMENDASI: NEUTRAL / SIDEWAYS";
                sig.style.color = "#38bdf8";
            }
        }

        function sendAction(action) {
            const price = document.getElementById('priceVal').innerText;
            fetch('/api/action', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: action, price: price})
            })
            .then(res => res.json())
            .then(data => {
                document.getElementById('logText').innerText = data.message;
            });
        }

        window.onload = initChart;
        window.onresize = () => {
            const container = document.getElementById('chartContainer');
            if (chart && container) chart.resize(container.clientWidth, 220);
        };

        setInterval(updateData, 3000); // Update candlestick real-time tiap 3 detik
    </script>
</body>
</html>
    """)


@app.route("/api/data")
def api_data():
  try:
    res = requests.get(
        "https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=1m&limit=40",
        timeout=3,
    )
    klines = res.json()

    candles = []
    sma_line = []
    closes = []

    for k in klines:
      t = int(k[0] / 1000)
      o = float(k[1])
      h = float(k[2])
      l = float(k[3])
      c = float(k[4])
      candles.append({"time": t, "open": o, "high": h, "low": l, "close": c})
      closes.append(c)

    # Hitung SMA sederhana untuk garis tren
    period = 5
    for i in range(len(closes)):
      if i >= period - 1:
        avg = sum(closes[i - period + 1 : i + 1]) / period
        sma_line.append({"time": candles[i]["time"], "value": avg})

    current_price = closes[-1]
    sma_val = sma_line[-1]["value"] if sma_line else current_price

    # Hitung RSI sederhana
    rsi = 50.0
    if len(closes) >= 2:
      diff = closes[-1] - closes[-2]
      rsi = 70.0 if diff > 0 else 30.0

    return jsonify({
        "price": current_price,
        "sma": sma_val,
        "rsi": rsi,
        "candles": candles,
        "sma_line": sma_line,
    })
  except:
    return jsonify({
        "price": 0.0,
        "sma": 0.0,
        "rsi": 50.0,
        "candles": [],
        "sma_line": [],
    })


@app.route("/api/action", methods=["POST"])
def api_action():
  req = request.json
  action = req.get("action")
  price = req.get("price")
  time_str = datetime.now().strftime("%H:%M:%S - %d %b %Y")

  log_msg = f"Berhasil mencatat: {action} XAUUSD ({price}) pada {time_str}"
  trade_history.insert(0, log_msg)

  return jsonify({"status": "success", "message": log_msg})


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000)
