import os
import telebot
import yfinance as yf
import requests

# Mengambil token dengan aman sebagai teks
TOKEN = str(os.getenv("TELEGRAM_BOT_TOKEN", ""))
bot = telebot.TeleBot(TOKEN)

# Fungsi ambil harga emas asli
def get_market_data():
    try:
        gold = yf.Ticker("GC=F")
        data = gold.history(period="1d", interval="15m")
        if not data.empty:
            current_price = float(data['Close'].iloc[-1])
            resistance = float(data['High'].iloc[-5:].max())
            support = float(data['Low'].iloc[-5:].min())
            return round(current_price, 2), round(resistance, 2), round(support, 2)
    except Exception as e:
        print(f"Error: {e}")
    return 0.0, 0.0, 0.0

# Fungsi ambil tren meme dari GMGN
def get_gmgn_memes():
    try:
        url = "https://gmgn.ai/defi/quotation/v1/ranking/swaps/1h?device_id=1&client_id=web&app_version=2.0.0"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            rankings = response.json().get("data", {}).get("rankings", [])
            meme_list = []
            for item in rankings[:5]:
                symbol = item.get("symbol", "UNKNOWN")
                name = item.get("name", "Token")
                change = item.get("price_change_percent1h", 0)
                meme_list.append(f"🔥 *{name}* ({symbol}) - 1h: `{change}%`")
            if meme_list:
                return "\n".join(meme_list)
    except Exception as e:
        print(f"Error GMGN: {e}")
    return "Belum ada sinyal token baru dari GMGN."

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "🤖 *Finbot S&D Engine Active*\n\n"
        "Perintah:\n"
        "👉 `/price` atau `/tf15` - Cek harga emas\n"
        "👉 `/meme` - Cek tren meme GMGN"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['price', 'tf15'])
def send_price(message):
    p, r, s = get_market_data()
    text = (
        f"📈 *XAUUSD 15M*\n"
        f"- Harga: `${p:,.2f}`\n"
        f"- Resistance: `${r:,.2f}`\n"
        f"- Support: `${s:,.2f}`"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['meme'])
def send_meme(message):
    trending = get_gmgn_memes()
    bot.reply_to(message, f"🚀 *Tren Meme GMGN*\n\n{trending}", parse_mode="Markdown")

if __name__ == "__main__":
    print("Finbot is polling 24/7...")
    bot.remove_webhook()  # Membersihkan webhook lama yang bikin error 409 Conflict
    bot.infinity_polling()
