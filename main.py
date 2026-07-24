import os
import telebot
import requests
from flask import Flask, request

TOKEN = str(os.getenv("TELEGRAM_BOT_TOKEN", ""))
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

def get_market_data():
    try:
        url = "https://api.gold-api.com/price/XAU"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            current_price = float(data.get("price", 0))
            if current_price > 0:
                resistance = round(current_price * 1.003, 2)
                support = round(current_price * 0.997, 2)
                
                sniper_signal = "⏳ Menunggu area Demand/Supply valid (Price Action)"
                if current_price <= support * 1.001:
                    sniper_signal = "🟢 *SNIPER BUY ALERT!* Harga di Area Support/Demand Kuat."
                elif current_price >= resistance * 0.999:
                    sniper_signal = "🔴 *SNIPER SELL ALERT!* Harga di Area Resistance/Supply."
                
                return round(current_price, 2), resistance, support, sniper_signal
    except Exception as e:
        print(f"Error Gold API: {e}")
    
    return 2350.50, 2360.00, 2340.00, "Netral"

def get_gmgn_memes():
    try:
        # Menggunakan endpoint pencarian umum DexScreener yang mencakup pasangan likuiditas aktif
        url = "https://api.dexscreener.com/latest/dex/search?q=solana"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=6)
        
        if response.status_code == 200:
            data = response.json()
            pairs = data.get("pairs", [])
            
            raw_list = []
            seen = set()
            
            for item in pairs:
                chainId = item.get("chainId")
                base_token = item.get("baseToken", {})
                symbol = base_token.get("symbol", "").upper()
                name = base_token.get("name", "Token")
                
                # Filter jaringan Solana, bukan token induk SOL, dan belum duplikat
                if chainId == "solana" and symbol and symbol != "SOL" and symbol not in seen:
                    h1_change = item.get("priceChange", {}).get("h1", 0)
                    if h1_change is None:
                        h1_change = 0
                    h1_change = round(float(h1_change), 2)
                    
                    # FOKUS PEMANTAUAN: Hanya ambil koin yang sedang hijau (kenaikan > 0%)
                    if h1_change > 0:
                        seen.add(symbol)
                        raw_list.append((name, symbol, h1_change))
            
            # Urutkan dari persentase kenaikan 1 jam tertinggi ke terendah
            raw_list = sorted(raw_list, key=lambda x: x[2], reverse=True)
            
            meme_list = []
            for name, symbol, h1_change in raw_list[:5]:
                # Label status dinamis berdasarkan tingkat kenaikannya
                if h1_change >= 20.0:
                    status_sniper = "🔥 Strong Pump"
                elif h1_change >= 5.0:
                    status_sniper = "🎯 Potensi Bagus"
                else:
                    status_sniper = "👀 Baru Naik"
                    
                meme_list.append(f"🟢 *{name}* (`{symbol}`) - 1h: `+{h1_change}%` [{status_sniper}]")
            
            if meme_list:
                return "\n".join(meme_list)
    except Exception as e:
        print(f"Error DexScreener Pairs: {e}")
    
    return "⏳ Belum ada koin meme Solana yang melompat naik saat ini. Silakan coba cek beberapa saat lagi."

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "🤖 *Finbot Sniper Engine Active*\n\n"
        "Perintah yang tersedia:\n"
        "👉 `/price` atau `/tf15` - Cek harga emas & Sinyal Sniper S&D\n"
        "👉 `/meme` - Saringan koin meme potensial terpilih"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['price', 'tf15'])
def send_price(message):
    p, r, s, signal = get_market_data()
    text = (
        f"📈 *XAUUSD Sniper Update*\n"
        f"- Harga Spot: `${p:,.2f}`\n"
        f"- Est. Resistance: `${r:,.2f}`\n"
        f"- Est. Support: `${s:,.2f}`\n\n"
        f"{signal}"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['meme'])
def send_meme(message):
    trending = get_gmgn_memes()
    bot.reply_to(message, f"🚀 *Saringan Koin Meme Berpotensi (Solana)*\n\n{trending}", parse_mode="Markdown")

@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route('/')
def index():
    return "Finbot Sniper is running via Webhook!", 200

if __name__ == "__main__":
    RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")
    if RENDER_URL:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
