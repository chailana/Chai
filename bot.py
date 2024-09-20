import os
import requests
from tqdm import tqdm
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from dotenv import load_dotenv
import yt_dlp

load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN')

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome to the URL Uploader Bot! Send me a file URL to upload.")

def download_file(url):
    ydl_opts = {
        'outtmpl': 'downloaded_file',  # Save the file with this name
        'format': 'best',  # Download the best available quality
        'noplaylist': True,  # Prevent downloading playlists
        'progress_hooks': [progress_hook],  # Set the progress hook
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return 'downloaded_file'
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

def progress_hook(d):
    if d['status'] == 'downloading':
        total_size = d.get('total_bytes', None)
        downloaded_size = d.get('downloaded_bytes', None)
        if total_size and downloaded_size:
            progress = downloaded_size / total_size * 100
            print(f"Download progress: {progress:.2f}%")

async def upload_file(update: Update, context: CallbackContext):
    url = update.message.text
    chat_id = update.message.chat.id

    await update.message.reply_text("Starting download...")

    try:
        file_path = download_file(url)
        if file_path and os.path.exists(file_path):
            await update.message.reply_text("Upload started...")
            with open(file_path, 'rb') as f:
                await context.bot.send_document(chat_id, f)
            await update.message.reply_text("Upload completed!")
        else:
            await update.message.reply_text("Failed to download the file.")
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, upload_file))

    application.run_polling()

if __name__ == '__main__':
    main()
