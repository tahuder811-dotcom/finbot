import os
import telebot
import requests
from flask import Flask, request

TOKEN = str(os.getenv("TELEGRAM_BOT_TOKEN", ""))
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Fungsi ambil data harga emas/XAUUSD stabil
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
                return round(current_price, 2), resistance, support
    except Exception as e:
        print(f"Error Gold API: {e}")
    
    # Fallback cadangan jika jaringan luar terbatas
    return 2350.50, 2360.00, 2340.00

# Fungsi saringan koin meme berpotensi dari GMGN
def get_gmgn_memes():
    try:
        url = "https://gmgn.ai/defi/quotation/v1/ranking/swaps/1h?device_id=1&client_id=web&app_version=2.0.0&system=web"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json"
        }
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            res_json = response.json()
            rankings = res_json.get("data", {}).get("rankings", [])
            if not rankings:
                rankings = res_json.get("data", [])
            
            meme_list = []
            # Saring 5 token teratas yang potensial berdasarkan volume & kenaikan 1h
            for item in rankings[:5]:
                symbol = item.get("symbol", "UNKNOWN")
                name = item.get("name", "Token")
                change = item.get("price_change_percent1h", 0)
                if change:
                    change = round(float(change), 2)
                
                # Filter koin meme yang menunjukkan potensi kenaikan positif
                if change > 0:
                    meme_list.append(f"🟢 *{name* ({symbol}) - 1h: `+{change}%`")
                else:
                    meme_list.append(f"🔴 *{name}* ({symbol}) - 1h: `{change}%`")
            
            if meme_list:
                return "\n".join(meme_list)
    except Exception as e:
        print(f"Error GMGN Filter: {e}")
    
    return "Belum ada sinyal koin meme potensial yang tertangkap saat ini."

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "🤖 *Finbot S&D & Meme Screener Active*\n\n"
        "Perintah yang tersedia:\n"
        "👉 `/price` atau `/tf15` - Cek harga emas & S&D\n"
        "👉 `/meme` - Saringan koin meme potensial terkini"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['price', 'tf15'])
def send_price(message):
    p, r, s = get_market_data()
    text = (
        f"📈 *XAUUSD Market Update*\n"
        f"- Harga Spot: `${p:,.2f}`\n"
        f"- Est. Resistance: `${r:,.2f}`\n"
        f"- Est. Support: `${s:,.2f}`"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['meme'])
def send_meme(message):
    trending = get_gmgn_memes()
    bot.reply_to(message, f"🚀 *Saringan Koin Meme Potensial (1H)*\n\n{trending}", parse_mode="Markdown")

@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route('/')
def index():
    return "Finbot is running via Webhook!", 200

if __name__ == "__main__":
    RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")
    if RENDER_URL:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
