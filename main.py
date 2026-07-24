import os
import time
import threading
import telebot
import requests
from flask import Flask, request

TOKEN = str(os.getenv("TELEGRAM_BOT_TOKEN", ""))
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

USER_CHAT_ID = None

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

def get_gmgn_memes_with_charts():
    try:
        url = "https://api.dexscreener.com/token-boosts/latest/v1"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=6)
        
        if response.status_code == 200:
            boosted_tokens = response.json()
            meme_results = []
            seen = set()
            
            sol_tokens = [t for t in boosted_tokens if t.get("chainId"] == "solana"]
            if not sol_tokens:
                sol_tokens = boosted_tokens
                
            for item in sol_tokens[:10]:
                token_address = item.get("tokenAddress", "")
                if token_address and token_address not in seen:
                    seen.add(token_address)
                    
                    detail_res = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{token_address}", headers=headers, timeout=3)
                    if detail_res.status_code == 200:
                        pair_data = detail_res.json().get("pairs", [])
                        if pair_data:
                            p = pair_data[0]
                            base_token = p.get("baseToken", {})
                            name = base_token.get("name", "Token")
                            symbol = base_token.get("symbol", "UNKNOWN")
                            pair_address = p.get("pairAddress", "")
                            
                            h1_change = p.get("priceChange", {}).get("h1", 0)
                            if h1_change is None:
                                h1_change = 0
                            h1_change = round(float(h1_change), 2)
                            
                            if h1_change > 0:
                                status_sniper = "🔥 Strong Pump" if h1_change > 10 else "🎯 Potensi Bagus"
                                
                                # Link langsung ke Chart DexScreener & Quick Swap
                                chart_link = f"https://dexscreener.com/solana/{pair_address if pair_address else token_address}"
                                
                                text_item = (
                                    f"🟢 *{name}* (`{symbol}`) - 1h: `+{h1_change}%` [{status_sniper}]\n"
                                    f"📊 [Buka Chart Live]({chart_link})"
                                )
                                meme_results.append(text_item)
                            
                            if len(meme_results) >= 5:
                                break
            
            if meme_results:
                return "\n\n".join(meme_results)
    except Exception as e:
        print(f"Error DexScreener Chart Fetch: {e}")
    
    return "⏳ Belum ada koin meme hijau yang melompat naik saat ini."

def background_price_monitor():
    global USER_CHAT_ID
    last_alert_status = None
    while True:
        try:
            if USER_CHAT_ID:
                p, r, s, signal = get_market_data()
                if "ALERT!" in signal and signal != last_alert_status:
                    last_alert_status = signal
                    alert_text = (
                        f"🚨 *AUTOMATIC SNIPER ALERT!* 🚨\n\n"
                        f"📈 *XAUUSD Market Update*\n"
                        f"- Harga Spot: `${p:,.2f}`\n"
                        f"- Est. Resistance: `${r:,.2f}`\n"
                        f"- Est. Support: `${s:,.2f}`\n\n"
                        f"{signal}\n\n"
                        f"📊 [Pantau Chart TradingView XAUUSD](https://www.tradingview.com/chart/?symbol=OANDA%3AXAUUSD)"
                    )
                    bot.send_message(USER_CHAT_ID, alert_text, parse_mode="Markdown", disable_web_page_preview=False)
                elif "Menunggu" in signal:
                    last_alert_status = "Menunggu"
        except Exception as e:
            print(f"Error Background Monitor: {e}")
        time.sleep(180)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    global USER_CHAT_ID
    USER_CHAT_ID = message.chat.id
    text = (
        "🤖 *Finbot Sniper Engine Active*\n\n"
        "Perintah yang tersedia:\n"
        "👉 `/price` atau `/tf15` - Cek harga emas & Link Chart XAUUSD\n"
        "👉 `/meme` - Saringan koin meme Solana lengkap dengan link Chart Live"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['price', 'tf15'])
def send_price(message):
    global USER_CHAT_ID
    USER_CHAT_ID = message.chat.id
    p, r, s, signal = get_market_data()
    text = (
        f"📈 *XAUUSD Sniper Update*\n"
        f"- Harga Spot: `${p:,.2f}`\n"
        f"- Est. Resistance: `${r:,.2f}`\n"
        f"- Est. Support: `${s:,.2f}`\n\n"
        f"{signal}\n\n"
        f"📊 [Klik Disini untuk Buka Chart TradingView XAUUSD](https://www.tradingview.com/chart/?symbol=OANDA%3AXAUUSD)"
    )
    bot.reply_to(message, text, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(commands=['meme'])
def send_meme(message):
    global USER_CHAT_ID
    USER_CHAT_ID = message.chat.id
    trending = get_gmgn_memes_with_charts()
    text = f"🚀 *Saringan Koin Meme Berpotensi & Chart (Solana)*\n\n{trending}"
    bot.reply_to(message, text, parse_mode="Markdown", disable_web_page_preview=True)

@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route('/')
def index():
    return "Finbot Sniper with Charts is running!", 200

if __name__ == "__main__":
    RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")
    if RENDER_URL:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    
    t = threading.Thread(target=background_price_monitor, daemon=True)
    t.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
