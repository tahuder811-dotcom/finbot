from datetime import datetime
from flask import Flask, jsonify, render_template_string, request

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
    <title>Finbot Pro Trading</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
        .chart-box { background: #0b101b; padding: 8px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.04); margin-bottom: 12px; height: 210px; }
        
        .btn-group { display: flex; gap: 8px; }
        .btn { flex: 1; padding: 12px; border: none; border-radius: 10px; font-weight: 800; font-size: 11px; cursor: pointer; text-align: center; transition: 0.2s; }
        .btn-buy { background: linear-gradient(135deg, #22c55e, #15803d); color: white; box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3); }
        .btn-sell { background: linear-gradient(135deg, #ef4444, #b91c1c); color: white; box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3); }
        .log-box { font-size: 10px; background: #1e293b; padding: 8px; border-radius: 8px; color: #cbd5e1; font-family: monospace; margin-bottom: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ FINBOT LIVE TERMINAL</h1>
            <div class="sub-header">Direct Browser API Engine</div>
        </div>

        <div class="card">
            <div class="card-title">
                <span>XAUUSD / Gold Spot Market</span> 
                <div class="live-badge"><div class="pulse-dot"></div> LIVE CONNECTED</div>
            </div>
            <div class="price-display" id="priceVal">Connecting...</div>
            
            <div class="info-grid">
                <div class="info-box">
                    <div class="info-label">Status Koneksi</div>
                    <div class="info-val" style="color: #22c55e;">Aktiv</div>
                </div>
                <div class="info-box">
                    <div class="info-label">Update Interval</div>
                    <div class="info-val">2 Detik</div>
                </div>
            </div>
            <div class="signal-box" id="signalVal">MEMUAT TREN PASAR...</div>
        </div>

        <div class="chart-box">
            <canvas id="liveChart"></canvas>
        </div>

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
        const ctx = document.getElementById('liveChart').getContext('2d');
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'XAUUSD',
                    data: [],
                    borderColor: '#38bdf8',
                    backgroundColor: 'rgba(56, 189, 248, 0.05)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: '#64748b', font: { size: 9 } }, grid: { color: 'rgba(255,255,255,0.03)' } },
                    y: { ticks: { color: '#64748b', font: { size: 9 } }, grid: { color: 'rgba(255,255,255,0.03)' } }
                }
            }
        });

        async function fetchLivePrice() {
            try {
                // Mengambil data langsung dari browser ke Binance API Publik (Tanpa perantara server Render yang sering delay)
                let res = await fetch('https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT');
                let data = await res.json();
                let price = parseFloat(data.price);
                
                let timeStr = new Date().toLocaleTimeString();
                
                document.getElementById('priceVal').innerText = price.toLocaleString(undefined, {minimumFractionDigits: 2});
                document.getElementById('signalVal').innerText = "PASAR AKTIF & BERGERAK NORMAL";

                if(chart.data.labels.length > 20) {
                    chart.data.labels.shift();
                    chart.data.datasets[0].data.shift();
                }
                chart.data.labels.push(timeStr);
                chart.data.datasets[0].data.push(price);
                chart.update('none');
            } catch(e) {
                document.getElementById('priceVal').innerText = "Koneksi Gagal";
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

        setInterval(fetchLivePrice, 2000);
        fetchLivePrice();
    </script>
</body>
</html>
    """)


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
