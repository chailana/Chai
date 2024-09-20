import os
import requests
from tqdm import tqdm
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN')

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome to the URL Uploader Bot! Send me a file URL to upload.")

def download_file(url, chat_id):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open('downloaded_file', 'wb') as f, tqdm(
        desc='Downloading',
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            f.write(data)
            bar.update(len(data))
    
    return 'downloaded_file'

def upload_file(update: Update, context: CallbackContext):
    url = update.message.text
    chat_id = update.message.chat_id

    update.message.reply_text("Starting download...")

    try:
        file_path = download_file(url, chat_id)
        with open(file_path, 'rb') as f:
            update.message.reply_text("Upload started...")
            context.bot.send_document(chat_id, f)
            update.message.reply_text("Upload completed!")
    except Exception as e:
        update.message.reply_text(f"An error occurred: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, upload_file))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
