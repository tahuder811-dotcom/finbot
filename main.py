from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes

TOKEN = "8914087726:AAGeuhs_0btpV97QnmgIDDGhEwHkzGtbvkM"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🟢 BUY XAUUSD", callback_data="action_buy"),
            InlineKeyboardButton("🔴 SELL XAUUSD", callback_data="action_sell")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🚨 **PANEL KENDALI TRADING** 🚨\n\nPilih aksi eksekusi untuk instrumen XAUUSD saat ini:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    action = query.data
    if action == "action_buy":
        text_resp = "✅ Order BUY XAUUSD Berhasil Diproses!"
    else:
        text_resp = "❌ Order SELL XAUUSD Berhasil Diproses!"
        
    await query.edit_message_text(text=f"🚨 **PANEL KENDALI TRADING** 🚨\n\nStatus Terkini: {text_resp}", parse_mode="Markdown")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("Bot sedang berjalan...")
    app.run_polling()

