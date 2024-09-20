import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from dotenv import load_dotenv
import yt_dlp

load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN')

available_qualities = {}

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome to the URL Uploader Bot! Send me a file URL to upload.")

async def fetch_quality(update: Update, context: CallbackContext):
    url = update.message.text
    chat_id = update.message.chat.id
    
    await update.message.reply_text("Fetching available qualities...")

    global available_qualities
    try:
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            available_qualities[chat_id] = {fmt['format_id']: fmt['height'] for fmt in formats if fmt.get('height')}

            if available_qualities[chat_id]:
                keyboard = [
                    [InlineKeyboardButton(f"{quality}p", callback_data=quality) for quality in available_qualities[chat_id].keys()]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text("Choose a quality:", reply_markup=reply_markup)
            else:
                await update.message.reply_text("No available qualities found.")
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")

async def quality_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    chat_id = query.message.chat.id
    quality = query.data
    url = context.user_data.get('url')

    await query.answer()
    await query.edit_message_text(text=f"Selected quality: {quality}p. Starting download...")

    file_path = download_file(url, quality)

    if file_path and os.path.exists(file_path):
        await context.bot.send_video(chat_id, open(file_path, 'rb'), supports_streaming=True)
        await context.bot.send_message(chat_id, "Upload completed!")
    else:
        await context.bot.send_message(chat_id, "Failed to download the file.")

def download_file(url, quality):
    ydl_opts = {
        'outtmpl': 'downloaded_file.%(ext)s',  # Ensure file is saved with the correct extension
        'format': quality,
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return 'downloaded_file.mp4'  # Change this if your format is different
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fetch_quality))
    application.add_handler(CallbackQueryHandler(quality_selection))

    application.run_polling()

if __name__ == '__main__':
    main()
