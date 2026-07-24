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
        # Menggunakan endpoint token boosts / trending terbaru agar data koin meme langsung nampak
        url = "https://api.dexscreener.com/token-boosts/latest/v1"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=6)
        
        if response.status_code == 200:
            boosted_tokens = response.json()
            meme_list = []
            seen = set()
            
            # Ambil token yang berada di jaringan solana
            sol_tokens = [t for t in boosted_tokens if t.get("chainId") == "solana"]
            if not sol_tokens:
                sol_tokens = boosted_tokens # Fallback jika format berbeda
                
            for item in sol_tokens[:10]:
                token_address = item.get("tokenAddress", "")
                if token_address and token_address not in seen:
                    seen.add(token_address)
                    
                    # Request detail pair per token untuk ambil harga & perubahan 1 jam
                    detail_res = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{token_address}", headers=headers, timeout=3)
                    if detail_res.status_code == 200:
                        pair_data = detail_res.json().get("pairs", [])
                        if pair_data:
                            p = pair_data[0]
                            base_token = p.get("baseToken", {})
                            name = base_token.get("name", "Token")
                            symbol = base_token.get("symbol", "UNKNOWN")
                            
                            h1_change = p.get("priceChange", {}).get("h1", 0)
                            if h1_change is None:
                                h1_change = 0
                            h1_change = round(float(h1_change), 2)
                            
                            # Tentukan status sniper
                            if h1_change > 10:
                                status_sniper = "🔥 Strong Pump"
                            elif h1_change > 0:
                                status_sniper = "🎯 Potensi Bagus"
                            else:
                                status_sniper = "👀 Pantau"
                                
                            if h1_change >= 0:
                                meme_list.append(f"🟢 *{name}* (`{symbol}`) - 1h: `+{h1_change}%` [{status_sniper}]")
                            else:
                                meme_list.append(f"🔴 *{name}* (`{symbol}`) - 1h: `{h1_change}%` [{status_sniper}]")
                            
                            if len(meme_list) >= 5:
                                break
            
            if meme_list:
                return "\n".join(meme_list)
    except Exception as e:
        print(f"Error DexScreener Boosts: {e}")
    
    # Fallback pengaman jika data boosts kosong: gunakan endpoint pencarian umum langsung urutkan
    try:
        fallback_url = "https://api.dexscreener.com/latest/dex/search?q=solana"
        headers = {"User-Agent": "Mozilla/5.0"}
        fb_res = requests.get(fallback_url, headers=headers, timeout=5)
        if fb_res.status_code == 200:
            pairs = fb_res.json().get("pairs", [])
            sol_pairs = [p for p in pairs if p.get("chainId") == "solana"]
            sol_pairs = sorted(sol_pairs, key=lambda x: x.get("priceChange", {}).get("h1", 0) or 0, reverse=True)
            
            fallback_list = []
            seen_fb = set()
            for p in sol_pairs:
                bt = p.get("baseToken", {})
                name = bt.get("name", "Token")
                symbol = bt.get("symbol", "UNKNOWN")
                if symbol == "SOL" or symbol in seen_fb:
                    continue
                seen_fb.add(symbol)
                
                h1 = p.get("priceChange", {}).get("h1", 0) or 0
                h1 = round(float(h1), 2)
                
                fallback_list.append(f"🟢 *{name}* (`{symbol}`) - 1h: `+{h1}%` [🎯 Pantau Aktif]")
                if len(fallback_list) >= 5:
                    break
            if fallback_list:
                return "\n".join(fallback_list)
    except Exception:
        pass

    return "⏳ Sedang memuat data koin meme, silakan coba ketik /meme sekali lagi."

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
