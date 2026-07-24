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

# Variabel Global untuk melacak posisi aktif & target TP/SL
active_position = None  # "BUY" atau "SELL"
entry_price_tracked = 0.0
target_tp = 0.0
target_sl = 0.0

def get_market_data():
    try:
        url = "https://api.gold-api.com/price/XAU"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            current_price = float(data.get("price", 0))
            if current_price > 0:
                # Parameter ketat khusus Timeframe 5 Menit (M5) Scalping
                upper_band = round(current_price * 1.0015, 2)
                lower_band = round(current_price * 0.9985, 2)
                
                sl_buy = round(current_price * 0.9980, 2)
                tp_buy = round(current_price * 1.0025, 2)
                
                sl_sell = round(current_price * 1.0020, 2)
                tp_sell = round(current_price * 0.9975, 2)
                
                trend_status = "⏳ *M5 ENGINE:* Memantau momentum mikro & tren 5 menit."
                
                # Logika Trend Following Khusus M5
                if current_price >= upper_band * 0.9995:
                    trend_status = (
                        f"📈 *TF 5M TREND: BULLISH (BUY SETUP)*\n"
                        f"- 📍 **Kondisi M5:** Harga menembus resistensi mikro\n"
                        f"- ⚡ **Action:** Ikut Tren BUY (Scalp M5)\n"
                        f"- 🛑 **SL:** `${sl_buy:,.2f}` | 🎯 **TP:** `${tp_buy:,.2f}`"
                    )
                elif current_price <= lower_band * 1.0005:
                    trend_status = (
                        f"📉 *TF 5M TREND: BEARISH (SELL SETUP)*\n"
                        f"- 📍 **Kondisi M5:** Harga menembus support mikro\n"
                        f"- ⚡ **Action:** Ikut Tren SELL (Scalp M5)\n"
                        f"- 🛑 **SL:** `${sl_sell:,.2f}` | 🎯 **TP:** `${tp_sell:,.2f}`"
                    )
                
                return round(current_price, 2), upper_band, lower_band, trend_status
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
    
    return "⏳ Belum ada koin meme yang memenuhi kriteria saat ini."

def background_price_monitor():
    global USER_CHAT_ID, active_position, entry_price_tracked, target_tp, target_sl
    last_alert_status = None
    
    while True:
        try:
            if USER_CHAT_ID:
                p, upper, lower, signal = get_market_data()
                
                # Pemantauan target TP / SL otomatis (Skala M5)
                if active_position == "BUY":
                    if p >= target_tp:
                        bot.send_message(USER_CHAT_ID, f"🎯 *TAKE PROFIT M5 TERCAPAI! (BUY)*\n- Harga TP: `${target_tp:,.2f}`\n- Harga Spot: `${p:,.2f}`\n✅ *Status: Scalp M5 Sukses!*", parse_mode="Markdown")
                        active_position = None
                    elif p <= target_sl:
                        bot.send_message(USER_CHAT_ID, f"🛑 *STOP LOSS M5 TERSENTUH! (BUY)*\n- Harga SL: `${target_sl:,.2f}`\n- Harga Spot: `${p:,.2f}`\n❌ *Status: Disiplin Cut Loss M5.*", parse_mode="Markdown")
                        active_position = None
                        
                elif active_position == "SELL":
                    if p <= target_tp:
                        bot.send_message(USER_CHAT_ID, f"🎯 *TAKE PROFIT M5 TERCAPAI! (SELL)*\n- Harga TP: `${target_tp:,.2f}`\n- Harga Spot: `${p:,.2f}`\n✅ *Status: Scalp M5 Sukses!*", parse_mode="Markdown")
                        active_position = None
                    elif p >= target_sl:
                        bot.send_message(USER_CHAT_ID, f"🛑 *STOP LOSS M5 TERSENTUH! (SELL)*\n- Harga SL: `${target_sl:,.2f}`\n- Harga Spot: `${p:,.2f}`\n❌ *Status: Disiplin Cut Loss M5.*", parse_mode="Markdown")
                        active_position = None

                # Kirim alert jika ada setup M5 baru
                if "SETUP" in signal and signal != last_alert_status and active_position is None:
                    last_alert_status = signal
                    if "BULLISH" in signal:
                        active_position = "BUY"
                        entry_price_tracked = p
                        target_tp = round(p * 1.0025, 2)
                        target_sl = round(p * 0.9980, 2)
                    elif "BEARISH" in signal:
                        active_position = "SELL"
                        entry_price_tracked = p
                        target_tp = round(p * 0.9975, 2)
                        target_sl = round(p * 1.0020, 2)
                        
                    alert_text = (
                        f"⚡ *M5 SCALPING ALERT!* ⚡\n\n"
                        f"📈 *XAUUSD Live Price:* `${p:,.2f}`\n\n"
                        f"{signal}\n\n"
                        f"🤖 *Bot mengunci target TP & SL M5 otomatis.*"
                    )
                    bot.send_message(USER_CHAT_ID, alert_text, parse_mode="Markdown", disable_web_page_preview=False)
                elif "Menunggu" in signal:
                    last_alert_status = "Menunggu"
        except Exception as e:
            print(f"Error Background Monitor: {e}")
        time.sleep(60)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    global USER_CHAT_ID
    USER_CHAT_ID = message.chat.id
    text = (
        "🤖 *Finbot M5 Scalping Engine Active*\n\n"
        "Perintah yang tersedia:\n"
        "👉 `/scalp` atau `/tf5` - Cek Setup Tren Timeframe 5 Menit\n"
        "👉 `/news` - Panduan Sentimen Makro XAUUSD\n"
        "👉 `/meme` - Saringan koin meme Solana"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['scalp', 'tf5', 'tf15', 'price'])
def send_scalp(message):
    global USER_CHAT_ID
    USER_CHAT_ID = message.chat.id
    p, upper, lower, signal = get_market_data()
    
    sl_buy = round(p * 0.9980, 2)
    tp_buy = round(p * 1.0025, 2)
    sl_sell = round(p * 1.0020, 2)
    tp_sell = round(p * 0.9975, 2)
    
    text = (
        f"📊 *XAUUSD Timeframe 5 Menit (M5) Setup*\n"
        f"- Harga Spot Saat Ini: `${p:,.2f}`\n\n"
        f"📌 *Parameter Scalping M5:*\n"
        f"🟢 **Setup BUY (M5 Bullish):** SL `${sl_buy:,.2f}` | TP `${tp_buy:,.2f}`\n"
        f"🔴 **Setup SELL (M5 Bearish):** SL `${sl_sell:,.2f}` | TP `${tp_sell:,.2f}`\n\n"
        f"{signal}\n\n"
        f"📊 [Buka Chart TradingView XAUUSD (M5)](https://www.tradingview.com/chart/?symbol=OANDA%3AXAUUSD)"
    )
    bot.reply_to(message, text, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(commands=['news', 'usnews'])
def send_us_news(message):
    global USER_CHAT_ID
    USER_CHAT_ID = message.chat.id
    news_text = (
        "🇺🇸 *XAUUSD Live Macro & M5 Scalping Guide*\n\n"
        "🔥 *Faktor Penggerak Utama Pasar Saat Ini:*\n"
        "1. **Suku Bunga & The Fed:** Perhatikan ekspektasi moneter yang menggerakkan volatilitas emas harian.\n"
        "2. **Geopolitik Global:** Pemicu lonjakan harga tiba-tiba pada timeframe pendek.\n\n"
        "⚠️ *Aturan Main M5 Scalper:*\n"
        "- Fokus eksekusi cepat di TF 5 menit sesuai arah tren mikro.\n"
        "- Disiplin ketat batas maksimal risiko 2x loss per minggu."
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
    return "Finbot M5 Scalping Engine is running!", 200

if __name__ == "__main__":
    RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")
    if RENDER_URL:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    
    t = threading.Thread(target=background_price_monitor, daemon=True)
    t.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
