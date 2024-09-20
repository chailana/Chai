import os
import requests
from tqdm import tqdm
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN')

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome to the URL Uploader Bot! Send me a file URL to upload.")

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

async def upload_file(update: Update, context: CallbackContext):
    url = update.message.text
    chat_id = update.message.chat_id

    await update.message.reply_text("Starting download...")

    try:
        file_path = download_file(url, chat_id)
        with open(file_path, 'rb') as f:
            await update.message.reply_text("Upload started...")
            await context.bot.send_document(chat_id, f)
            await update.message.reply_text("Upload completed!")
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

def main():
    # Create the Application instance
    application = Application.builder().token(TOKEN).build()

    # Add handlers for the /start command and URL messages
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, upload_file))

    # Start the bot with polling
    application.run_polling()

if __name__ == '__main__':
    main()
