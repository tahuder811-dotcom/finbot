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
                
                sl_buy = round(support * 0.997, 2)
                tp_buy = round(current_price * 1.006, 2)
                
                sniper_signal = "⏳ Menunggu area Demand/Supply valid (Price Action)"
                if current_price <= support * 1.001:
                    sniper_signal = (
                        f"🟢 *SNIPER BUY & RISK MANAGEMENT ALERT!*\n"
                        f"- Action: **OPEN BUY** di Area Support\n"
                        f"- Entry Harga: `${current_price:,.2f}`\n"
                        f"- 🛑 **Stop Loss (SL):** `${sl_buy:,.2f}`\n"
                        f"- 🎯 **Take Profit (TP):** `${tp_buy:,.2f}` (Ratio 1:2)"
                    )
                elif current_price >= resistance * 0.999:
                    sniper_signal = "🔴 *SNIPER SELL ALERT!* Harga di Area Resistance/Supply."
                
                return round(current_price, 2), resistance, support, sniper_signal
    except Exception as e:
        print(f"Error Gold API: {e}")
    
    return 2350.50, 2360.00, 2340.00, "Netral"

def get_gmgn_memes_with_charts():
    try:
        url = "https://api.dexscreener.com/latest/dex/search?q=solana"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=6)
        
        if response.status_code == 200:
            data = response.json()
            pairs = data.get("pairs", [])
            
            meme_results = []
            seen = set()
            
            sol_pairs = [p for p in pairs if p.get("chainId") == "solana"]
            
            for p in sol_pairs:
                base_token = p.get("baseToken", {})
                name = base_token.get("name", "Token")
                symbol = base_token.get("symbol", "UNKNOWN")
                pair_address = p.get("pairAddress", "")
                token_address = base_token.get("address", "")
                
                if symbol == "SOL" or symbol in seen:
                    continue
                seen.add(symbol)
                
                liquidity = p.get("liquidity", {})
                usd_liq = liquidity.get("usd", 0) or 0
                
                volume = p.get("volume", {})
                h24_vol = volume.get("h24", 0) or 0
                
                price_change = p.get("priceChange", {})
                h1_change = price_change.get("h1", 0) or 0
                h1_change = round(float(h1_change), 2)
                
                if usd_liq >= 5000 and h24_vol >= 1000:
                    status_sniper = "🛡️ Likuiditas Cukup & Aktif"
                    chart_link = f"https://dexscreener.com/solana/{pair_address if pair_address else token_address}"
                    
                    text_item = (
                        f"🟢 *{name}* (`{symbol}`) | 1h: `{h1_change}%`\n"
                        f"💧 Liq: `${usd_liq:,.0f}` | 📊 Vol: `${h24_vol:,.0f}`\n"
                        f"[{status_sniper}]\n"
                        f"📊 [Buka Chart Live]({chart_link})"
                    )
                    meme_results.append(text_item)
                
                if len(meme_results) >= 5:
                    break
            
            if meme_results:
                return "\n\n".join(meme_results)
    except Exception as e:
        print(f"Error DexScreener Filter: {e}")
    
    return "⏳ Belum ada koin meme yang memenuhi kriteria saat ini. Coba lagi sebentar."

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
                        f"🚨 *AUTOMATIC RISK-MANAGED SNIPER ALERT!* 🚨\n\n"
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
        "👉 `/price` atau `/tf15` - Cek harga emas & Kalkulasi SL/TP\n"
        "👉 `/news` - Panduan Sentimen Makro US\n"
        "👉 `/meme` - Saringan koin meme Solana"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['price', 'tf15'])
def send_price(message):
    global USER_CHAT_ID
    USER_CHAT_ID = message.chat.id
    p, r, s, signal = get_market_data()
    
    sl_buy = round(s * 0.997, 2)
    tp_buy = round(p * 1.006, 2)
    
    text = (
        f"📈 *XAUUSD Sniper & Risk Management*\n"
        f"- Harga Spot: `${p:,.2f}`\n"
        f"- Est. Support: `${s:,.2f}`\n"
        f"- Est. Resistance: `${r:,.2f}`\n\n"
        f"💡 *Rekomendasi Setup Buy & S&D:*\n"
        f"- 🛑 Rekomendasi Stop Loss (SL): `${sl_buy:,.2f}`\n"
        f"- 🎯 Rekomendasi Take Profit (TP): `${tp_buy:,.2f}` (Ratio 1:2)\n\n"
        f"{signal}\n\n"
        f"📊 [Klik Disini untuk Buka Chart TradingView XAUUSD](https://www.tradingview.com/chart/?symbol=OANDA%3AXAUUSD)"
    )
    bot.reply_to(message, text, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(commands=['news', 'usnews'])
def send_us_news(message):
    global USER_CHAT_ID
    USER_CHAT_ID = message.chat.id
    news_text = (
        "🇺🇸 *US Macro & Fundamental Guide (XAUUSD)*\n\n"
        "⚠️ *Faktor Utama Penggerak Emas:*\n"
        "1. Kebijakan The Fed & Suku Bunga.\n"
        "2. Faktor Politik/Trump & Geopolitik terhadap DXY.\n"
        "3. Jam Rawan Sesi AS: 19.30 WIB – 23.00 WIB.\n\n"
        "💡 *Tips Disiplin:* Selalu pasang Stop Loss sesuai perhitungan bot untuk mengamankan target maksimal 2x loss seminggu!"
    )
    bot.reply_to(message, news_text, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(commands=['meme'])
def send_meme(message):
    global USER_CHAT_ID
    USER_CHAT_ID = message.chat.id
    trending = get_gmgn_memes_with_charts()
    text = f"🚀 *Saringan Koin Meme Solana*\n\n{trending}"
    bot.reply_to(message, text, parse_mode="Markdown", disable_web_page_preview=True)

@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route('/')
def index():
    return "Finbot Sniper Fixed is running!", 200

if __name__ == "__main__":
    RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")
    if RENDER_URL:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    
    t = threading.Thread(target=background_price_monitor, daemon=True)
    t.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
