import os
import telebot
import yfinance as yf
import requests

TOKEN = os.getenv("8914087726:AAEfKU9rv7ZoRfHlOMhme_xM9l_luOfS33A")
CHAT_ID = os.getenv("7657888575")

bot = telebot.TeleBot(TOKEN)

# Fungsi ambil harga emas real-time
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
        print(f"Error fetching market data: {e}")
    return 0.0, 0.0, 0.0

# Fungsi ambil tren meme coin langsung dari GMGN API
def get_gmgn_memes():
    try:
        # Endpoint publik trending token GMGN
        url = "https://gmgn.ai/defi/quotation/v1/ranking/swaps/1h?device_id=1&client_id=web&app_version=2.0.0"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            res_data = response.json()
            rankings = res_data.get("data", {}).get("rankings", [])
            
            meme_list = []
            for item in rankings[:5]: # Ambil 5 token teratas
                symbol = item.get("symbol", "UNKNOWN")
                name = item.get("name", "Unknown Token")
                price_change = item.get("price_change_percent1h", 0)
                meme_list.append(f"🔥 *{name}* ({symbol}) - 1h Change: ` {price_change}%`")
            
            if meme_list:
                return "\n".join(meme_list)
    except Exception as e:
        print(f"Error fetching GMGN data: {e}")
    
    return "Belum ada sinyal token baru dari GMGN saat ini."

# Handler /start
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    help_text = (
        "🤖 *Finbot Ultimate S&D Engine Active*\n\n"
        "Perintah yang tersedia:\n"
        "👉 `/price` - Cek harga emas terkini\n"
        "👉 `/tf15` - Cek status S&D Timeframe 15M\n"
        "👉 `/meme` - Cek tren meme coin dari GMGN"
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")

# Handler /price dan /tf15
@bot.message_handler(commands=['price', 'tf15'])
def send_price(message):
    price, res, sup = get_market_data()
    response_text = (
        f"📈 *Status S&D Timeframe 15M (XAUUSD)*\n"
        f"- Harga Saat Ini: `${price:,.2f}`\n"
        f"- Resistance 15m: `${res:,.2f}`\n"
        f"- Support 15m: `${sup:,.2f}`\n"
        f"- Status: Bot aktif memantau di background."
    )
    bot.reply_to(message, response_text, parse_mode="Markdown")

# Handler /meme (Mengambil data dari GMGN)
@bot.message_handler(commands=['meme'])
def send_meme(message):
    trending_text = get_gmgn_memes()
    response_text = (
        f"🚀 *Tren Meme Coin Terkini (GMGN)*\n\n"
        f"{trending_text}"
    )
    bot.reply_to(message, response_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "Gunakan /start untuk melihat daftar perintah bot.")

if __name__ == "__main__":
    print("Finbot Ultimate with GMGN is Running 24/7!")
