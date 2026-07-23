import time
import requests

TOKEN = "8914087726:AAGeuhs_0btpV97QnmgIDDGhEwHkzGtbvkM"
URL = f"https://api.telegram.org/bot{TOKEN}/"

def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        data["reply_markup"] = reply_markup
    requests.post(URL + "sendMessage", json=data)

def edit_message(chat_id, message_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        data["reply_markup"] = reply_markup
    requests.post(URL + "editMessageText", json=data)

def main():
    print("Bot Telegram murni (Python standard) sedang berjalan...")
    offset = 0
    
    while True:
        try:
            response = requests.get(URL + f"getUpdates?offset={offset}&timeout=30")
            data = response.json()
            
            if data.get("ok"):
                for result in data.get("result", []):
                    offset = result["update_id"] + 1
                    
                    # Handle Pesan Masuk / Perintah /start
                    if "message" in result:
                        message = result["message"]
                        chat_id = message["chat"]["id"]
                        text = message.get("text", "")
                        
                        if text == "/start":
                            keyboard = {
                                "inline_keyboard": [
                                    [
                                        {"text": "🟢 BUY XAUUSD", "callback_data": "action_buy"},
                                        {"text": "🔴 SELL XAUUSD", "callback_data": "action_sell"}
                                    ]
                                ]
                            }
                            send_message(
                                chat_id, 
                                "🚨 **PANEL KENDALI TRADING** 🚨\n\nPilih aksi eksekusi untuk instrumen XAUUSD saat ini:", 
                                reply_markup=keyboard
                            )
                            
                    # Handle Tombol Inline Diklik
                    elif "callback_query" in result:
                        callback = result["callback_query"]
                        chat_id = callback["message"]["chat"]["id"]
                        message_id = callback["message"]["message_id"]
                        data_action = callback["data"]
                        
                        # Jawab callback supaya loading di tombol hilang
                        requests.post(URL + "answerCallbackQuery", json={"callback_query_id": callback["id"]})
                        
                        if data_action == "action_buy":
                            resp_text = "✅ Order BUY XAUUSD Berhasil Diproses!"
                        else:
                            resp_text = "❌ Order SELL XAUUSD Berhasil Diproses!"
                            
                        edit_message(
                            chat_id, 
                            message_id, 
                            f"🚨 **PANEL KENDALI TRADING** 🚨\n\nStatus Terkini:\n{resp_text}"
                        )
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
